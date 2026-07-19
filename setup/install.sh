#!/bin/bash
# install.sh — Set up Splitflap OS.
#
# Supported targets:
#   * Raspberry Pi OS / Debian / Ubuntu (apt): full install — system packages,
#     Python venv, WiFi-hotspot fallback and systemd services.
#   * Other Linux (no apt): installs the Python venv and, if systemd is present,
#     the services. You install python3/pip/venv (and NetworkManager for the
#     hotspot) yourself with your own package manager.
#   * macOS: installs the Python venv only. No system packages, no networking and
#     no services are touched — you run the server yourself. You are responsible
#     for installing python3, pip and venv (e.g. `brew install python`).
#
# Run from the repo directory. On Linux the package/service steps need root:
#   sudo bash setup/install.sh
# On macOS run it without sudo:
#   bash setup/install.sh
# Flags: --skip-network  skip the hotspot/NetworkManager setup (implied on macOS)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$REPO_DIR/venv"
SKIP_NETWORK=false

for arg in "$@"; do
    case "$arg" in
        --skip-network) SKIP_NETWORK=true ;;
    esac
done

# --- Detect platform -------------------------------------------------------
# apt (Debian/Ubuntu/Raspberry Pi OS) and systemd decide what we can automate.
# Anything we can't automate is skipped with a note telling the user what to do.
OS="$(uname -s)"
IS_MAC=false
HAS_APT=false
HAS_SYSTEMD=false
[ "$OS" = "Darwin" ] && IS_MAC=true
command -v apt-get   >/dev/null 2>&1 && HAS_APT=true
command -v systemctl >/dev/null 2>&1 && HAS_SYSTEMD=true

# The systemd services (and the WiFi-hotspot fallback that rides on them) only
# make sense where systemd exists. On macOS we skip networking unconditionally,
# even if the user didn't pass --skip-network.
SKIP_SERVICES=false
if $IS_MAC; then
    SKIP_NETWORK=true
    SKIP_SERVICES=true
elif ! $HAS_SYSTEMD; then
    SKIP_NETWORK=true
    SKIP_SERVICES=true
fi

PLATFORM_LABEL="$OS"
$IS_MAC && PLATFORM_LABEL="macOS"

echo "=== Splitflap OS Installer ==="
echo "  Installing from: $REPO_DIR"
echo "  Platform:        $PLATFORM_LABEL"
$SKIP_NETWORK  && echo "  Network/hotspot: SKIPPED"
$SKIP_SERVICES && echo "  System service:  SKIPPED (you run the server manually)"
echo ""

# --- Root check ------------------------------------------------------------
# Only the privileged steps need root: apt installs and writing systemd units.
# A macOS or service-less-Linux install runs entirely in userspace.
NEED_ROOT=false
if $HAS_APT; then NEED_ROOT=true; fi
if ! $SKIP_SERVICES; then NEED_ROOT=true; fi
if $NEED_ROOT && [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run as root (sudo bash setup/install.sh)"
    exit 1
fi

# --- [1/4] System packages -------------------------------------------------
if $IS_MAC; then
    echo "[1/4] macOS — skipping system packages."
    echo "  NOTE: You are responsible for installing python3, pip and venv yourself"
    echo "        (e.g. 'brew install python')."
elif $HAS_APT; then
    echo "[1/4] Installing system packages (apt)..."
    apt-get update -qq
    if $SKIP_NETWORK; then
        apt-get install -y python3-pip python3-venv libopenblas0
    else
        apt-get install -y python3-pip python3-venv network-manager libopenblas0
    fi
else
    echo "[1/4] Non-Debian Linux — skipping system package install."
    echo "  NOTE: Install these yourself with your package manager: python3, pip,"
    echo "        the python venv module, and libopenblas (for numpy/pandas)."
    if ! $SKIP_NETWORK; then
        echo "        Also install NetworkManager for the WiFi hotspot fallback."
    fi
fi

# --- [2/4] NetworkManager --------------------------------------------------
if $SKIP_NETWORK; then
    echo "[2/4] Skipping network configuration..."
else
    echo "[2/4] Configuring NetworkManager..."
    if ! systemctl is-active --quiet NetworkManager; then
        systemctl enable NetworkManager
        systemctl start NetworkManager
    fi
fi

# --- [3/4] Python venv + dependencies --------------------------------------
# A venv avoids PEP 668 conflicts on Bookworm/Trixie and keeps dependencies
# isolated from the system Python. --prefer-binary uses pre-built wheels — much
# faster on Pi Zero W (ARMv6).
echo "[3/4] Installing Python dependencies..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found. Install Python 3 (with pip and the venv module)"
    echo "       and re-run this script."
    exit 1
fi
if [ ! -d "$VENV_DIR" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi
echo "  Installing packages (this may take a while on Pi Zero W)..."
"$VENV_DIR/bin/pip" install --prefer-binary -r "$REPO_DIR/server/requirements.txt"

# --- [4/4] systemd services ------------------------------------------------
if $SKIP_SERVICES; then
    if $IS_MAC; then
        echo "[4/4] macOS — skipping systemd services."
    else
        echo "[4/4] No systemd — skipping services."
    fi
else
    echo "[4/4] Setting up systemd services..."

    # Make scripts executable
    chmod +x "$REPO_DIR/setup/network-check.sh"

    # Install systemd services (preserve existing Environment= variables)
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

    if ! $SKIP_NETWORK; then
        install_service "$REPO_DIR/setup/splitflap-network.service" /etc/systemd/system/splitflap-network.service
    fi
    install_service "$REPO_DIR/setup/splitflap.service" /etc/systemd/system/splitflap.service
    systemctl daemon-reload
    if ! $SKIP_NETWORK; then
        systemctl enable splitflap-network.service
        systemctl restart splitflap-network.service
    fi
    systemctl enable splitflap.service
    systemctl restart splitflap.service
fi

# Create settings.json if it doesn't exist
if [ ! -f "$REPO_DIR/server/settings.json" ]; then
    echo "{}" > "$REPO_DIR/server/settings.json"
fi

# --- Summary ---------------------------------------------------------------
echo ""
if $SKIP_SERVICES; then
    echo "=== Splitflap OS dependencies installed ==="
    echo ""
    echo "  No system service was installed on this platform — start the server yourself:"
    echo "    cd \"$REPO_DIR/server\" && sudo \"$VENV_DIR/bin/python\" app.py"
    echo "  (it binds port 80, so it needs sudo; then open http://localhost)"
    echo ""
    echo "  To update:  cd \"$REPO_DIR\" && git pull && bash setup/install.sh"
    echo ""
else
    echo "=== Splitflap OS installed and running ==="
    echo ""
    IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
    echo "  Access UI:     http://${IP:-<this-host-ip>}"
    echo "  View logs:     journalctl -u splitflap -f"
    if ! $SKIP_NETWORK; then
        echo "  Network logs:  journalctl -u splitflap-network -f"
    fi
    echo ""
    echo "  To update:     cd \"$REPO_DIR\" && git pull && sudo bash setup/install.sh"
    echo ""
    if ! $SKIP_NETWORK; then
        echo "  WiFi hotspot fallback is enabled."
        echo "  If no WiFi is found on boot, the Pi will create:"
        echo "    SSID: SplitflapOS"
        echo "    Password: splitflap"
        echo ""
        echo "  To change hotspot credentials, edit:"
        echo "    /etc/systemd/system/splitflap-network.service"
        echo ""
    fi
fi
