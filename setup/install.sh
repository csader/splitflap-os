#!/bin/bash
# install.sh — Set up Splitflap OS on a Raspberry Pi (Bookworm)
# Run as root from the repo directory: sudo bash setup/install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

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
apt-get install -y -qq python3-pip python3-venv network-manager libopenblas0 > /dev/null

# Ensure NetworkManager manages WiFi
echo "[2/4] Configuring NetworkManager..."
if ! systemctl is-active --quiet NetworkManager; then
    systemctl enable NetworkManager
    systemctl start NetworkManager
fi

# Install Python dependencies
echo "[3/4] Installing Python dependencies..."
pip3 install -q --break-system-packages -r "$REPO_DIR/server/requirements.txt" 2>/dev/null || \
pip3 install -q -r "$REPO_DIR/server/requirements.txt"

# Make scripts executable
chmod +x "$REPO_DIR/setup/network-check.sh"

# Install systemd services (with actual repo path substituted in)
echo "[4/4] Setting up systemd services..."
sed "s|/opt/splitflap-os|$REPO_DIR|g" "$REPO_DIR/setup/splitflap-network.service" > /etc/systemd/system/splitflap-network.service
sed "s|/opt/splitflap-os|$REPO_DIR|g" "$REPO_DIR/setup/splitflap.service" > /etc/systemd/system/splitflap.service
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
echo "=== Splitflap OS installed ==="
echo ""
echo "  Start now:     sudo systemctl start splitflap.service"
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
