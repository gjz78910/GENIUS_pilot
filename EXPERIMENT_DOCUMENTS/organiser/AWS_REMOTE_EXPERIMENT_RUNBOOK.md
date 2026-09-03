# AWS Remote Experiment Runbook

Use this guide to run the GENIUS experiment on AWS remote desktops.

> **AI-only note:** The KCL-01 pilot used Kiro and previously included a pure human/manual condition. Future GENIUS sessions use only AI-assisted VMs with VS Code and the Claude Code extension, configured for Amazon Bedrock through the VM IAM role so organisers do not need to log in to each VM manually.

## Fixed Setup

- AWS profile: `genius-dcv`
- AWS region: `eu-west-2`
- Terraform folder: `infrastructure/aws-dcv/terraform`
- Artifact bucket: `s3://genius-dcv-artifacts-684638912478-82c72ce8/`
- Desktop username: `participant`
- Desktop URL format: `https://<participant-hostname>:8443/#genius`
- Golden AMI: `ami-0cc9d8a4392798d01`

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
- `condition`: use `ai` for every participant.
- `claude_code_bedrock_region`: Bedrock region used by Claude Code on AI VMs.
- `claude_code_model`: optional model or inference profile pin for Claude Code.
- `repo_ref`: commit or branch that VMs must clone.
- `dcv_allowed_cidrs`: set to `["0.0.0.0/0"]` when participants join from unknown or variable IPs. DCV is still secured by HTTPS cert + per-VM password.
- `auto_stop_hours`: experiment time plus buffer.
- `enable_trusted_dcv_cert = true`
- `dynamic_dns_provider = "sslip"`

Current Terraform validation allows up to 30 roster entries. For a 30-participant day, request or confirm EC2 and Bedrock throughput quotas before launch, then run a one-VM dry run and a small fleet dry run.

Example roster:

```hcl
participant_roster = [
  {
    participant_id = "ai-01"
    session_id     = "S1"
    condition      = "ai"
  },
  {
    participant_id = "ai-02"
    session_id     = "S1"
    condition      = "ai"
  }
]
```

Participants do not need individual Claude browser logins when the AWS account has Bedrock access and the VM instance role has Bedrock invoke permissions. The bootstrap writes `~/.claude/settings.json` for the participant user and sets `claudeCode.disableLoginPrompt` in VS Code user settings.

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

## Post-Launch Patches

New VMs provisioned from the current `user_data.sh.tftpl` already include the screen recorder fixes below (DCV display detection, `DISPLAY`/`XAUTHORITY` for ffmpeg, minimum 1280×720 gate, 15-second systemd watchdog, segment merge on stop).

For VMs created **before** this update, either replace the instance with `terraform apply` or copy `/usr/local/bin/genius-screen-recorder`, `/usr/local/bin/genius-recorder-watchdog`, and the `genius-recorder-watchdog.*` systemd units from a freshly provisioned VM.

**Important:** Send SSM commands to one VM at a time when running git operations or heavy commands. Sending to all VMs simultaneously can saturate the SSM agent queue and leave all agents unresponsive.

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

If `dcv list-sessions` returns `There are no sessions available`, create the session manually:

```bash
AWS_PROFILE=genius-dcv aws ssm send-command \
  --region eu-west-2 \
  --instance-ids <instance-id> \
  --document-name AWS-RunShellScript \
  --parameters 'commands=["dcv create-session --type=virtual --user=participant --owner=participant genius","dcv list-sessions"]'
```

