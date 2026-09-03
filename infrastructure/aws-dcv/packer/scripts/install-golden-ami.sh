#!/usr/bin/env bash
set -euo pipefail
trap 'status=$?; echo "AMI install failed at line $LINENO: $BASH_COMMAND" >&2; exit "$status"' ERR

export DEBIAN_FRONTEND=noninteractive

GENIUS_REPO_URL="${GENIUS_REPO_URL:-https://github.com/gjz78910/GENIUS_pilot.git}"
GENIUS_REPO_REF="${GENIUS_REPO_REF:-main}"
DCV_PACKAGE_URL="https://d1uj6qtbmh3dt5.cloudfront.net/nice-dcv-ubuntu2404-x86_64.tgz"
MINIFORGE_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"

apt-get update -qq
apt-get install -y \
  build-essential \
  ca-certificates \
  curl \
  dbus-x11 \
  git \
  gnupg \
  jq \
  kazam \
  libasound2t64 \
  libgbm1 \
  libgtk-3-0 \
  libnss3 \
  libsecret-tools \
  libxkbfile1 \
  libxshmfence1 \
  libxss1 \
  nodejs \
  npm \
  pulseaudio-utils \
  rsync \
  software-properties-common \
  unzip \
  wget \
  ffmpeg \
  wmctrl \
  x11-utils \
  x11-xserver-utils \
  xfce4 \
  xfce4-terminal \
  xterm

install -d -m 0755 /etc/apt/keyrings
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor >/etc/apt/keyrings/packages.microsoft.gpg
cat >/etc/apt/sources.list.d/vscode.list <<'EOF'
deb [arch=amd64 signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main
EOF

curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor >/etc/apt/keyrings/google-chrome.gpg
chmod 0644 /etc/apt/keyrings/google-chrome.gpg
cat >/etc/apt/sources.list.d/google-chrome.list <<'EOF'
deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] https://dl.google.com/linux/chrome/deb/ stable main
EOF

apt-get update -qq
apt-get install -y code google-chrome-stable
update-alternatives --install /usr/bin/x-www-browser x-www-browser /usr/bin/google-chrome-stable 300
update-alternatives --install /usr/bin/gnome-www-browser gnome-www-browser /usr/bin/google-chrome-stable 300
update-alternatives --set x-www-browser /usr/bin/google-chrome-stable
update-alternatives --set gnome-www-browser /usr/bin/google-chrome-stable

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

curl -fsSL https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o "$tmp_dir/awscliv2.zip"
unzip -q "$tmp_dir/awscliv2.zip" -d "$tmp_dir"
"$tmp_dir/aws/install" --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli

wget -qO "$tmp_dir/NICE-GPG-KEY" https://d1uj6qtbmh3dt5.cloudfront.net/NICE-GPG-KEY
gpg --import "$tmp_dir/NICE-GPG-KEY"
wget -qO "$tmp_dir/dcv.tgz" "$DCV_PACKAGE_URL"
tar -xzf "$tmp_dir/dcv.tgz" -C "$tmp_dir"
dcv_dir="$(find "$tmp_dir" -maxdepth 1 -type d -name 'nice-dcv-*' | head -n 1)"
apt-get install -y \
  "$dcv_dir"/nice-dcv-server_*_amd64.ubuntu2404.deb \
  "$dcv_dir"/nice-dcv-web-viewer_*_amd64.ubuntu2404.deb \
  "$dcv_dir"/nice-xdcv_*_amd64.ubuntu2404.deb

cat >/etc/dcv/dcv.conf <<'EOF'
[security]
authentication="system"

[connectivity]
web-port=8443
quic-port=8443
enable-quic-frontend=true

[session-management/defaults]
disconnection-idle-timeout=0
EOF
systemctl enable dcvserver

curl -fsSL "$MINIFORGE_URL" -o "$tmp_dir/miniforge.sh"
bash "$tmp_dir/miniforge.sh" -b -p /opt/conda
ln -sf /opt/conda/bin/conda /usr/local/bin/conda
cat >/etc/profile.d/conda.sh <<'EOF'
. /opt/conda/etc/profile.d/conda.sh
EOF

install -d -m 0755 /opt/genius
git clone "$GENIUS_REPO_URL" /opt/genius/base
cd /opt/genius/base
git fetch --all --tags
git checkout "$GENIUS_REPO_REF"
git rev-parse HEAD >/opt/genius/base_commit

if /opt/conda/bin/conda env list | awk '{print $1}' | grep -qx genius_pilot; then
  /opt/conda/bin/conda env update -n genius_pilot -f environment.yml
else
  /opt/conda/bin/conda env create -f environment.yml
fi
/opt/conda/bin/conda run -n genius_pilot pip install -r requirements.txt
/opt/conda/bin/conda run -n genius_pilot python -m src.demo >/opt/genius/demo_check.log

if ! id participant >/dev/null 2>&1; then
  useradd -m -s /bin/bash participant
fi
usermod -aG audio,video participant
install -d -m 0755 /usr/local/share/genius
cat >/usr/local/bin/genius-configure-claude-code <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

