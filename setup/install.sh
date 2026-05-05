#!/bin/bash
# install.sh — Set up Splitflap OS on a Raspberry Pi (Bookworm)
# Run as root: sudo bash setup/install.sh

set -e

INSTALL_DIR="/opt/splitflap-os"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Splitflap OS Installer ==="
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run as root (sudo bash setup/install.sh)"
    exit 1
fi

# Install system packages
echo "[1/5] Installing system packages..."
apt-get update -qq
apt-get install -y -qq python3-pip python3-venv network-manager > /dev/null

# Ensure NetworkManager manages WiFi
echo "[2/5] Configuring NetworkManager..."
if ! systemctl is-active --quiet NetworkManager; then
    systemctl enable NetworkManager
    systemctl start NetworkManager
fi

# Install Python dependencies
echo "[3/5] Installing Python dependencies..."
pip3 install -q --break-system-packages -r "$REPO_DIR/server/requirements.txt" 2>/dev/null || \
pip3 install -q -r "$REPO_DIR/server/requirements.txt"

# Copy project to install directory
echo "[4/5] Installing to $INSTALL_DIR..."
if [ "$REPO_DIR" != "$INSTALL_DIR" ]; then
    mkdir -p "$INSTALL_DIR"
    rsync -a --delete "$REPO_DIR/" "$INSTALL_DIR/"
fi

# Make scripts executable
chmod +x "$INSTALL_DIR/setup/network-check.sh"

# Install systemd services
echo "[5/5] Setting up systemd services..."
cp "$INSTALL_DIR/setup/splitflap-network.service" /etc/systemd/system/
cp "$INSTALL_DIR/setup/splitflap.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable splitflap-network.service
systemctl enable splitflap.service

# Create settings.json if it doesn't exist
if [ ! -f "$INSTALL_DIR/server/settings.json" ]; then
    echo "{}" > "$INSTALL_DIR/server/settings.json"
fi

echo ""
echo "=== Splitflap OS installed ==="
echo ""
echo "  Start now:     sudo systemctl start splitflap.service"
echo "  View logs:     journalctl -u splitflap -f"
echo "  Network logs:  journalctl -u splitflap-network -f"
echo ""
echo "  WiFi hotspot fallback is enabled."
echo "  If no WiFi is found on boot, the Pi will create:"
echo "    SSID: SplitflapOS"
echo "    Password: splitflap"
echo "    UI: http://10.42.0.1"
echo ""
echo "  To change hotspot credentials, set environment variables:"
echo "    SPLITFLAP_HOTSPOT_SSID and SPLITFLAP_HOTSPOT_PASS"
echo "    in /etc/systemd/system/splitflap-network.service"
echo ""