This is commonly needed after a VM stop/start — see [DCV session missing after stop/start](#dcv-session-missing-after-stopstart).

## Start Recording

Screen recording is started by the participant from their own terminal as part of the setup steps in the participant instructions. Resource monitoring starts automatically.

As organiser, verify the recorder, watchdog, and resource monitor after the
participant confirms recording has started:

```bash
AWS_PROFILE=genius-dcv aws ssm send-command \
  --region eu-west-2 \
  --instance-ids <instance-id> \
  --document-name AWS-RunShellScript \
  --parameters 'commands=["sudo -u participant -H bash -lc \"/usr/local/bin/genius-screen-recorder status\"","/usr/local/bin/genius-collection-health snapshot","ls -lh /home/participant/Videos"]'
```

Expected:

```text
running
file=/home/participant/Videos/GENIUS_<participant-id>_<session-id>_YYYYMMDDTHHMMSSZ.mp4
display=:1 size=1920x1080
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
5. Use VS Code with Claude Code only.
6. Complete the assigned task.
7. Complete the post-experiment survey.
8. Stop screen recording.
9. Run the unified submission command and review the authoritative checkpoint
    report. Claude Code statements that a task is complete are not completion evidence.

For participants:

- Claude Code should already be available in the VS Code sidebar.
- Claude Code is configured for Amazon Bedrock through the VM IAM role.
- If the Claude panel shows an Anthropic login prompt, run `/usr/local/bin/genius-configure-claude-code` through SSM or in a participant terminal, then reload VS Code.

**Clipboard in DCV browser:** Participants should use **Ctrl+Shift+V** in the VS Code terminal, or right-click → Paste. If the DCV clipboard relay is needed, they must use the DCV toolbar clipboard icon on the left edge of the browser window first, paste text there, and then paste into the VM.

## Fast Claude Code Fleet Setup

Use the AMI and bootstrap path, not per-VM desktop login.

1. Build a fresh AMI from `infrastructure/aws-dcv/packer`. The build installs VS Code, the Claude Code extension, and a reusable `/usr/local/bin/genius-configure-claude-code` helper.
2. Ensure the AWS account has access to the target Anthropic Claude model in Amazon Bedrock.
3. Launch AI VMs with an instance role that includes `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`, `bedrock:ListInferenceProfiles`, and `bedrock:GetInferenceProfile`.
4. Optionally pin `claude_code_model` and `claude_code_small_fast_model` in `terraform.tfvars`.
5. After launch, verify or repair all AI VMs with one SSM command:

```bash
AWS_PROFILE=genius-dcv aws ssm send-command \
  --region eu-west-2 \
  --targets "Key=tag:Condition,Values=ai" \
  --document-name AWS-RunShellScript \
  --parameters 'commands=[
    "CLAUDE_CODE_BEDROCK_REGION=eu-west-2 /usr/local/bin/genius-configure-claude-code",
    "sudo -u participant -H code --list-extensions | grep -x anthropic.claude-code",
    "sudo -u participant -H bash -lc \"grep -q CLAUDE_CODE_USE_BEDROCK ~/.claude/settings.json\""
  ]'
```

Run a single interactive dry run before the real session: open one AI VM, confirm VS Code opens the project, open the Claude Code sidebar, send a harmless prompt such as `Explain the repository structure without editing files`, and confirm the response uses Bedrock without a browser login.

## End Session And Upload Data

Always run this before stopping or destroying VMs.

The end-session flow captures a final health snapshot, invokes the unified
submission path, copies experiment-scoped terminal audit and runtime evidence,
creates and verifies a portable full-history Git bundle, stops the background
resource service, and uploads a recoverable archive. A checkpoint failure is a
study result; a storage/Git-bundle/upload failure is an operational incident
that must be resolved before destroying the VM.

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
- Claude Code metrics for AI participants
- Claude Code local transcript and VS Code extension artifacts under `DATA_COLLECTION/claude_code_history/`
- screen recordings under `DATA_COLLECTION/screen_recordings/`
- one uploaded `.tar.gz` archive in S3

Claude Code local files copied from the VM:

```text
/home/participant/.claude/projects
/home/participant/.claude/todos
/home/participant/.config/Code/logs
```

Do not archive `~/.claude/settings.json` or VS Code global storage, because
those locations can contain authentication or provider configuration state.

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
DATA_COLLECTION/claude_code_metrics_*.json
DATA_COLLECTION/claude_code_history/manifest.txt
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

### DCV session missing after stop/start

Cause: the DCV session startup script runs once at first boot via cloud-init. If a VM is stopped and restarted, cloud-init does not re-run, so the `genius` session is not recreated automatically.

Symptom: DCV URL shows "No session is available or you are not authorised to join the session."

Fix:

```bash
AWS_PROFILE=genius-dcv aws ssm send-command \
  --region eu-west-2 \
  --instance-ids <instance-id> \
  --document-name AWS-RunShellScript \
  --parameters 'commands=[
    "dcv create-session --type=virtual --user=participant --owner=participant genius 2>&1 || true",
    "dcv list-sessions"
  ]'
```

Do this for every VM that was stopped and restarted before handing credentials to participants.

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

Cause: recording was started before the participant connected via DCV, or ffmpeg restarted while the display was still at the default low resolution (800×600).

Fix: ask the participant to stop and restart recording once they have connected and can see the full desktop:

```bash
/usr/local/bin/genius-screen-recorder stop
/usr/local/bin/genius-screen-recorder start
```

The recorder now refuses to start below 1280×720 and the watchdog waits for full resolution before auto-resuming.

Verify the display size via SSM:

```bash
DISPLAY=:1 XAUTHORITY=/run/user/1001/dcv/genius.xauth xdpyinfo | awk '/dimensions:/ {print $2}'
/usr/local/bin/genius-screen-recorder status
```

### Screen recorder fails to start (ffmpeg errors)

**`Authorization required` / `Cannot open display`**: DCV is not connected yet, or Xdcv restarted. Connect via DCV, wait for the full desktop, then run `/usr/local/bin/genius-screen-recorder start`. Current VMs pass `DISPLAY` and `XAUTHORITY` to ffmpeg automatically.

### Recording stops early

Cause: `ffmpeg x11grab` can fail if mouse pointer capture is enabled.

Fix: current recorder does not use `-draw_mouse`. Restart recording from the participant terminal:

```bash
/usr/local/bin/genius-screen-recorder start
```

### Claude Code panel asks for login on an AI VM

Cause: the VS Code extension did not read the Bedrock settings or the disable-login setting before opening.

Fix:

```bash
AWS_PROFILE=genius-dcv aws ssm send-command \
  --region eu-west-2 --instance-ids <instance-id> \
  --document-name AWS-RunShellScript \
  --parameters 'commands=["CLAUDE_CODE_BEDROCK_REGION=eu-west-2 /usr/local/bin/genius-configure-claude-code"]'
