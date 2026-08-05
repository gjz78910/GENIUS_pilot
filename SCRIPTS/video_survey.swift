#!/usr/bin/swift
// Local, dependency-free video survey for GENIUS screen recordings.
// Usage: swift video_survey.swift INPUT.mp4 OUTPUT_DIR INTERVAL_SECONDS
//        [START_SECONDS END_SECONDS [MAX_WIDTH]]

import Foundation
import AVFoundation
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

struct Sample: Encodable {
    let video_sec: Double
    let frame_file: String
    let change_score: Double
}

struct Survey: Encodable {
    let duration_sec: Double
    let interval_sec: Double
    let start_sec: Double
    let end_sec: Double
    let samples: [Sample]
}

func thumbnail(_ image: CGImage, maxWidth: Int = 480) -> CGImage? {
    let width = min(maxWidth, image.width)
    let height = max(1, Int(Double(image.height) * Double(width) / Double(image.width)))
    let colorSpace = CGColorSpaceCreateDeviceRGB()
    guard let context = CGContext(
        data: nil, width: width, height: height,
        bitsPerComponent: 8, bytesPerRow: width * 4,
        space: colorSpace,
        bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
    ) else { return nil }
    context.interpolationQuality = .medium
    context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
    return context.makeImage()
}

func signature(_ image: CGImage) -> [UInt8] {
    guard let data = image.dataProvider?.data,
          let bytes = CFDataGetBytePtr(data) else { return [] }
    let stepX = max(1, image.width / 80)
    let stepY = max(1, image.height / 45)
    let bytesPerPixel = max(1, image.bitsPerPixel / 8)
    var values: [UInt8] = []
    for y in stride(from: 0, to: image.height, by: stepY) {
        for x in stride(from: 0, to: image.width, by: stepX) {
            let offset = y * image.bytesPerRow + x * bytesPerPixel
            let channels = min(3, bytesPerPixel)
            var sum = 0
            for channel in 0..<channels { sum += Int(bytes[offset + channel]) }
            values.append(UInt8(sum / max(1, channels)))
        }
    }
    return values
}

func score(_ previous: [UInt8]?, _ current: [UInt8]) -> Double {
    guard let previous, previous.count == current.count, !current.isEmpty else { return 0 }
    let total = zip(previous, current).reduce(0) { $0 + abs(Int($1.0) - Int($1.1)) }
    return Double(total) / Double(current.count * 255)
}

func saveJPEG(_ image: CGImage, to url: URL) -> Bool {
    guard let destination = CGImageDestinationCreateWithURL(
        url as CFURL, UTType.jpeg.identifier as CFString, 1, nil
    ) else { return false }
    CGImageDestinationAddImage(destination, image, [
        kCGImageDestinationLossyCompressionQuality: 0.72
    ] as CFDictionary)
    return CGImageDestinationFinalize(destination)
}

let args = CommandLine.arguments
guard (args.count == 4 || args.count == 6 || args.count == 7),
      let interval = Double(args[3]), interval > 0 else {
    fputs("Usage: video_survey.swift INPUT.mp4 OUTPUT_DIR INTERVAL_SECONDS [START_SECONDS END_SECONDS [MAX_WIDTH]]\n", stderr)
    exit(2)
}

let input = URL(fileURLWithPath: args[1])
let output = URL(fileURLWithPath: args[2], isDirectory: true)
try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)

let asset = AVURLAsset(url: input)
let duration = CMTimeGetSeconds(asset.duration)
guard duration.isFinite, duration > 0 else {
    fputs("Could not read a usable duration from \(input.path)\n", stderr)
    exit(1)
}

let hasWindow = args.count >= 6
let requestedStart = hasWindow ? Double(args[4]) : 0.0
let requestedEnd = hasWindow ? Double(args[5]) : duration
let maxWidth = args.count == 7 ? (Int(args[6]) ?? 480) : 480
guard maxWidth > 0 else {
    fputs("MAX_WIDTH must be positive.\n", stderr)
    exit(2)
}
guard let requestedStart, let requestedEnd,
      requestedStart >= 0, requestedEnd > requestedStart, requestedEnd <= duration + 0.01 else {
    fputs("Invalid survey window. It must be within the video duration.\n", stderr)
    exit(2)
}

let generator = AVAssetImageGenerator(asset: asset)
generator.appliesPreferredTrackTransform = true
generator.requestedTimeToleranceBefore = CMTime(seconds: 0.25, preferredTimescale: 600)
generator.requestedTimeToleranceAfter = CMTime(seconds: 0.25, preferredTimescale: 600)

var samples: [Sample] = []
var previous: [UInt8]? = nil
var second = requestedStart
while second <= requestedEnd + 0.01 {
    do {
        let image = try generator.copyCGImage(at: CMTime(seconds: second, preferredTimescale: 600), actualTime: nil)
        guard let small = thumbnail(image, maxWidth: maxWidth) else { continue }
        let file = String(format: "frame_%07.2f.jpg", second)
        if saveJPEG(small, to: output.appendingPathComponent(file)) {
            let current = signature(small)
            samples.append(Sample(video_sec: second, frame_file: file, change_score: score(previous, current)))
            previous = current
        }
    } catch {
        fputs("Warning: could not extract frame at \(second)s: \(error)\n", stderr)
    }
    second += interval
}

let result = Survey(duration_sec: duration, interval_sec: interval,
                    start_sec: requestedStart, end_sec: requestedEnd, samples: samples)
let encoder = JSONEncoder()
encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
print(String(data: try encoder.encode(result), encoding: .utf8)!)