participant_home="/home/participant"
project_dir="${PROJECT_DIR:-$participant_home/GENIUS_pilot}"
bedrock_region="${CLAUDE_CODE_BEDROCK_REGION:-${AWS_REGION:-eu-west-2}}"
model="${CLAUDE_CODE_MODEL:-}"
small_model="${CLAUDE_CODE_SMALL_FAST_MODEL:-}"

install -d -o participant -g participant \
  "$participant_home/.config/Code/User" \
  "$participant_home/.config/Code/CachedExtensionVSIXs" \
  "$participant_home/.config/Code/logs" \
  "$participant_home/.claude"
chown -R participant:participant "$participant_home/.config" "$participant_home/.claude"

sudo -u participant -H code --install-extension anthropic.claude-code --force >/tmp/genius-claude-code-extension.log 2>&1 || {
  cat /tmp/genius-claude-code-extension.log >&2 || true
  exit 1
}

sudo -u participant -H bash -lc '
  set -euo pipefail
  if ! command -v claude >/dev/null 2>&1; then
    curl -fsSL https://claude.ai/install.sh | bash
  fi
' || true

python3 - "$participant_home/.claude/settings.json" "$bedrock_region" "$model" "$small_model" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
region, model, small_model = sys.argv[2:5]
settings = {}
if path.exists():
    try:
        settings = json.loads(path.read_text())
    except json.JSONDecodeError:
        settings = {}
settings["$schema"] = "https://json.schemastore.org/claude-code-settings.json"
env = dict(settings.get("env", {}))
env["CLAUDE_CODE_USE_BEDROCK"] = "1"
env["AWS_REGION"] = region
env["AWS_DEFAULT_REGION"] = region
if model:
    env["ANTHROPIC_MODEL"] = model
if small_model:
    env["ANTHROPIC_SMALL_FAST_MODEL"] = small_model
settings["env"] = env
path.write_text(json.dumps(settings, indent=2) + "\n")
PY

python3 - "$participant_home/.config/Code/User/settings.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
settings = {}
if path.exists():
    try:
        settings = json.loads(path.read_text())
    except json.JSONDecodeError:
        settings = {}
settings["claudeCode.disableLoginPrompt"] = True
settings["claudeCode.preferredLocation"] = "sidebar"
settings["security.workspace.trust.enabled"] = False
path.write_text(json.dumps(settings, indent=2) + "\n")
PY

chown -R participant:participant "$participant_home/.config/Code" "$participant_home/.claude"
EOF
chmod 0755 /usr/local/bin/genius-configure-claude-code
CLAUDE_CODE_BEDROCK_REGION="${CLAUDE_CODE_BEDROCK_REGION:-eu-west-2}" genius-configure-claude-code || true
cat >>/home/participant/.bashrc <<'EOF'
. /opt/conda/etc/profile.d/conda.sh
conda activate genius_pilot
export PATH="$HOME/.local/bin:$HOME/.claude/local:$PATH"
cd ~/GENIUS_pilot 2>/dev/null || true
EOF
install -d -m 0755 /home/participant/.config /home/participant/.config/xfce4/xfconf/xfce-perchannel-xml
cat >/home/participant/.config/mimeapps.list <<'EOF'
[Default Applications]
x-scheme-handler/http=google-chrome.desktop
x-scheme-handler/https=google-chrome.desktop
text/html=google-chrome.desktop
application/xhtml+xml=google-chrome.desktop
EOF
cat >/home/participant/.config/xfce4/xfconf/xfce-perchannel-xml/exo.xml <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<channel name="exo" version="1.0">
  <property name="preferred-applications" type="empty">
    <property name="WebBrowser" type="empty">
      <property name="custom" type="bool" value="true"/>
      <property name="command" type="string" value="google-chrome-stable"/>
    </property>
  </property>
</channel>
EOF
chown participant:participant /home/participant/.bashrc
chown -R participant:participant /home/participant/.config

install -d -m 0755 /etc/genius
cat >/usr/local/bin/genius-dcv-init <<'EOF'
#!/usr/bin/env bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec dbus-launch --exit-with-session startxfce4
EOF
chmod 0755 /usr/local/bin/genius-dcv-init

cat >/usr/local/bin/open-genius-ide <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-$HOME/GENIUS_pilot}"
CONDITION="manual"
if [ -f /etc/genius/condition ]; then
  CONDITION="$(cat /etc/genius/condition)"
fi

if [ "$CONDITION" = "ai" ]; then
  code --new-window "$PROJECT_DIR" &
else
  code --new-window "$PROJECT_DIR" &
fi

for _ in $(seq 1 40); do
  if command -v wmctrl >/dev/null 2>&1 && wmctrl -r "GENIUS_pilot" -b add,maximized_vert,maximized_horz 2>/dev/null; then
    exit 0
  fi
  sleep 0.5
done
wait
EOF
chmod 0755 /usr/local/bin/open-genius-ide

apt-get clean
rm -rf /var/lib/apt/lists/*
