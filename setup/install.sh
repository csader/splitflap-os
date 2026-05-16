#!/bin/bash
# install.sh — Set up Splitflap OS on a Raspberry Pi (Bookworm / Trixie)
# Run as root from the repo directory: sudo bash setup/install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$REPO_DIR/venv"

echo "=== Splitflap OS Installer ==="
echo "  Installing from: $REPO_DIR"
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run as root (sudo bash setup/install.sh)"
    exit 1
fi

# Install system packages
echo "[1/4] Installing system packages..."
apt-get update -qq
apt-get install -y python3-pip python3-venv network-manager libopenblas0

# Ensure NetworkManager manages WiFi
echo "[2/4] Configuring NetworkManager..."
if ! systemctl is-active --quiet NetworkManager; then
    systemctl enable NetworkManager
    systemctl start NetworkManager
fi

# Create venv and install Python dependencies
# Using a venv avoids PEP 668 conflicts on Bookworm/Trixie and keeps
# dependencies isolated from the system Python.
# --prefer-binary uses pre-built wheels — much faster on Pi Zero W (ARMv6).
echo "[3/4] Installing Python dependencies..."
if [ ! -d "$VENV_DIR" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi
echo "  Installing packages (this may take a while on Pi Zero W)..."
"$VENV_DIR/bin/pip" install --prefer-binary -r "$REPO_DIR/server/requirements.txt"

# Make scripts executable
chmod +x "$REPO_DIR/setup/network-check.sh"

# Install systemd services (preserve existing Environment= variables)
echo "[4/4] Setting up systemd services..."

install_service() {
    local src="$1"
    local dest="$2"
    local tmp=$(mktemp)
    sed "s|/opt/splitflap-os|$REPO_DIR|g" "$src" > "$tmp"
    # Preserve existing Environment= lines if service already installed
    if [ -f "$dest" ]; then
        while IFS= read -r line; do
            if [[ "$line" == Environment=* ]]; then
                key="${line%%=*}=${line#*=}"
                key="${line%%=*}"
                # Replace matching Environment= line with existing value
                sed -i "s|^${key}=.*|${line}|" "$tmp"
            fi
        done < "$dest"
    fi
    mv "$tmp" "$dest"
}

install_service "$REPO_DIR/setup/splitflap-network.service" /etc/systemd/system/splitflap-network.service
install_service "$REPO_DIR/setup/splitflap.service" /etc/systemd/system/splitflap.service
systemctl daemon-reload
systemctl enable splitflap-network.service
systemctl enable splitflap.service
systemctl restart splitflap-network.service
systemctl restart splitflap.service

# Create settings.json if it doesn't exist
if [ ! -f "$REPO_DIR/server/settings.json" ]; then
    echo "{}" > "$REPO_DIR/server/settings.json"
fi

echo ""
echo "=== Splitflap OS installed and running ==="
echo ""
echo "  Access UI:     http://$(hostname -I | awk '{print $1}')"
echo "  View logs:     journalctl -u splitflap -f"
echo "  Network logs:  journalctl -u splitflap-network -f"
echo ""
echo "  To update:     cd $REPO_DIR && git pull && sudo bash setup/install.sh"
echo ""
echo "  WiFi hotspot fallback is enabled."
echo "  If no WiFi is found on boot, the Pi will create:"
echo "    SSID: SplitflapOS"
echo "    Password: splitflap"
echo ""
echo "  To change hotspot credentials, edit:"
echo "    /etc/systemd/system/splitflap-network.service"
echo ""
