# AWS Remote Experiment Runbook

Use this guide to run the GENIUS experiment on AWS remote desktops.

## Fixed Setup

- AWS profile: `genius-dcv`
- AWS region: `eu-west-2`
- Terraform folder: `infrastructure/aws-dcv/terraform`
- Artifact bucket: `s3://genius-dcv-artifacts-684638912478-82c72ce8/`
- Desktop username: `participant`
- Desktop URL format: `https://<participant-hostname>:8443/#genius`
- Golden AMI: `ami-0e056aaceae76cdab`

Each participant gets one AWS Ubuntu desktop through Amazon DCV.

```text
participant laptop -> browser -> Amazon DCV -> AWS Ubuntu desktop
```

## Before Launch

Create or switch to the experiment branch first.

```bash
git checkout -b <experiment-branch>
git push -u origin HEAD
```

Edit:

```text
infrastructure/aws-dcv/terraform/terraform.tfvars
```

Check these values:

- `participant_roster`: one row per participant.
- `condition`: `manual` uses VS Code, `ai` uses Kiro.
- `repo_ref`: commit or branch that VMs must clone.
- `dcv_allowed_cidrs`: organizer and participant public IPs only.
- `auto_stop_hours`: experiment time plus buffer.
- `enable_trusted_dcv_cert = true`
- `dynamic_dns_provider = "sslip"`

Current Terraform validation allows up to 10 roster entries. For a 20-participant day, launch two batches or intentionally raise that limit after checking AWS capacity and budget.

Example roster:

```hcl
participant_roster = [
  {
    participant_id = "manual-01"
    session_id     = "S1"
    condition      = "manual"
  },
  {
    participant_id = "ai-01"
    session_id     = "S1"
    condition      = "ai"
  }
]
```

AI participants need assigned Kiro accounts. Kiro login can be prepared before the session, but Kiro chat history is local to each VM and is not synced by account.

## Launch VMs

```bash
cd infrastructure/aws-dcv/terraform

AWS_PROFILE=genius-dcv terraform init
AWS_PROFILE=genius-dcv terraform validate
AWS_PROFILE=genius-dcv terraform plan
AWS_PROFILE=genius-dcv terraform apply
```

Get links, instance IDs, and password parameter names:

```bash
AWS_PROFILE=genius-dcv terraform output dcv_urls
AWS_PROFILE=genius-dcv terraform output instance_ids
AWS_PROFILE=genius-dcv terraform output participant_password_parameters
```

Get one participant password:

```bash
AWS_PROFILE=genius-dcv aws ssm get-parameter \
  --region eu-west-2 \
  --name "/genius-dcv/participants/<participant-id>/linux-password" \
  --with-decryption \
  --query "Parameter.Value" \
  --output text
```

Send each participant only their own link, username, and password.

```text
Remote desktop link: https://<their-hostname>:8443/#genius
Username: participant
Password: <their-password>
```

## Readiness Check

Do not open the DCV link too early. Wait for SSM and cloud-init first.

Poll until SSM shows `Online` (usually within 60–90 seconds of the instance reaching `running` state):

```bash
AWS_PROFILE=genius-dcv aws ssm describe-instance-information \
  --region eu-west-2 \
  --filters Key=InstanceIds,Values=<instance-id> \
  --query "InstanceInformationList[0].PingStatus" --output text
```

Then verify cloud-init completed and DCV is ready:

```bash
AWS_PROFILE=genius-dcv aws ssm send-command \
  --region eu-west-2 \
  --instance-ids <instance-id> \
  --document-name AWS-RunShellScript \
  --parameters 'commands=["cloud-init status","systemctl is-active dcvserver","dcv list-sessions"]'
```

The DCV session should show:

```text
Session: 'genius'
```

## Start Recording

Screen recording is started by the participant from their own terminal as part of the setup steps in the participant instructions. Resource monitoring starts automatically.

As organiser, verify the recording is running after the participant confirms they have started it:

