#!/bin/bash
# network-check.sh — Fallback to hotspot if no WiFi connection found
# For Raspberry Pi OS Bookworm (NetworkManager-based)
# Runs on boot before the Flask server starts.

STATUS_FILE="/tmp/splitflap-network-mode"
HOTSPOT_SSID="${SPLITFLAP_HOTSPOT_SSID:-SplitflapOS}"
HOTSPOT_PASS="${SPLITFLAP_HOTSPOT_PASS:-splitflap}"
TIMEOUT=30

echo "wifi" > "$STATUS_FILE"

# Wait for WiFi connection
echo "[splitflap-network] Waiting up to ${TIMEOUT}s for WiFi..."
for i in $(seq 1 $TIMEOUT); do
    # Check if any WiFi connection is active
    if nmcli -t -f TYPE,STATE con show --active | grep -q "wifi:activated"; then
        IP=$(nmcli -t -f IP4.ADDRESS dev show wlan0 2>/dev/null | head -1 | cut -d: -f2 | cut -d/ -f1)
        echo "[splitflap-network] WiFi connected: $IP"
        echo "wifi" > "$STATUS_FILE"
        exit 0
    fi
    sleep 1
done

# No WiFi — start hotspot via NetworkManager
echo "[splitflap-network] No WiFi found. Starting hotspot..."

nmcli device wifi hotspot ifname wlan0 ssid "$HOTSPOT_SSID" password "$HOTSPOT_PASS" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "[splitflap-network] Hotspot active: $HOTSPOT_SSID @ 192.168.4.1"
    echo "hotspot" > "$STATUS_FILE"
else
    echo "[splitflap-network] ERROR: Failed to start hotspot"
    echo "error" > "$STATUS_FILE"
    exit 1
fi
