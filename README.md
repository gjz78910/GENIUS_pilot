# GENIUS Pilot - Field Engineer Scheduling

Python system that assigns engineers to jobs and finds shortest travel routes.

---

## For Participants

**Open the AI-assisted instructions file in a browser and follow the steps there.**

| Session | File to open |
|---|---|
| AI-assisted coding | `EXPERIMENT_DOCUMENTS/PARTICIPANT_INSTRUCTIONS_AI.html` |

The instructions will guide you through everything: setup, the three tasks, and submitting your work. All steps are interactive — check each one off as you go.

---

## For Experiment Organizers

> **AI-only note:** The KCL-01 pilot used Kiro and previously included a pure human/manual condition. Future GENIUS sessions use only AI-assisted VMs with VS Code and the Claude Code extension, configured for Amazon Bedrock through the VM IAM role so organisers do not need to log in to each VM manually.

### Setup

1. Clone repo and create conda environment: `conda env create -f environment.yml`
2. Activate: `conda activate genius_pilot`
3. Install dependencies: `pip install -r requirements.txt`
4. Run demo to verify: `python -m src.demo`
5. Run tests to confirm baseline: `python -m unittest tests.test_matching tests.test_routing tests.test_benchmarks tests.test_report_correctness tests.test_data_loader -v`
6. Review `EXPERIMENT_DOCUMENTS/organiser/EXPERIMENT_CHECKLIST.html` for the full experiment protocol
7. Collect pre-experiment data (system info, survey) — see `EXPERIMENT_DOCUMENTS/organiser/DATA_COLLECTION.md`

### Key Documents

**Organiser only** (in `EXPERIMENT_DOCUMENTS/organiser/`):
- `EXPERIMENT_CHECKLIST.html` — Session checklist (open in browser)
- `DATA_COLLECTION.md` — Data collection guide
- `AWS_REMOTE_EXPERIMENT_RUNBOOK.md` — AWS VM setup and management

**Participant-facing** (in `EXPERIMENT_DOCUMENTS/`):
- `PARTICIPANT_INSTRUCTIONS_AI.html` — Instructions, AI-assisted group

**Organiser only** — surveys and config (in `EXPERIMENT_DOCUMENTS/organiser/`):
- `Pre_Experiment_Survey.html` — Pre-experiment survey
- `Post_Experiment_Survey.html` — Post-experiment survey
- `session_config.js` — Auto-generated participant session config
- `PLENARY_ETHICS_AMENDMENT_DRAFT.md` — ethics record for deployed AI-attitude survey questions and proposed publication consent; do not collect plenary responses before approval

### Run an Experiment Session

**Step 1 — Prepare participant branches** (run once from `main` before provisioning):

```bash
./SCRIPTS/prepare_vms.sh --count 30 --session S1
```

**Step 2 — Create experiment branch and configure Terraform:**

```bash
git checkout -b <experiment-branch>   # e.g. KCL-S1
# Edit infrastructure/aws-dcv/terraform/terraform.tfvars:
#   - Paste the roster block printed above
#   - Set dcv_allowed_cidrs = ["0.0.0.0/0"]
#   - Set repo_ref to current main HEAD commit hash
#   - Set auto_stop_hours = 12 (do NOT change this after first apply)
#   - Optionally set claude_code_model to an enabled Bedrock model or inference profile
```

**Step 3 — Apply Terraform (provisions all VMs at once):**

```bash
cd infrastructure/aws-dcv/terraform
AWS_PROFILE=genius-dcv terraform apply
```

**Step 4 — For each VM, wait for SSM Online then run post-boot fixes:**

```bash
# Wait for SSM Online:
AWS_PROFILE=genius-dcv aws ssm describe-instance-information \
  --region eu-west-2 --filters "Key=InstanceIds,Values=<instance-id>" \
  --query "InstanceInformationList[0].PingStatus" --output text

# Wait for cloud-init done, then apply fixes (one VM at a time):
AWS_PROFILE=genius-dcv aws ssm send-command \
  --region eu-west-2 --instance-ids <instance-id> \
  --document-name AWS-RunShellScript \
  --parameters 'commands=[
    "update-alternatives --set x-session-manager /usr/bin/xfce4-session",
    "printf \"[Desktop]\\nSession=xfce\\n\" > /home/participant/.dmrc && chown participant:participant /home/participant/.dmrc",
    "sed -i \"/enable-client-resize/s/=.*/=true/\" /etc/dcv/dcv.conf",
    "dcv close-session genius 2>/dev/null || true",
    "systemctl restart dcvserver && sleep 5",
    "dcv create-session --type=virtual --user=participant --owner=participant genius 2>&1 || true",
    "dcv list-sessions"
  ]'
```

**Step 5 — Generate session_config.js on each VM** (get URL and password from terraform output):

```bash
AWS_PROFILE=genius-dcv aws ssm send-command \
  --region eu-west-2 --instance-ids <instance-id> \
  --document-name AWS-RunShellScript \
  --parameters "commands=[\"cd /home/participant/GENIUS_pilot && sudo -u participant /opt/conda/bin/conda run -n genius_pilot python SCRIPTS/generate_session_config.py --desktop-url '<URL>' --password '<PASSWORD>' 2>&1\"]"
```

**Step 6 — For AI VMs, verify Claude Code before handing credentials to participants.**

Claude Code is installed as a VS Code extension and configured for Amazon Bedrock during VM bootstrap. Use SSM to verify it across the fleet:

```bash
AWS_PROFILE=genius-dcv aws ssm send-command \
  --region eu-west-2 \
  --targets "Key=tag:Condition,Values=ai" \
  --document-name AWS-RunShellScript \
  --parameters 'commands=["sudo -u participant -H code --list-extensions | grep -x anthropic.claude-code","sudo -u participant -H bash -lc \"test -f ~/.claude/settings.json && grep -q CLAUDE_CODE_USE_BEDROCK ~/.claude/settings.json\""]'
```

> ⚠️ **Never run `terraform apply` again after VMs are configured.** Any change to `terraform.tfvars` that touches user_data (e.g. `auto_stop_hours`, `repo_ref`, Claude Code model settings) will destroy and recreate all VMs.

For full details and troubleshooting see `EXPERIMENT_DOCUMENTS/organiser/AWS_REMOTE_EXPERIMENT_RUNBOOK.md`.

### Between Participants

1. Submit and store work: `./SCRIPTS/submit_participant_work.sh <ID> <SESSION>`
2. Reset environment: `./SCRIPTS/reset_environment.sh <ID> <SESSION>`
3. Verify reset: `python -m src.demo`

The submission command runs the authoritative checkpoint report, snapshots
experiment-scoped runtime and terminal-audit evidence, stores the participant
branch, creates and verifies a complete Git bundle, pushes the branch, and
records each step in a local manifest. Checkpoint failures do not invalidate
submission; storage, Git-state capture, or push failures do.

On AWS VMs, resource monitoring runs as a restartable system service. Screen
recording runs independently of terminal windows and is protected by a
watchdog. Organisers can record their states with:

```bash
/usr/local/bin/genius-collection-health snapshot
```

### Project Structure

```
├── src/                    # Main source code
│   ├── models/            # Engineer and Job classes
│   ├── optimization/      # Matching and routing algorithms
│   ├── scheduling/        # High-level scheduler
│   └── features/          # Reports and data loading
├── data/                   # Sample data and benchmarks
├── tests/                  # Unit and performance tests
├── EXPERIMENT_DOCUMENTS/   # Experiment protocol and participant instructions
├── SCRIPTS/                # Data collection and environment management scripts
└── reports/                # Generated CSV reports
```