```bash
AWS_PROFILE=genius-dcv aws ssm send-command \
  --region eu-west-2 \
  --instance-ids <instance-id> \
  --document-name AWS-RunShellScript \
  --parameters 'commands=["sudo -u participant -H bash -lc \"/usr/local/bin/genius-screen-recorder status\"","ls -lh /home/participant/Videos"]'
```

Expected:

```text
running
/home/participant/Videos/GENIUS_<participant-id>_<session-id>.mp4
```

Also verify the recording resolution matches the participant's browser window (not 800×600):

```bash
AWS_PROFILE=genius-dcv aws ssm send-command \
  --region eu-west-2 \
  --instance-ids <instance-id> \
  --document-name AWS-RunShellScript \
  --parameters 'commands=["DISPLAY=:1 XAUTHORITY=/run/user/1001/dcv/genius.xauth xdpyinfo | awk \"/dimensions:/ {print \\$2}\""]'
```

If the recording has not been started or shows `800x600`, ask the participant to run `/usr/local/bin/genius-screen-recorder start` in their terminal before proceeding.

## Run The Session

Participant steps:

1. Open their DCV link.
2. Confirm there is a valid HTTPS lock.
3. Log in as `participant`.
4. Follow the setup steps in the participant instructions (activate conda, confirm branch, **start screen recording**).
5. Manual group: use VS Code only.
6. AI group: use Kiro only.
7. Complete the assigned task.
8. Complete the post-experiment survey.
9. Stop screen recording.

For AI participants:

- Kiro account login can persist after closing and reopening the DCV browser tab.
- The same Kiro account can connect on more than one VM, but do not use a shared account in the formal experiment.
- Kiro chat history is stored on the VM, not synced across machines.

**Clipboard in DCV browser:** Participants cannot paste directly into the Kiro terminal with Ctrl+V. Tell them to use **Ctrl+Shift+V** in the Kiro terminal, or right-click → Paste. If the DCV clipboard relay is needed (e.g. pasting from local machine), they must use the DCV toolbar clipboard icon on the left edge of the browser window first, paste text there, and then paste into the VM.

## End Session And Upload Data

Always run this before stopping or destroying VMs.

```bash
AWS_PROFILE=genius-dcv terraform output end_session_commands
```

Run the printed command for each participant, or run:

```bash
AWS_PROFILE=genius-dcv aws ssm send-command \
  --region eu-west-2 \
  --document-name genius-dcv-end-session \
  --instance-ids <instance-id> \
  --parameters participantId=<participant-id>,sessionId=<session-id>
```

This collects:

- participant code and git activity
- resource, energy, and carbon data
- test and code quality metrics
- Kiro metrics for AI participants
- Kiro local chat/history/log files under `DATA_COLLECTION/kiro_history/`
- screen recordings under `DATA_COLLECTION/screen_recordings/`
- one uploaded `.tar.gz` archive in S3

Kiro local files copied from the VM:

```text
/home/participant/.config/Kiro/User/globalStorage/kiro.kiroagent
/home/participant/.config/Kiro/logs
/home/participant/.local/share/kiro-cli
```

## Download Data Locally

```bash
mkdir -p DATA_COLLECTION/aws_artifacts

AWS_PROFILE=genius-dcv aws s3 sync \
  s3://genius-dcv-artifacts-684638912478-82c72ce8/ \
  DATA_COLLECTION/aws_artifacts/
```

Check each participant archive contains:

```text
DATA_COLLECTION/aggregated_*.json
DATA_COLLECTION/resource_usage_*.jsonl
DATA_COLLECTION/kiro_metrics_*.json
DATA_COLLECTION/kiro_history/manifest.txt
DATA_COLLECTION/screen_recordings/*.mp4
```

## Stop Or Destroy VMs

To stop compute charges but keep disks:

```bash
AWS_PROFILE=genius-dcv aws ec2 stop-instances \
  --region eu-west-2 \
  --instance-ids <instance-id-1> <instance-id-2>
```

Confirm:

