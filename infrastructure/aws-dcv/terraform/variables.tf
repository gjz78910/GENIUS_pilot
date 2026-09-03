variable "aws_region" {
  type    = string
  default = "eu-west-2"
}

variable "project_name" {
  type    = string
  default = "genius-dcv"
}

variable "ami_id" {
  type        = string
  description = "Golden AMI ID built with Packer."
}

variable "instance_type" {
  type    = string
  default = "m7i.xlarge"
}

variable "volume_size_gb" {
  type    = number
  default = 60
}

variable "participant_roster" {
  type = list(object({
    participant_id = string
    session_id     = string
    condition      = string
  }))

  validation {
    condition     = length(var.participant_roster) > 0 && length(var.participant_roster) <= 30
    error_message = "participant_roster must contain between 1 and 30 entries."
  }

  validation {
    condition     = length(var.participant_roster) == length(distinct([for participant in var.participant_roster : participant.participant_id]))
    error_message = "participant_id values must be unique."
  }

  validation {
    condition     = alltrue([for participant in var.participant_roster : participant.condition == "ai"])
    error_message = "condition must be ai; future GENIUS sessions are AI-assisted only."
  }
}

variable "dcv_allowed_cidrs" {
  type        = list(string)
  description = "Participant and organizer public IP CIDRs allowed to reach Amazon DCV."

  validation {
    condition     = length(var.dcv_allowed_cidrs) > 0
    error_message = "Provide at least one DCV allowlist CIDR."
  }
}

variable "enable_trusted_dcv_cert" {
  type        = bool
  description = "Use dynamic DNS and Let's Encrypt to replace the default self-signed DCV certificate."
  default     = false
}

variable "dynamic_dns_provider" {
  type        = string
  description = "DNS naming mode used by instance user data. Use sslip for Elastic IP based test links or duckdns for DuckDNS hostnames."
  default     = "duckdns"

  validation {
    condition     = contains(["duckdns", "sslip"], var.dynamic_dns_provider)
    error_message = "dynamic_dns_provider must be duckdns or sslip."
  }
}

variable "duckdns_token" {
  type        = string
  description = "DuckDNS token used by each participant instance to update its hostname."
  default     = ""
  sensitive   = true
}

variable "dcv_hostname_domain" {
  type        = string
  description = "Base domain for participant hostnames, for example duckdns.org."
  default     = "duckdns.org"
}

variable "dcv_hostname_prefix" {
  type        = string
  description = "Prefix for generated participant hostnames."
  default     = "genius"
}

variable "dcv_hostname_overrides" {
  type        = map(string)
  description = "Optional participant_id to hostname map for manually assigned participant hostnames."
  default     = {}
}

variable "letsencrypt_email" {
  type        = string
  description = "Email address used for Let's Encrypt registration and expiry notices."
  default     = ""
}

variable "vpc_id" {
  type    = string
  default = ""
}

variable "subnet_id" {
  type    = string
  default = ""
}

variable "repo_url" {
  type    = string
  default = "https://github.com/gjz78910/GENIUS_pilot.git"
}

variable "repo_ref" {
  type    = string
  default = "main"
}

variable "monitor_interval_seconds" {
  type    = number
  default = 60
}

variable "claude_code_bedrock_region" {
  type        = string
  description = "AWS region Claude Code should use for Amazon Bedrock on AI-condition VMs."
  default     = "eu-west-2"
}

variable "claude_code_model" {
  type        = string
  description = "Optional Claude Code model pin for Bedrock, for example an inference profile or model ID enabled in the AWS account."
  default     = ""
}

variable "claude_code_small_fast_model" {
  type        = string
  description = "Optional Claude Code small/fast model pin for Bedrock."
  default     = ""
}

variable "auto_stop_hours" {
  type    = number
  default = 3
}

variable "shutdown_behavior" {
  type    = string
  default = "stop"

  validation {
    condition     = contains(["stop", "terminate"], var.shutdown_behavior)
    error_message = "shutdown_behavior must be stop or terminate."
  }
}

variable "delete_ebs_on_termination" {
  type    = bool
  default = true
}

variable "artifact_retention_days" {
  type    = number
  default = 90
}

variable "budget_email" {
  type    = string
  default = ""
}

variable "monthly_budget_usd" {
  type    = number
  default = 100
}
