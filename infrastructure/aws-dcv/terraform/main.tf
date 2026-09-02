data "aws_caller_identity" "current" {}

data "aws_vpc" "default" {
  count   = var.vpc_id == "" ? 1 : 0
  default = true
}

locals {
  selected_vpc_id = var.vpc_id != "" ? var.vpc_id : data.aws_vpc.default[0].id
  participants    = { for participant in var.participant_roster : participant.participant_id => participant }
  common_tags = {
    Project = "GENIUS"
    Stack   = var.project_name
  }
}

data "aws_subnets" "selected" {
  filter {
    name   = "vpc-id"
    values = [local.selected_vpc_id]
  }
}

locals {
  selected_subnet_id = var.subnet_id != "" ? var.subnet_id : data.aws_subnets.selected.ids[0]
  auto_stop_minutes  = floor(var.auto_stop_hours * 60)
  participant_hostnames = {
    for participant_id, participant in local.participants :
    participant_id => var.dynamic_dns_provider == "sslip" ? "${var.dcv_hostname_prefix}-${replace(aws_eip.participant[participant_id].public_ip, ".", "-")}.sslip.io" : lookup(
      var.dcv_hostname_overrides,
      participant_id,
      "${var.dcv_hostname_prefix}-${replace(lower(participant.participant_id), "_", "-")}.${var.dcv_hostname_domain}"
    )
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "artifacts" {
  bucket        = "${var.project_name}-artifacts-${data.aws_caller_identity.current.account_id}-${random_id.bucket_suffix.hex}"
  force_destroy = false
  tags          = local.common_tags
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    id     = "expire-artifacts"
    status = "Enabled"

    filter {
      prefix = ""
    }

    expiration {
      days = var.artifact_retention_days
    }
  }
}

resource "aws_security_group" "dcv" {
  name        = "${var.project_name}-dcv"
  description = "Amazon DCV access for GENIUS experiment workstations"
  vpc_id      = local.selected_vpc_id
  tags        = merge(local.common_tags, { Name = "${var.project_name}-dcv" })
}

resource "aws_vpc_security_group_ingress_rule" "dcv_tcp" {
  for_each          = toset(var.dcv_allowed_cidrs)
  security_group_id = aws_security_group.dcv.id
  cidr_ipv4         = each.value
  from_port         = 8443
  ip_protocol       = "tcp"
  to_port           = 8443
}

resource "aws_vpc_security_group_ingress_rule" "dcv_udp" {
  for_each          = toset(var.dcv_allowed_cidrs)
  security_group_id = aws_security_group.dcv.id
  cidr_ipv4         = each.value
  from_port         = 8443
  ip_protocol       = "udp"
  to_port           = 8443
}

resource "aws_vpc_security_group_ingress_rule" "acme_http" {
  for_each          = var.enable_trusted_dcv_cert ? toset(["0.0.0.0/0"]) : toset([])
  security_group_id = aws_security_group.dcv.id
  cidr_ipv4         = each.value
  from_port         = 80
  ip_protocol       = "tcp"
  to_port           = 80
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.dcv.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_eip" "participant" {
  for_each = var.enable_trusted_dcv_cert && var.dynamic_dns_provider == "sslip" ? local.participants : {}

  domain = "vpc"
  tags   = merge(local.common_tags, { Name = "${var.project_name}-${each.value.participant_id}" })
}

resource "aws_iam_role" "workstation" {
  name = "${var.project_name}-workstation"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.workstation.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_policy" "workstation" {
  name = "${var.project_name}-workstation"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::dcv-license.${var.aws_region}",
          "arn:aws:s3:::dcv-license.${var.aws_region}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.artifacts.arn,
          "${aws_s3_bucket.artifacts.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:ListInferenceProfiles",
          "bedrock:GetInferenceProfile"
        ]
        Resource = [
          "arn:aws:bedrock:*:*:inference-profile/*",
          "arn:aws:bedrock:*:*:application-inference-profile/*",
          "arn:aws:bedrock:*:*:foundation-model/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "workstation" {
  role       = aws_iam_role.workstation.name
  policy_arn = aws_iam_policy.workstation.arn
}

resource "aws_iam_instance_profile" "workstation" {
  name = "${var.project_name}-workstation"
  role = aws_iam_role.workstation.name
}

resource "random_password" "participant" {
  for_each = local.participants

  length           = 20
  special          = true
  override_special = "!#%+=?"

  keepers = {
    participant_id = each.value.participant_id
    session_id     = each.value.session_id
  }
}

resource "aws_ssm_parameter" "participant_password" {
  for_each = local.participants

  name  = "/${var.project_name}/participants/${each.value.participant_id}/linux-password"
  type  = "SecureString"
  value = random_password.participant[each.key].result
  tags  = local.common_tags
}

resource "aws_instance" "participant" {
  for_each = local.participants

  ami                                  = var.ami_id
  instance_type                        = var.instance_type
  subnet_id                            = local.selected_subnet_id
  vpc_security_group_ids               = [aws_security_group.dcv.id]
  iam_instance_profile                 = aws_iam_instance_profile.workstation.name
  associate_public_ip_address          = true
  instance_initiated_shutdown_behavior = var.shutdown_behavior
  user_data_replace_on_change          = true

  root_block_device {
    volume_size           = var.volume_size_gb
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = var.delete_ebs_on_termination
  }

  user_data_base64 = base64gzip(templatefile("${path.module}/templates/user_data.sh.tftpl", {
    participant_id               = each.value.participant_id
    session_id                   = each.value.session_id
    condition                    = each.value.condition
    participant_password         = random_password.participant[each.key].result
    artifact_bucket              = aws_s3_bucket.artifacts.bucket
    repo_url                     = var.repo_url
    repo_ref                     = var.repo_ref
    monitor_interval_seconds     = var.monitor_interval_seconds
    claude_code_bedrock_region   = var.claude_code_bedrock_region
    claude_code_model            = var.claude_code_model
    claude_code_small_fast_model = var.claude_code_small_fast_model
    auto_stop_minutes            = local.auto_stop_minutes
    trusted_dcv_cert_enabled     = var.enable_trusted_dcv_cert
    dynamic_dns_provider         = var.dynamic_dns_provider
    duckdns_token                = var.duckdns_token
    dcv_hostname                 = local.participant_hostnames[each.key]
    duckdns_domain               = trimsuffix(local.participant_hostnames[each.key], ".${var.dcv_hostname_domain}")
    expected_public_ip           = var.dynamic_dns_provider == "sslip" ? aws_eip.participant[each.key].public_ip : ""
    letsencrypt_email            = var.letsencrypt_email
  }))

  tags = merge(local.common_tags, {
    Name          = "${var.project_name}-${each.value.participant_id}"
    ParticipantID = each.value.participant_id
    SessionID     = each.value.session_id
    Condition     = each.value.condition
  })

  lifecycle {
    precondition {
      condition     = !var.enable_trusted_dcv_cert || var.letsencrypt_email != ""
      error_message = "letsencrypt_email is required when enable_trusted_dcv_cert is true."
    }

    precondition {
      condition     = !var.enable_trusted_dcv_cert || var.dynamic_dns_provider != "duckdns" || var.duckdns_token != ""
      error_message = "duckdns_token is required when enable_trusted_dcv_cert is true."
    }

    precondition {
      condition     = !var.enable_trusted_dcv_cert || var.dynamic_dns_provider != "duckdns" || var.dcv_hostname_domain != ""
      error_message = "dcv_hostname_domain is required when enable_trusted_dcv_cert is true."
    }
  }
}

resource "aws_eip_association" "participant" {
  for_each = aws_eip.participant

  allocation_id = each.value.id
  instance_id   = aws_instance.participant[each.key].id
}

resource "aws_ssm_document" "end_session" {
  name            = "${var.project_name}-end-session"
  document_type   = "Command"
  document_format = "JSON"

  content = jsonencode({
    schemaVersion = "2.2"
    description   = "Stop GENIUS monitoring, collect results, and upload artifacts."
    parameters = {
      participantId = {
        type        = "String"
        description = "Participant ID, e.g. kcl-manual-01 or kcl-ai-01"
      }
      sessionId = {
        type        = "String"
        description = "Session ID, e.g. S1"
      }
    }
    mainSteps = [
      {
        action = "aws:runShellScript"
        name   = "endSession"
        inputs = {
          timeoutSeconds = "7200"
          runCommand = split("\n", templatefile("${path.module}/templates/end_session.sh.tftpl", {
            artifact_bucket = aws_s3_bucket.artifacts.bucket
          }))
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_budgets_budget" "monthly" {
  count = var.budget_email == "" ? 0 : 1

  name         = "${var.project_name}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.budget_email]
  }
}