```bash
AWS_PROFILE=genius-dcv aws ec2 describe-instances \
  --region eu-west-2 \
  --filters Name=tag:Stack,Values=genius-dcv \
  --query "Reservations[].Instances[].{InstanceId:InstanceId,State:State.Name,Participant:Tags[?Key=='ParticipantID']|[0].Value}" \
  --output table
```

To fully remove participant VMs, disks, Elastic IPs, and passwords after data is safe:

```bash
cd infrastructure/aws-dcv/terraform

AWS_PROFILE=genius-dcv terraform apply -destroy \
  -target=aws_eip_association.participant \
  -target=aws_eip.participant \
  -target=aws_instance.participant \
  -target=aws_ssm_parameter.participant_password \
  -target=random_password.participant
```

## Common Failures

### DCV login form does nothing

Cause: the page is stale, often because DCV restarted or the auth WebSocket timed out.

Fix:

```bash
AWS_PROFILE=genius-dcv aws ssm send-command \
  --region eu-west-2 \
  --instance-ids <instance-id> \
  --document-name AWS-RunShellScript \
  --parameters 'commands=["systemctl is-active dcvserver","dcv list-sessions","journalctl -u dcvserver --since \"15 minutes ago\" --no-pager | tail -n 120"]'
```

If the service is stable, close the browser tab and reopen the DCV link. Do not keep clicking a stale login form.

### DCV restarts during login

Cause: unattended upgrades can restart services after boot.

Fix: current VM bootstrap disables `apt-daily`, `apt-daily-upgrade`, and `unattended-upgrades`. If this happens on a live VM, stop them:

```bash
systemctl disable --now apt-daily.timer apt-daily-upgrade.timer unattended-upgrades.service
systemctl stop apt-daily.service apt-daily-upgrade.service unattended-upgrades.service
```

### Recording is too small or cropped

Cause: recording was started before the participant connected via DCV, so the display was still at its default low resolution (800×600).

Fix: ask the participant to stop and restart recording once they have connected and can see the full desktop:

```bash
/usr/local/bin/genius-screen-recorder stop
/usr/local/bin/genius-screen-recorder start
```

Verify the display size via SSM:

```bash
DISPLAY=:1 XAUTHORITY=/run/user/1001/dcv/genius.xauth xdpyinfo | awk '/dimensions:/ {print $2}'
```

### Screen recorder fails to start (ffmpeg errors)

**`Unrecognized option 'use_shm'`**: The installed ffmpeg version does not support this flag. Remove it from the recorder script:

```bash
sudo sed -i '/-use_shm 0/d' /usr/local/bin/genius-screen-recorder
```

**`Authorization required` / `Cannot open display`**: The recorder is not passing `XAUTHORITY` to ffmpeg. Patch the script:

```bash
sudo sed -i 's|nohup ffmpeg|XAUTHORITY="$xauthority" DISPLAY="$display_value" nohup ffmpeg|' /usr/local/bin/genius-screen-recorder
```

Both fixes should be applied to the golden AMI so they do not recur.

### Recording stops early

Cause: `ffmpeg x11grab` can fail if mouse pointer capture is enabled.

Fix: current recorder does not use `-draw_mouse`. Restart recording from the participant terminal:

```bash
/usr/local/bin/genius-screen-recorder start
```

### Kiro chat history is missing after login on another VM

Cause: Kiro chat history is local to the VM. It is not synced by the Kiro account.

Fix: always run the end-session command before cleanup. It copies Kiro local history and logs into `DATA_COLLECTION/kiro_history/`.

### Terraform or AWS says no credentials

Fix:

```bash
AWS_PROFILE=genius-dcv aws sts get-caller-identity
```

If this fails, authenticate the `genius-dcv` profile before running Terraform or AWS commands.

### Cost risk

Always stop VMs when testing is done:

```bash
AWS_PROFILE=genius-dcv aws ec2 stop-instances --region eu-west-2 --instance-ids <ids>
```

Then confirm all participant instances show `stopped`.
