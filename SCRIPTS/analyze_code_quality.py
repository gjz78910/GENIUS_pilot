#!/usr/bin/env python3
"""Analyze code quality metrics.

This script analyzes code quality using pylint, radon, and pydocstyle to
measure code quality score, cyclomatic complexity, and documentation coverage.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_pylint(source_path):
    """Run pylint and parse output.
    
    Args:
        source_path: Path to source code directory or file
    
    Returns:
        Dictionary with pylint metrics
    """
    try:
        result = subprocess.run(
            ["pylint", "--output-format=json", str(source_path)],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Parse JSON output
        try:
            issues = json.loads(result.stdout)
        except json.JSONDecodeError:
            issues = []
        
        # Calculate score (pylint outputs score in stderr)
        score = None
        for line in result.stderr.split("\n"):
            if "rated at" in line.lower():
                try:
                    # Extract score from line like "Your code has been rated at 8.50/10"
                    parts = line.split("rated at")
                    if len(parts) > 1:
                        score_str = parts[1].split("/")[0].strip()
                        score = float(score_str)
                except (ValueError, IndexError):
                    pass
        
        # Count issues by type
        issue_counts = {
            "error": 0,
            "warning": 0,
            "refactor": 0,
            "convention": 0,
            "info": 0,
        }
        
        for issue in issues:
            issue_type = issue.get("type", "").lower()
            if issue_type in issue_counts:
                issue_counts[issue_type] += 1
        
        return {
            "available": True,
            "score": score,
            "score_max": 10.0,
            "total_issues": len(issues),
            "issue_counts": issue_counts,
            "issues": issues[:100],  # Limit to first 100 issues
        }
    except FileNotFoundError:
        return {
            "available": False,
            "error": "pylint not installed",
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
        }


def run_radon(source_path):
    """Run radon for cyclomatic complexity analysis.
    
    Args:
        source_path: Path to source code directory or file
    
    Returns:
        Dictionary with radon metrics
    """
    try:
        # Run radon cc (cyclomatic complexity)
        result_cc = subprocess.run(
            ["radon", "cc", "-j", str(source_path)],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Run radon mi (maintainability index)
        result_mi = subprocess.run(
            ["radon", "mi", "-j", str(source_path)],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Parse complexity results
        complexity_data = {}
        try:
            complexity_data = json.loads(result_cc.stdout)
        except json.JSONDecodeError:
            pass
        
        # Parse maintainability results
        maintainability_data = {}
        try:
            maintainability_data = json.loads(result_mi.stdout)
        except json.JSONDecodeError:
            pass
        
        # Calculate average complexity
        total_complexity = 0
        function_count = 0
        max_complexity = 0
        
        def extract_complexity(obj):
            nonlocal total_complexity, function_count, max_complexity
            if isinstance(obj, dict):
                if "complexity" in obj:
                    complexity = obj["complexity"]
                    total_complexity += complexity
                    function_count += 1
                    max_complexity = max(max_complexity, complexity)
                for value in obj.values():
                    extract_complexity(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_complexity(item)
        
        extract_complexity(complexity_data)
        
        avg_complexity = total_complexity / function_count if function_count > 0 else 0
        
        # Calculate average maintainability index
        total_mi = 0
        module_count = 0
        
        def extract_mi(obj):
            nonlocal total_mi, module_count
            if isinstance(obj, dict):
                if "rank" in obj and "mi" in obj:
                    total_mi += obj["mi"]
                    module_count += 1
                for value in obj.values():
                    extract_mi(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_mi(item)
        
        extract_mi(maintainability_data)
        
        avg_mi = total_mi / module_count if module_count > 0 else 0
        
        return {
            "available": True,
            "cyclomatic_complexity": {
                "average": round(avg_complexity, 2),
                "max": max_complexity,
                "function_count": function_count,
            },
            "maintainability_index": {
                "average": round(avg_mi, 2),
                "module_count": module_count,
            },
            "raw_data": {
                "complexity": complexity_data,
                "maintainability": maintainability_data,
            },
        }
    except FileNotFoundError:
        return {
            "available": False,
            "error": "radon not installed",
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
        }


def run_pydocstyle(source_path):
    """Run pydocstyle for documentation analysis.
    
    Args:
        source_path: Path to source code directory or file
    
    Returns:
        Dictionary with pydocstyle metrics
    """
    try:
        result = subprocess.run(
            ["pydocstyle", "--format=json", str(source_path)],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Parse JSON output
        try:
            issues = json.loads(result.stdout)
        except json.JSONDecodeError:
            issues = []
        
        # Count issues by type
        issue_counts = {}
        for issue in issues:
            code = issue.get("code", "unknown")
            issue_counts[code] = issue_counts.get(code, 0) + 1
        
        # Count files and functions/classes
        files_with_issues = set()
        for issue in issues:
            files_with_issues.add(issue.get("filename", ""))
        
        return {
            "available": True,
            "total_issues": len(issues),
            "files_with_issues": len(files_with_issues),
            "issue_counts": issue_counts,
            "issues": issues[:100],  # Limit to first 100 issues
        }
    except FileNotFoundError:
        return {
            "available": False,
            "error": "pydocstyle not installed",
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
        }


def count_code_statistics(source_path):
    """Count basic code statistics.
    
    Args:
        source_path: Path to source code directory
    
    Returns:
        Dictionary with code statistics
    """
    source_path = Path(source_path)
    stats = {
        "total_files": 0,
        "total_lines": 0,
        "total_functions": 0,
        "total_classes": 0,
        "files": [],
    }
    
    if source_path.is_file():
        files = [source_path]
    else:
        files = list(source_path.rglob("*.py"))
    
    for file_path in files:
        if "__pycache__" in str(file_path) or ".pyc" in str(file_path):
            continue
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                line_count = len(lines)
                
                # Count functions and classes (simple regex)
                import re
                function_count = len(re.findall(r"^\s*def\s+\w+", "".join(lines), re.MULTILINE))
                class_count = len(re.findall(r"^\s*class\s+\w+", "".join(lines), re.MULTILINE))
                
                stats["total_files"] += 1
                stats["total_lines"] += line_count
                stats["total_functions"] += function_count
                stats["total_classes"] += class_count
                
                stats["files"].append({
                    "path": str(file_path.relative_to(source_path.parent)),
                    "lines": line_count,
                    "functions": function_count,
                    "classes": class_count,
                })
        except Exception:
            pass
    
    return stats


def analyze_code_quality(source_path="src", output_file=None):
    """Analyze code quality using all available tools.
    
    Args:
        source_path: Path to source code directory
        output_file: Output JSON file path
    
    Returns:
        Dictionary with all code quality metrics
    """
    source_path = Path(source_path)
    
    if not source_path.exists():
        print(f"Error: Source path {source_path} does not exist", file=sys.stderr)
        return None
    
    print(f"Analyzing code quality for: {source_path}")
    
    metrics = {
        "analysis_timestamp": datetime.now().isoformat(),
        "source_path": str(source_path.absolute()),
        "code_statistics": count_code_statistics(source_path),
        "pylint": run_pylint(source_path),
        "radon": run_radon(source_path),
        "pydocstyle": run_pydocstyle(source_path),
    }
    
    # Calculate overall quality score (weighted average)
    scores = []
    weights = []
    
    if metrics["pylint"]["available"] and metrics["pylint"]["score"] is not None:
        scores.append(metrics["pylint"]["score"] / 10.0)  # Normalize to 0-1
        weights.append(0.4)  # 40% weight
    
    if metrics["radon"]["available"]:
        # Convert maintainability index to score (0-100 scale, higher is better)
        mi = metrics["radon"]["maintainability_index"]["average"]
        mi_score = max(0, min(1, mi / 100.0))  # Normalize to 0-1
        scores.append(mi_score)
        weights.append(0.3)  # 30% weight
        
        # Penalize high complexity
        complexity = metrics["radon"]["cyclomatic_complexity"]["average"]
        complexity_score = max(0, 1 - (complexity - 5) / 20.0)  # Penalize if > 5
        scores.append(complexity_score)
        weights.append(0.2)  # 20% weight
    
    if metrics["pydocstyle"]["available"]:
        # Penalize missing documentation
        doc_issues = metrics["pydocstyle"]["total_issues"]
        total_files = metrics["code_statistics"]["total_files"]
        doc_score = max(0, 1 - (doc_issues / max(total_files * 2, 1)))  # Allow 2 issues per file
        scores.append(doc_score)
        weights.append(0.1)  # 10% weight
    
    if scores and weights:
        total_weight = sum(weights)
        if total_weight > 0:
            overall_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
            metrics["overall_quality_score"] = round(overall_score, 3)
            metrics["overall_quality_percent"] = round(overall_score * 100, 1)
    
    # Save to file if specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(metrics, f, indent=2)
        
        print(f"\nCode quality metrics saved to: {output_path}")
    
    return metrics


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze code quality metrics"
    )
    parser.add_argument(
        "-s", "--source",
        type=str,
        default="src",
        help="Path to source code directory (default: src)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="DATA_COLLECTION/code_quality.json",
        help="Output JSON file path"
    )
    parser.add_argument(
        "--participant-id",
        type=str,
        help="Participant ID to include in filename"
    )
    
    args = parser.parse_args()
    
    # Determine output path
    output_path = args.output
    if args.participant_id:
        output_path = f"DATA_COLLECTION/code_quality_{args.participant_id}.json"
    
    # Analyze code quality
    metrics = analyze_code_quality(
        source_path=args.source,
        output_file=output_path
    )
    
    if not metrics:
        return 1
    
    # Print summary
    print(f"\n=== Code Quality Summary ===")
    print(f"Total files: {metrics['code_statistics']['total_files']}")
    print(f"Total lines: {metrics['code_statistics']['total_lines']}")
    print(f"Total functions: {metrics['code_statistics']['total_functions']}")
    print(f"Total classes: {metrics['code_statistics']['total_classes']}")
    
    if metrics["pylint"]["available"]:
        score = metrics["pylint"]["score"]
        if score is not None:
            print(f"\nPylint score: {score:.2f}/10.0")
        print(f"Pylint issues: {metrics['pylint']['total_issues']}")
    else:
        print(f"\nPylint: Not available ({metrics['pylint'].get('error', 'unknown error')})")
    
    if metrics["radon"]["available"]:
        print(f"\nCyclomatic complexity:")
        print(f"  Average: {metrics['radon']['cyclomatic_complexity']['average']}")
        print(f"  Max: {metrics['radon']['cyclomatic_complexity']['max']}")
        print(f"Maintainability index:")
        print(f"  Average: {metrics['radon']['maintainability_index']['average']}")
    else:
        print(f"\nRadon: Not available ({metrics['radon'].get('error', 'unknown error')})")
    
    if metrics["pydocstyle"]["available"]:
        print(f"\nPydocstyle issues: {metrics['pydocstyle']['total_issues']}")
        print(f"Files with issues: {metrics['pydocstyle']['files_with_issues']}")
    else:
        print(f"\nPydocstyle: Not available ({metrics['pydocstyle'].get('error', 'unknown error')})")
    
    if "overall_quality_percent" in metrics:
        print(f"\nOverall quality score: {metrics['overall_quality_percent']}%")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
