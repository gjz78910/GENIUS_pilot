# AWS DCV Workstations

Build one Ubuntu 24.04 golden AMI, then launch one Amazon DCV desktop per participant.

## What You Get

- One EC2 instance per participant.
- Browser access at `https://<public-dns>:8443`.
- Participants use VS Code with the Claude Code extension.
- Resource monitoring starts automatically.
- End-session collection runs through AWS Systems Manager and uploads artifacts to S3.

## Prerequisites

- AWS CLI authenticated to the target account.
- Packer `>= 1.10`.
- Terraform `>= 1.6`.
- Participant and organizer public IP ranges for DCV allowlisting.
- Amazon Bedrock access to the selected Anthropic Claude models.
- EC2/Bedrock quotas sized for the planned parallel session count.
- A public subnet if you set `subnet_id`; direct DCV needs an internet route.

## Authenticate AWS

Prefer AWS SSO when your AWS account supports it:

```bash
aws configure sso
aws sts get-caller-identity --region eu-west-2
```

If your AWS account uses access keys instead, run `aws configure` in your own terminal and enter the keys there. Do not put AWS secrets in this repo or chat.

## Build Golden AMI

```bash
cd infrastructure/aws-dcv/packer
packer init .
packer build \
  -var "aws_region=eu-west-2" \
  -var "repo_ref=$(git -C ../../.. rev-parse HEAD)" \
  .
```

The build starts a temporary AWS builder instance and prints the AMI ID at the end. Use that AMI ID in Terraform.

## Launch Fleet

```bash
cd infrastructure/aws-dcv/terraform
test -f terraform.tfvars || cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars: ami_id, dcv_allowed_cidrs, participant_roster, budget_email
terraform init
terraform plan
terraform apply
terraform output dcv_urls
terraform output participant_password_parameters
```

Retrieve a password for a participant:

```bash
aws ssm get-parameter \
  --name "/genius-dcv/participants/kcl-ai-01/linux-password" \
  --with-decryption \
  --query "Parameter.Value" \
  --output text \
  --region eu-west-2
```

Give each participant their own URL, username `participant`, and password.
Terraform state also contains generated passwords, so store state in a private backend before real sessions.

## End A Session

```bash
aws ssm send-command \
  --document-name genius-dcv-end-session \
  --instance-ids <instance-id> \
  --parameters participantId=kcl-ai-01,sessionId=S1 \
  --region eu-west-2
```

The command stops monitoring, stores participant work, runs checkpoint scripts, collects Claude Code artifacts when present, archives `DATA_COLLECTION/`, and uploads the archive to the Terraform-created S3 bucket.

## Cost Controls

- `auto_stop_hours` schedules an in-instance shutdown.
- `shutdown_behavior = "stop"` keeps disks for inspection.
- `shutdown_behavior = "terminate"` deletes instances after shutdown if root volume deletion is enabled.
- `budget_email` creates an AWS Budget alert.

Keep `dcv_allowed_cidrs` narrow. Do not use `0.0.0.0/0` for real sessions.
