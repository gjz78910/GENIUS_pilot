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
- `dcv_allowed_cidrs`: set to `["0.0.0.0/0"]` when participants join from unknown or variable IPs. DCV is still secured by HTTPS cert + per-VM password.
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

## Post-Launch Patches

After `terraform apply`, apply two screen recorder bug-fixes to every VM before participants connect. Run each VM sequentially (not all at once) to avoid overloading the SSM agent queue.

```bash
for INSTANCE_ID in <id-1> <id-2> ...; do
  AWS_PROFILE=genius-dcv aws ssm send-command \
    --region eu-west-2 \
    --instance-ids "$INSTANCE_ID" \
    --document-name AWS-RunShellScript \
    --parameters 'commands=[
      "sed -i \"/-use_shm 0/d\" /usr/local/bin/genius-screen-recorder",
      "sed -i \"s|nohup ffmpeg|XAUTHORITY=\\\"\\$xauthority\\\" DISPLAY=\\\"\\$display_value\\\" nohup ffmpeg|\" /usr/local/bin/genius-screen-recorder",
      "echo patched"
    ]'
  # Wait for this command to finish before sending to the next VM.
done
```

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

Cause: `user_data_replace_on_change = true`. Any change to `terraform.tfvars` that affects user_data (e.g. `auto_stop_hours`, `repo_ref`) forces full instance replacement, wiping all configuration including Kiro logins.

Prevention: set `auto_stop_hours` and `repo_ref` correctly **before** the first `terraform apply` and do not change them again. Recommended values: `auto_stop_hours = 12`, `repo_ref` = pinned main HEAD commit.

### Screen recording stops during experiment

Cause: when a participant closes and reopens the DCV browser tab, the Xdcv process can restart and rotate its X auth cookie. ffmpeg loses display access and dies silently.

Fix (restart from organiser side without affecting participant):

```bash
AWS_PROFILE=genius-dcv aws ssm send-command \
  --region eu-west-2 --instance-ids <instance-id> \
  --document-name AWS-RunShellScript \
  --parameters 'commands=["sudo -u participant /usr/local/bin/genius-screen-recorder start 2>&1"]'
```

Prevention: install the watchdog cron job on each VM after provisioning:

```bash
# Run on each VM via SSM — checks every minute and auto-restarts if crashed
B64=$(python3 -c "import base64; print(base64.b64encode(b'#!/bin/bash\nPID_FILE=/home/participant/genius-runtime/screen_recording.pid\nif [ -s \"\$PID_FILE\" ] && ! kill -0 \"\$(cat \$PID_FILE)\" 2>/dev/null; then\n  sudo -u participant /usr/local/bin/genius-screen-recorder start\nfi\n').decode())")
aws ssm send-command --region eu-west-2 --instance-ids <instance-id> \
  --document-name AWS-RunShellScript \
  --parameters "{\"commands\":[
    \"echo '$B64' | base64 -d > /usr/local/bin/genius-recorder-watchdog && chmod +x /usr/local/bin/genius-recorder-watchdog\",
    \"(crontab -l 2>/dev/null | grep -v recorder-watchdog; echo '* * * * * /usr/local/bin/genius-recorder-watchdog') | crontab -\"
  ]}"
```

Note: the watchdog only restarts if the PID file exists but the process is dead (crashed). If the participant intentionally stops recording, the PID file is removed and the watchdog will not restart it.

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
