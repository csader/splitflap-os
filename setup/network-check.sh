#!/bin/bash
# network-check.sh — Fallback to hotspot if no WiFi connection found
# For Raspberry Pi OS Bookworm (NetworkManager-based)
# Runs on boot after network-online.target.

STATUS_FILE="/tmp/splitflap-network-mode"
HOTSPOT_SSID="${SPLITFLAP_HOTSPOT_SSID:-SplitflapOS}"
HOTSPOT_PASS="${SPLITFLAP_HOTSPOT_PASS:-splitflap}"
TIMEOUT=60

echo "wifi" > "$STATUS_FILE"

# Check if wlan0 has a real (non-link-local) IP address
has_wifi_ip() {
    ip addr show wlan0 2>/dev/null \
        | grep -E "inet [0-9]" \
        | grep -v "169\.254\." \
        | grep -q "."
}

# Wait for a real IP on wlan0
echo "[splitflap-network] Waiting up to ${TIMEOUT}s for WiFi IP..."
for i in $(seq 1 $TIMEOUT); do
    if has_wifi_ip; then
        IP=$(ip addr show wlan0 | grep -E "inet [0-9]" | grep -v "169\.254\." | awk '{print $2}' | cut -d/ -f1 | head -1)
        echo "[splitflap-network] WiFi connected: $IP"
        echo "wifi" > "$STATUS_FILE"
        exit 0
    fi
    sleep 1
done

# No WiFi IP found — check if we're already in hotspot mode before creating one
if nmcli -t -f TYPE,STATE con show --active 2>/dev/null | grep -q "wifi:activated"; then
    # WiFi is active but no IP yet — something is wrong, don't clobber it
    echo "[splitflap-network] WiFi active but no IP — skipping hotspot"
    echo "wifi" > "$STATUS_FILE"
    exit 0
fi

# No WiFi at all — start hotspot via NetworkManager
echo "[splitflap-network] No WiFi found. Starting hotspot..."

nmcli device wifi hotspot ifname wlan0 ssid "$HOTSPOT_SSID" password "$HOTSPOT_PASS" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "[splitflap-network] Hotspot active: $HOTSPOT_SSID"
    echo "hotspot" > "$STATUS_FILE"
else
    echo "[splitflap-network] ERROR: Failed to start hotspot"
    echo "error" > "$STATUS_FILE"
    exit 1
fi
