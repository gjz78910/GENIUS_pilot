packer {
  required_version = ">= 1.10.0"

  required_plugins {
    amazon = {
      source  = "github.com/hashicorp/amazon"
      version = ">= 1.3.0"
    }
  }
}

variable "aws_region" {
  type    = string
  default = "eu-west-2"
}

variable "ami_name_prefix" {
  type    = string
  default = "genius-dcv-ubuntu2404"
}

variable "instance_type" {
  type    = string
  default = "m7i.large"
}

variable "volume_size_gb" {
  type    = number
  default = 60
}

variable "repo_url" {
  type    = string
  default = "https://github.com/gjz78910/GENIUS_pilot.git"
}

variable "repo_ref" {
  type    = string
  default = "main"
}

locals {
  timestamp = regex_replace(timestamp(), "[- TZ:]", "")
}

source "amazon-ebs" "ubuntu" {
  region        = var.aws_region
  instance_type = var.instance_type
  ssh_username  = "ubuntu"
  ami_name      = "${var.ami_name_prefix}-${local.timestamp}"

  source_ami_filter {
    filters = {
      name                = "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    owners      = ["099720109477"]
    most_recent = true
  }

  launch_block_device_mappings {
    device_name           = "/dev/sda1"
    volume_type           = "gp3"
    volume_size           = var.volume_size_gb
    delete_on_termination = true
    encrypted             = true
  }

  tags = {
    Project = "GENIUS"
    Role    = "golden-ami"
  }
}

build {
  sources = ["source.amazon-ebs.ubuntu"]

  provisioner "shell" {
    execute_command = "chmod +x {{ .Path }}; sudo -E env {{ .Vars }} {{ .Path }}"

    environment_vars = [
      "GENIUS_REPO_URL=${var.repo_url}",
      "GENIUS_REPO_REF=${var.repo_ref}",
    ]
    script = "scripts/install-golden-ami.sh"
  }
}