```

Then ask the participant to run **Developer: Reload Window** in VS Code.

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

### "Oh no! Something has gone wrong" on DCV login

Cause: `x-session-manager` alternative points to `gnome-session`, which is not installed on this AMI. The AMI uses XFCE, but the alternative is not set correctly by default.

Fix (run for each affected VM):

```bash
AWS_PROFILE=genius-dcv aws ssm send-command \
  --region eu-west-2 --instance-ids <instance-id> \
  --document-name AWS-RunShellScript \
  --parameters 'commands=[
    "update-alternatives --set x-session-manager /usr/bin/xfce4-session",
    "printf \"[Desktop]\\nSession=xfce\\n\" > /home/participant/.dmrc && chown participant:participant /home/participant/.dmrc",
    "dcv close-session genius 2>/dev/null || true",
    "systemctl restart dcvserver && sleep 5",
    "dcv create-session --type=virtual --user=participant --owner=participant genius 2>&1 || true"
  ]'
```

Prevention: always run this after provisioning each VM — see the post-boot fix step in the README.

### Terraform destroys and recreates all VMs unexpectedly

Cause: `user_data_replace_on_change = true`. Any change to `terraform.tfvars` that affects user_data (e.g. `auto_stop_hours`, `repo_ref`, Claude Code model settings) forces full instance replacement.

Prevention: set `auto_stop_hours` and `repo_ref` correctly **before** the first `terraform apply` and do not change them again. Recommended values: `auto_stop_hours = 12`, `repo_ref` = pinned main HEAD commit.

### Screen recording stops during experiment

Cause: when a participant closes and reopens the DCV browser tab, the Xdcv process can restart and rotate its X auth cookie. ffmpeg loses display access and dies silently.

Fix (restart from organiser side without affecting participant):

```bash
AWS_PROFILE=genius-dcv aws ssm send-command \
  --region eu-west-2 --instance-ids <instance-id> \
  --document-name AWS-RunShellScript \
  --parameters 'commands=["sudo -u participant /usr/local/bin/genius-screen-recorder resume 2>&1"]'
```

Prevention: `genius-screen-recorder start` enables a systemd watchdog timer that checks every 15 seconds. It only auto-resumes when recording was intentionally started (watchdog flag file present) and waits until the DCV display is at least 1280×720 before restarting ffmpeg. This avoids the cropped 800×600 resume segments seen in earlier sessions.

Check watchdog and segment status:

```bash
systemctl status genius-recorder-watchdog.timer
/usr/local/bin/genius-screen-recorder status
cat /home/participant/genius-runtime/screen_recording_segments.json
```

On session end, `genius-screen-recorder stop` merges multiple segments into `GENIUS_<participant>_<session>_merged.mp4`.

### OOM crash on simultaneous VM boot

Cause: booting many VMs at the same time causes cloud-init, conda, git, certbot, and dcvserver to compete for RAM (8 GB per VM). dcvserver gets OOM-killed and the VM becomes unresponsive.

Fix: force-stop the affected VM, start it again, wait for SSM Online, then run the post-boot fixes.

Prevention: `terraform apply` provisioning all VMs simultaneously is acceptable. Avoid triggering additional heavy SSM commands (git, conda) across all VMs at the same time.

### SSM agent goes unresponsive

Cause: sending git or other heavy SSM commands to all VMs simultaneously saturates the SSM agent queue.

Prevention: always send SSM commands to one VM at a time. Wait for `Success` before sending to the next.

### session_config.js shows wrong participantId after git pull

Cause: the file is committed with placeholder values. Any `git pull` or `git checkout` resets it.

Fix: re-run `generate_session_config.py` on the affected VM after any git operation:

```bash
AWS_PROFILE=genius-dcv aws ssm send-command \
  --region eu-west-2 --instance-ids <instance-id> \
  --document-name AWS-RunShellScript \
  --parameters "commands=[\"cd /home/participant/GENIUS_pilot && sudo -u participant /opt/conda/bin/conda run -n genius_pilot python SCRIPTS/generate_session_config.py --desktop-url '<URL>' --password '<PASSWORD>' 2>&1\"]"
```
