import serial
import time
import threading
import json
import os
import logging
import random
import requests
import pytz
import yfinance as yf
import importlib.util
import urllib.request
import shutil
from datetime import datetime
from flask import Flask, render_template, request, jsonify

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None
    logging.warning("paho-mqtt not installed — MQTT integration disabled")

SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 9600
CONFIG_PATH = os.environ.get(
    "SPLITFLAP_CONFIG",
    os.path.join(os.path.dirname(__file__), "settings.json")
)
APPS_PATH = os.path.join(os.path.dirname(__file__), '..', 'apps')
VERSION_FILE = os.path.join(os.path.dirname(__file__), '..', 'VERSION')

def _read_version():
    try:
        with open(VERSION_FILE, 'r') as f:
            return f.read().strip()
    except Exception:
        return 'unknown'

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

serial_lock = threading.Lock()

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.5)
except Exception as e:
    ser = None
    logging.error(f"Serial failed. Simulation Mode. Reason: {e}")

# --- GLOBAL STATE ---
FLAP_CHARS = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$&()-+=;q:%'.,/?*roygbpw"
current_indices = [-1] * 45  # resized after settings load
current_display_string = " " * 45
is_homed = False
sim_mode = not ser  # auto-enable simulation if no serial hardware


# ============================================================
#  SETTINGS
# ============================================================

def load_settings():
    # Detect system timezone
    sys_tz = 'US/Eastern'
    try:
        import subprocess
        result = subprocess.run(['cat', '/etc/timezone'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0 and result.stdout.strip():
            sys_tz = result.stdout.strip()
    except Exception:
        try:
            link = os.readlink('/etc/localtime')
            sys_tz = link.split('zoneinfo/')[-1]
        except Exception:
            pass
    defaults = {
        "offsets":       {str(i): 2832 for i in range(45)},
        "calibrations":  {str(i): 4096 for i in range(45)},
        "tuned_chars":   {str(i): {} for i in range(45)},
        "zip_code":      "02118",
        "timezone":      sys_tz,
        "weather_api_key": "",
        "mbta_stop":     "place-bbsta",
        "mbta_route":    "Orange",
        "stocks_list":   "MSFT,GOOG,NVDA",
        "nhl_teams":     "BOS,DAL",
        "yt_channel_id": "UC2GJfspFn6o4liy6GaBFtHA",
        "yt_api_key":    "",
        "yt_video_id":   "",
        "auto_home":     True,
        "countdown_event":   "NEW YEAR",
        "countdown_target":  "2027-01-01T00:00:00",
        "world_clock_zones": "US/Eastern,US/Pacific,Europe/London",
        "crypto_list":   "bitcoin,ethereum,solana",
        "anim_style":    "ltr",
        "anim_speed":    "0.4",
        "anim_text":     "SPLIT  FLAP  DISPLAY",
        "saved_playlists": {},
        "livestream_interval": "25",
        "livestream_comments": "",
        "sports_nfl":   "",
        "sports_nba":   "",
        "sports_mlb":   "",
        "sports_nhl":   "",
        "sports_ncaaf": "",
        "sports_ncaab": "",
        "sports_mls":   "",
        "sports_epl":   "",
        "sports_laliga":"",
        "sports_ucl":   "",
        "sports_wnba":  "",
        "sports_pga":   "",
        "sports_ufc":   "",
        "mqtt_enabled":  False,
        "mqtt_broker":   "homeassistant.local",
        "mqtt_port":     1883,
        "mqtt_user":     "",
        "mqtt_password": "",
        "sim_rows": 3,
        "sim_cols": 15,
        "app_library_url": "https://raw.githubusercontent.com/csader/splitflap-os/main/apps",
        "installed_apps": [
            "time", "date", "weather", "stocks", "sports", "countdown",
            "world_clock", "crypto", "iss", "metro", "youtube", "yt_comments",
            "dashboard", "demo", "livestream",
            "anim_rainbow", "anim_sweep", "anim_twinkle", "anim_checker", "anim_matrix",
            "word-clock", "moon-phase", "star-wars-quotes",
        ],
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                defaults.update(data)
                if "tuned_chars" not in defaults:
                    defaults["tuned_chars"] = {str(i): {} for i in range(45)}
                return defaults
        except:
            pass
    return defaults

def save_settings(data):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

settings = load_settings()


# ============================================================
#  GRID HELPERS
# ============================================================

def get_rows(): return int(settings.get('sim_rows', 3))
def get_cols(): return int(settings.get('sim_cols', 15))
def get_module_count(): return get_rows() * get_cols()

def resize_grid():
    global current_indices, current_display_string
    n = get_module_count()
    current_indices = [-1] * n
    current_display_string = " " * n

resize_grid()


# ============================================================
#  SPORTS LEAGUE REGISTRY
# ============================================================

SPORTS_LEAGUES = {
    'nfl':    {'path': 'football/nfl',                       'name': 'NFL'},
    'nba':    {'path': 'basketball/nba',                     'name': 'NBA'},
    'mlb':    {'path': 'baseball/mlb',                       'name': 'MLB'},
    'nhl':    {'path': 'hockey/nhl',                         'name': 'NHL'},
    'ncaaf':  {'path': 'football/college-football',          'name': 'NCAAF'},
    'ncaab':  {'path': 'basketball/mens-college-basketball', 'name': 'NCAAB'},
    'mls':    {'path': 'soccer/usa.1',                       'name': 'MLS'},
    'epl':    {'path': 'soccer/eng.1',                       'name': 'EPL'},
    'laliga': {'path': 'soccer/esp.1',                       'name': 'LALIGA'},
    'ucl':    {'path': 'soccer/uefa.champions',              'name': 'UCL'},
    'wnba':   {'path': 'basketball/wnba',                    'name': 'WNBA'},
    'ncaaw':  {'path': 'basketball/womens-college-basketball','name': 'NCAAW'},
    'soft':   {'path': 'baseball/college-softball',          'name': 'SOFTBALL'},
    'msoc':   {'path': 'soccer/usa.ncaa.m.1',               'name': 'MSOC'},
    'wsoc':   {'path': 'soccer/usa.ncaa.w.1',               'name': 'WSOC'},
    'pga':    {'path': 'golf/pga',                           'name': 'PGA'},
    'ufc':    {'path': 'mma/ufc',                            'name': 'UFC'},
}


# ============================================================
#  MQTT INTEGRATION
# ============================================================

MQTT_TOPIC_PREFIX = "splitflap"
MQTT_AVAIL_TOPIC = f"{MQTT_TOPIC_PREFIX}/availability"
MQTT_TEXT_CMD     = f"{MQTT_TOPIC_PREFIX}/text/set"
MQTT_TEXT_STATE   = f"{MQTT_TOPIC_PREFIX}/text/state"
MQTT_MODE_CMD     = f"{MQTT_TOPIC_PREFIX}/app/set"
MQTT_MODE_STATE   = f"{MQTT_TOPIC_PREFIX}/app/state"
MQTT_STATUS_STATE = f"{MQTT_TOPIC_PREFIX}/status/state"
MQTT_CENTER_CMD   = f"{MQTT_TOPIC_PREFIX}/center/set"
MQTT_CENTER_STATE = f"{MQTT_TOPIC_PREFIX}/center/state"
MQTT_PLAYLIST_CMD = f"{MQTT_TOPIC_PREFIX}/playlist/set"
MQTT_PLAYLIST_STATE = f"{MQTT_TOPIC_PREFIX}/playlist/state"

MQTT_DEVICE = {
    "identifiers": ["splitflap_display"],
    "name": "Split-Flap Display",
    "manufacturer": "Adam G Makes",
    "model": "SplitFlap 45-Module",
}

mqtt_client = None


def _get_mqtt_app_options():
    """Build dynamic app list from plugin registry."""
    return ["off"] + sorted(_plugin_registry.keys())


def _get_mqtt_playlist_options():
    """Build playlist list from saved playlists."""
    return ["off"] + sorted(settings.get('saved_app_playlists', {}).keys())


def mqtt_publish_state():
    """Publish current display state and active mode to MQTT."""
    if not mqtt_client or not mqtt_client.is_connected():
        return
    mqtt_client.publish(MQTT_STATUS_STATE, current_display_string, retain=True)
    mqtt_client.publish(MQTT_MODE_STATE, active_app or "off", retain=True)
    center_state = "ON" if settings.get('mqtt_center', True) else "OFF"
    mqtt_client.publish(MQTT_CENTER_STATE, center_state, retain=True)
    mqtt_client.publish(MQTT_PLAYLIST_STATE, app_playlist_name or "off", retain=True)


def mqtt_publish_discovery():
    """Publish Home Assistant MQTT discovery config for all entities."""
    if not mqtt_client:
        return
    avail = {"topic": MQTT_AVAIL_TOPIC, "payload_available": "online", "payload_not_available": "offline"}

    configs = [
        ("text", "splitflap_text", {
            "unique_id": "splitflap_text",
            "name": "Display Text (use | for line breaks)",
            "command_topic": MQTT_TEXT_CMD,
            "state_topic": MQTT_TEXT_STATE,
            "min": 0,
            "max": 45,
            "mode": "text",
            "availability": avail,
            "device": MQTT_DEVICE,
        }),
        ("select", "splitflap_app", {
            "unique_id": "splitflap_app",
            "name": "Active App",
            "command_topic": MQTT_MODE_CMD,
            "state_topic": MQTT_MODE_STATE,
            "options": _get_mqtt_app_options(),
            "availability": avail,
            "device": MQTT_DEVICE,
        }),
        ("select", "splitflap_playlist", {
            "unique_id": "splitflap_playlist",
            "name": "Playlist",
            "command_topic": MQTT_PLAYLIST_CMD,
            "state_topic": MQTT_PLAYLIST_STATE,
            "options": _get_mqtt_playlist_options(),
            "availability": avail,
            "device": MQTT_DEVICE,
        }),
        ("switch", "splitflap_center", {
            "unique_id": "splitflap_center",
            "name": "Center Text",
            "command_topic": MQTT_CENTER_CMD,
            "state_topic": MQTT_CENTER_STATE,
            "payload_on": "ON",
            "payload_off": "OFF",
            "availability": avail,
            "device": MQTT_DEVICE,
        }),
        ("sensor", "splitflap_status", {
            "unique_id": "splitflap_status",
            "name": "Display Status",
            "state_topic": MQTT_STATUS_STATE,
            "availability": avail,
            "device": MQTT_DEVICE,
        }),
        ("sensor", "splitflap_network_mode", {
            "unique_id": "splitflap_network_mode",
            "name": "Network Mode",
            "state_topic": f"{MQTT_TOPIC_PREFIX}/network/mode",
            "icon": "mdi:wifi",
            "availability": avail,
            "device": MQTT_DEVICE,
        }),
        ("sensor", "splitflap_network_ssid", {
            "unique_id": "splitflap_network_ssid",
            "name": "WiFi SSID",
            "state_topic": f"{MQTT_TOPIC_PREFIX}/network/ssid",
            "icon": "mdi:wifi",
            "availability": avail,
            "device": MQTT_DEVICE,
        }),
        ("sensor", "splitflap_network_ip", {
            "unique_id": "splitflap_network_ip",
            "name": "IP Address",
            "state_topic": f"{MQTT_TOPIC_PREFIX}/network/ip",
            "icon": "mdi:ip-network",
            "availability": avail,
            "device": MQTT_DEVICE,
        }),
        ("binary_sensor", "splitflap_online", {
            "unique_id": "splitflap_online",
            "name": "Internet Connected",
            "state_topic": f"{MQTT_TOPIC_PREFIX}/network/online",
            "payload_on": "ON",
            "payload_off": "OFF",
            "device_class": "connectivity",
            "availability": avail,
            "device": MQTT_DEVICE,
        }),
        ("button", "splitflap_home", {
            "unique_id": "splitflap_home",
            "name": "Home All",
            "command_topic": f"{MQTT_TOPIC_PREFIX}/home/set",
            "icon": "mdi:home-import-outline",
            "availability": avail,
            "device": MQTT_DEVICE,
        }),
    ]
    for component, object_id, payload in configs:
        topic = f"homeassistant/{component}/{object_id}/config"
        mqtt_client.publish(topic, json.dumps(payload), retain=True)
    # Remove deprecated entities
    mqtt_client.publish("homeassistant/select/splitflap_mode/config", "", retain=True)
    logging.info("MQTT discovery payloads published")


def _mqtt_on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0 or (hasattr(rc, 'is_failure') and not rc.is_failure):
        logging.info("MQTT connected to broker")
        client.subscribe(MQTT_TEXT_CMD)
        client.subscribe(MQTT_MODE_CMD)
        client.subscribe(MQTT_CENTER_CMD)
        client.subscribe(MQTT_PLAYLIST_CMD)
        client.subscribe(f"{MQTT_TOPIC_PREFIX}/home/set")
        client.subscribe("homeassistant/status")
        client.publish(MQTT_AVAIL_TOPIC, "online", retain=True)
        mqtt_publish_discovery()
        mqtt_publish_state()
    else:
        logging.error(f"MQTT connection failed with code {rc}")


def _mqtt_on_message(client, userdata, msg):
    global active_app, current_playlist, last_sent_page, loop_delay
    global active_app_playlist, app_playlist_loop, app_playlist_name
    payload = msg.payload.decode('utf-8', errors='ignore').strip()

    if msg.topic == "homeassistant/status" and payload == "online":
        mqtt_publish_discovery()
        mqtt_publish_state()
        return

    if msg.topic == MQTT_TEXT_CMD:
        active_app = None
        active_app_playlist = None
        if settings.get('mqtt_center', True):
            lines = payload.split('|')
            current_playlist = [format_lines(*lines)]
        else:
            current_playlist = [payload]
        last_sent_page = None
        stop_event.set()
        mqtt_publish_state()

    elif msg.topic == MQTT_CENTER_CMD:
        settings['mqtt_center'] = (payload.upper() == 'ON')
        save_settings(settings)
        mqtt_publish_state()

    elif msg.topic == MQTT_MODE_CMD:
        if payload == "off":
            active_app = None
            active_app_playlist = None
            stop_event.set()
        elif payload in _plugin_registry:
            active_app = payload
            active_app_playlist = None
            manifest = _plugin_registry[payload]
            if manifest.get('animation'):
                loop_delay = max(0.1, float(settings.get('anim_speed', '0.4')))
            else:
                saved = settings.get(f'plugin_{payload}_loop_delay', '')
                loop_delay = float(saved) if saved else float(manifest.get('loop_delay', 5))
            stop_event.set()
        mqtt_publish_state()

    elif msg.topic == MQTT_PLAYLIST_CMD:
        if payload == "off":
            active_app_playlist = None
            active_app = None
            stop_event.set()
        else:
            playlists = settings.get('saved_app_playlists', {})
            if payload in playlists:
                pl = playlists[payload]
                active_app_playlist = pl.get('entries', [])
                app_playlist_loop = pl.get('loop', True)
                app_playlist_name = payload
                active_app = None
                current_playlist = []
                last_sent_page = None
                stop_event.set()
        mqtt_publish_state()

    elif msg.topic == f"{MQTT_TOPIC_PREFIX}/home/set":
        send_raw("m**h")
        is_homed = True
        current_indices = [0] * get_module_count()
        current_display_string = " " * get_module_count()
        mqtt_publish_state()


def mqtt_setup():
    """Initialize MQTT client and connect to broker. Fails gracefully."""
    global mqtt_client
    if not mqtt or not settings.get('mqtt_enabled', True):
        logging.info("MQTT disabled or paho-mqtt not installed")
        return
    try:
        mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="splitflap_display")
        user = settings.get('mqtt_user', '').strip()
        pw = settings.get('mqtt_password', '').strip()
        if user:
            mqtt_client.username_pw_set(user, pw)
        mqtt_client.will_set(MQTT_AVAIL_TOPIC, "offline", qos=1, retain=True)
        mqtt_client.on_connect = _mqtt_on_connect
        mqtt_client.on_message = _mqtt_on_message
        broker = settings.get('mqtt_broker', 'homeassistant.local')
        port = int(settings.get('mqtt_port', 1883))
        mqtt_client.connect_async(broker, port)
        mqtt_client.loop_start()
        logging.info(f"MQTT connecting to {broker}:{port}")
    except Exception as e:
        mqtt_client = None
        logging.error(f"MQTT setup failed: {e}")


def mqtt_reconnect():
    """Disconnect and reconnect MQTT with current settings."""
    global mqtt_client
    if mqtt_client:
        try:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
        except Exception:
            pass
        mqtt_client = None
    mqtt_setup()


mqtt_setup()


# ============================================================
#  SERIAL HELPERS
# ============================================================

def send_raw(cmd):
    if not cmd.endswith('\n'):
        cmd += '\n'
    with serial_lock:
        if ser and not sim_mode:
            ser.write(cmd.encode())
            ser.flush()
            time.sleep(0.02)

def sync_hardware_data(mod_id):
    if not ser:
        return False
    with serial_lock:
        ser.reset_input_buffer()
        ser.write(f"m{mod_id:02d}d\n".encode())
        ser.flush()
        start = time.time()
        buffer = ""
        target = f"m{mod_id:02d}d:"
        while time.time() - start < 5.0:
            if ser.in_waiting > 0:
                try:
                    chunk = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                    buffer += chunk
                    if target in buffer and '\n' in buffer[buffer.find(target):]:
                        valid_part = buffer[buffer.find(target):].split('\n')[0]
                        data = valid_part.split('d:', 1)[1]
                        parts = data.split(':')
                        if len(parts) >= 2:
                            settings['offsets'][str(mod_id)] = int(parts[0])
                            settings['calibrations'][str(mod_id)] = int(parts[1])
                            settings['tuned_chars'][str(mod_id)] = {}
                            if len(parts) == 3 and parts[2]:
                                for p in parts[2].split(','):
                                    if '=' in p:
                                        idx, val = p.split('=')
                                        settings['tuned_chars'][str(mod_id)][idx] = int(val)
                            save_settings(settings)
                            return True
                except Exception as e:
                    logging.error(f"Parse error: {e}")
            time.sleep(0.05)
    return False


# ============================================================
#  ANIMATION ORDER GENERATORS
# ============================================================

def get_animation_order(style='ltr', rows=None, cols=None):
    """Return a list of the module indices in the requested send order."""
    rows = rows or get_rows()
    cols = cols or get_cols()
    total = rows * cols
    def m(r, c): return r * cols + c

    if style == 'rtl':
        return list(range(total - 1, -1, -1))

    elif style == 'center_out':
        order, seen = [], set()
        center = cols // 2
        for d in range(center + 1):
            for r in range(rows):
                cs = [center] if d == 0 else [center - d, center + d]
                for c in cs:
                    if 0 <= c < cols:
                        idx = m(r, c)
                        if idx not in seen:
                            seen.add(idx); order.append(idx)
        return order

    elif style == 'outside_in':
        return list(reversed(get_animation_order('center_out', rows, cols)))

    elif style == 'spiral':
        vis = [[False] * cols for _ in range(rows)]
        order = []
        top, bottom, left, right = 0, rows - 1, 0, cols - 1
        while top <= bottom and left <= right:
            for c in range(left, right + 1):
                if not vis[top][c]:
                    vis[top][c] = True; order.append(m(top, c))
            for r in range(top + 1, bottom + 1):
                if not vis[r][right]:
                    vis[r][right] = True; order.append(m(r, right))
            if top < bottom:
                for c in range(right - 1, left - 1, -1):
                    if not vis[bottom][c]:
                        vis[bottom][c] = True; order.append(m(bottom, c))
            if left < right:
                for r in range(bottom - 1, top, -1):
                    if not vis[r][left]:
                        vis[r][left] = True; order.append(m(r, left))
            top += 1; bottom -= 1; left += 1; right -= 1
        return order

    elif style == 'diagonal':
        order, seen = [], set()
        for d in range(rows + cols - 1):
            for r in range(rows):
                c = d - r
                if 0 <= c < cols:
                    idx = m(r, c)
                    if idx not in seen:
                        seen.add(idx); order.append(idx)
        return order

    elif style == 'anti_diagonal':
        order, seen = [], set()
        for d in range(rows + cols - 1):
            for r in range(rows):
                c = (cols - 1 - d) + r
                if 0 <= c < cols:
                    idx = m(r, c)
                    if idx not in seen:
                        seen.add(idx); order.append(idx)
        return order

    elif style == 'random':
        return random.sample(range(total), total)

    elif style == 'rain':
        return [m(r, c) for r in range(rows) for c in range(cols)]

    elif style == 'reverse_rain':
        return [m(r, c) for r in range(rows - 1, -1, -1) for c in range(cols)]

    elif style == 'columns':
        return [m(r, c) for c in range(cols) for r in range(rows)]

    elif style == 'columns_rtl':
        return [m(r, c) for c in range(cols - 1, -1, -1) for r in range(rows)]

    elif style == 'alternating':
        order = []
        for c in range(cols):
            for r in range(rows):
                ac = c if r % 2 == 0 else (cols - 1 - c)
                order.append(m(r, ac))
        return order

    return list(range(total))  # default ltr


# ============================================================
#  DISPLAY
# ============================================================

COLOR_MAP = {
    '\U0001f7e5': 'r', '\U0001f7e7': 'o', '\U0001f7e8': 'y', '\U0001f7e9': 'g',
    '\U0001f7e6': 'b', '\U0001f7ea': 'p', '\u2b1c': 'w', '\u2b1b': ' ',
}

def send_to_display(text, order=None, raw=False, step_delay_ms=15):
    global current_indices, current_display_string, is_homed
    if not text:
        return 0

    # For normal text: uppercase first (emojis are unaffected by upper()),
    # then replace emojis with color codes. Animation pages pass raw=True to
    # skip uppercasing so their color codes (r o y g b p w) stay lowercase.
    if not raw:
        clean_text = text.upper()
    else:
        clean_text = text
    for emoji, char in COLOR_MAP.items():
        clean_text = clean_text.replace(emoji, char)
    # The physical " flap is addressed as 'q' in the firmware character map
    clean_text = clean_text.replace('"', 'q')
    n = get_module_count()
    clean_text = clean_text.ljust(n)[:n]
    logging.info(f"DISPLAY: {clean_text}")

    if order is None:
        order = list(range(n))

    max_dist = 0
    with serial_lock:
        for i in order:
            if i >= len(clean_text):
                continue
            char = clean_text[i]
            if ser and not sim_mode:
                ser.write(f"m{i:02d}-{char}\n".encode())
                ser.flush()
                time.sleep(step_delay_ms / 1000.0)

            target_idx = FLAP_CHARS.find(char)
            if target_idx == -1:
                target_idx = 0
            dist = 128 if current_indices[i] == -1 else (target_idx - current_indices[i]) % 64
            if dist > max_dist:
                max_dist = dist
            current_indices[i] = target_idx

    current_display_string = clean_text
    is_homed = True
    mqtt_publish_state()
    return max_dist



# ============================================================
#  APP DATA FETCHERS
# ============================================================

def format_lines(*lines, cols=None):
    cols = cols or get_cols()
    rows = get_rows()
    padded = list(lines) + [''] * (rows - len(lines))
    return ''.join(l.center(cols)[:cols] for l in padded[:rows])


# ============================================================
#  PLUGIN SYSTEM
# ============================================================
# SECURITY NOTE: Functional plugins execute arbitrary Python code.
# Only install apps from trusted sources. Plugins run with the same
# permissions as this Flask app. There is no sandboxing.

_plugin_registry = {}
_plugin_modules = {}
_plugin_data = {}
_plugin_caches = {}
_registry_cache = {'data': None, 'fetched_at': 0}


def load_installed_plugins():
    global _plugin_registry, _plugin_modules, _plugin_data
    _plugin_registry.clear()
    _plugin_modules.clear()
    _plugin_data.clear()
    if not os.path.isdir(APPS_PATH):
        return
    enabled = settings.get('installed_apps', [])
    for app_id in os.listdir(APPS_PATH):
        if app_id not in enabled:
            continue
        app_dir = os.path.join(APPS_PATH, app_id)
        manifest_path = os.path.join(app_dir, "manifest.json")
        if not os.path.isfile(manifest_path):
            continue
        try:
            with open(manifest_path, "r", encoding='utf-8') as f:
                manifest = json.load(f)
            manifest["id"] = app_id
            _plugin_registry[app_id] = manifest
            if manifest.get("type") == "channel":
                _load_channel_data(app_id, app_dir)
            elif manifest.get("type") == "functional":
                _load_functional_module(app_id, app_dir)
            logging.info(f"Plugin loaded: {app_id} ({manifest.get('type')})")
        except Exception as e:
            logging.error(f"Failed to load plugin {app_id}: {e}")


def _load_channel_data(app_id, app_dir):
    data_path = os.path.join(app_dir, "data.json")
    if not os.path.isfile(data_path):
        return
    try:
        with open(data_path, "r", encoding='utf-8') as f:
            data = json.load(f)
        pages = []
        for page in data.get("pages", []):
            if isinstance(page, str):
                pages.append(page)
            elif isinstance(page, dict) and "lines" in page:
                pages.append(format_lines(*page["lines"]))
        _plugin_data[app_id] = pages
    except Exception as e:
        logging.error(f"Plugin {app_id}: error loading data.json: {e}")


def _load_functional_module(app_id, app_dir):
    module_path = os.path.join(app_dir, "app.py")
    if not os.path.isfile(module_path):
        return
    try:
        spec = importlib.util.spec_from_file_location(f"plugin_{app_id}", module_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "fetch") and callable(mod.fetch):
            _plugin_modules[app_id] = mod
        else:
            logging.error(f"Plugin {app_id}: app.py has no fetch() function")
    except Exception as e:
        logging.error(f"Plugin {app_id}: error importing app.py: {e}")


def get_plugin_pages(app_id):
    manifest = _plugin_registry.get(app_id)
    if not manifest:
        return [format_lines("PLUGIN ERROR", app_id.upper()[:get_cols()], "NOT FOUND")]
    app_type = manifest.get("type")
    refresh_interval = manifest.get("refresh_interval", 300)
    # Allow a plugin setting named 'polling_rate' to override the cache interval
    _poll = settings.get(f"plugin_{app_id}_polling_rate")
    if _poll:
        try:
            refresh_interval = max(10, int(float(_poll)))
        except (ValueError, TypeError):
            pass

    if app_type == "channel":
        pages = _plugin_data.get(app_id, [])
        return pages or [format_lines(manifest.get("name", app_id).upper()[:get_cols()], "NO DATA", "")]

    elif app_type == "functional":
        mod = _plugin_modules.get(app_id)
        if not mod:
            return [format_lines("PLUGIN ERROR", app_id.upper()[:get_cols()], "NOT LOADED")]
        now = time.time()
        cached = _plugin_caches.get(app_id)
        if cached and (now - cached["fetched_at"]) < refresh_interval:
            return cached["pages"]
        try:
            plugin_settings = dict(settings)  # full settings for built-in apps
            for s in manifest.get("settings", []):
                if s.get('global_key'):
                    # global_key settings use the key as-is, already in settings
                    pass
                else:
                    key = f"plugin_{app_id}_{s['key']}"
                    plugin_settings[s["key"]] = settings.get(key, s.get("default", ""))
            pages = mod.fetch(plugin_settings, format_lines, get_rows, get_cols)
            if not isinstance(pages, list):
                pages = [str(pages)]
            _plugin_caches[app_id] = {"pages": pages, "fetched_at": now}
            return pages
        except Exception as e:
            logging.error(f"Plugin {app_id} fetch error: {e}")
            cached_pages = _plugin_caches.get(app_id, {}).get("pages")
            if cached_pages:
                return cached_pages
            # Show OFFLINE for network errors, generic error otherwise
            err_str = str(e).lower()
            if not _is_online or 'timeout' in err_str or 'connection' in err_str or 'network' in err_str:
                return [format_lines(manifest.get("name", app_id).upper()[:get_cols()], "OFFLINE", "")]
            return [format_lines("APP ERROR", app_id.upper()[:get_cols()], str(e)[:get_cols()])]

    return [format_lines("PLUGIN ERROR", "UNKNOWN TYPE", "")]


def get_plugin_app_list():
    entries = []
    for app_id, manifest in _plugin_registry.items():
        entries.append({
            "key": f"plugin_{app_id}",
            "icon": manifest.get("icon", "🧩"),
            "name": manifest.get("name", app_id),
            "desc": manifest.get("description", "")[:30],
            "plugin": True,
            "plugin_id": app_id,
        })
    entries.sort(key=lambda a: a['name'].lower())
    return entries


_SETTING_PASSTHROUGH_KEYS = (
    "size",
    "min",
    "max",
    "step",
    "stepper",
    "searchUrl",
    "resultKey",
    "maxItems",
    "compute",
)


def _resolve_manifest_setting_key(app_id, raw_key, *, global_key=False):
    if global_key:
        return raw_key
    return f"plugin_{app_id}_{raw_key}"


def _build_resolved_settings_lookup(app_id, settings):
    return {
        setting["key"]: _resolve_manifest_setting_key(
            app_id,
            setting["key"],
            global_key=setting.get("global_key", False),
        )
        for setting in settings
        if setting.get("key")
    }


def _normalize_inline_toggle(app_id, inline_toggle):
    inline = dict(inline_toggle)
    inline_key = inline.get("key")
    if inline_key:
        inline["key"] = _resolve_manifest_setting_key(
            app_id,
            inline_key,
            global_key=inline.get("global_key", False),
        )
    return inline


def _normalize_sync_values(sync_values, map_related_key):
    return {
        source_value: {
            map_related_key(target_key): target_value
            for target_key, target_value in target_map.items()
        }
        for source_value, target_map in sync_values.items()
    }


def _build_plugin_setting_field(app_id, setting, resolved_keys):
    raw_key = setting["key"]
    key = resolved_keys[raw_key]

    def map_related_key(raw_related_key):
        if raw_related_key in resolved_keys:
            return resolved_keys[raw_related_key]
        return _resolve_manifest_setting_key(app_id, raw_related_key)

    field = {
        "key": key,
        "label": setting.get("label", raw_key),
        "type": setting.get("type", "text"),
        "ph": setting.get("default", ""),
    }

    if "options" in setting:
        field["opts"] = setting["options"]

    for pass_key in _SETTING_PASSTHROUGH_KEYS:
        if pass_key in setting:
            field[pass_key] = setting[pass_key]

    if "inline_toggle" in setting:
        field["inline_toggle"] = _normalize_inline_toggle(app_id, setting["inline_toggle"])

    if "sync_values" in setting:
        field["sync_values"] = _normalize_sync_values(setting["sync_values"], map_related_key)

    if "sync_parent" in setting:
        field["sync_parent"] = map_related_key(setting["sync_parent"])

    if "sync_parent_custom_value" in setting:
        field["sync_parent_custom_value"] = setting["sync_parent_custom_value"]

    if "visible_when" in setting:
        field["visible_when"] = {
            map_related_key(k): v
            for k, v in setting["visible_when"].items()
        }

    if "watches" in setting:
        field["watches"] = [map_related_key(k) for k in setting["watches"]]

    return field


def get_plugin_settings_config():
    configs = {}
    for app_id, manifest in _plugin_registry.items():
        manifest_settings = [s for s in manifest.get("settings", []) if s.get("key")]
        resolved_keys = _build_resolved_settings_lookup(app_id, manifest_settings)
        fields = [
            _build_plugin_setting_field(app_id, setting, resolved_keys)
            for setting in manifest_settings
        ]

        configs[f"plugin_{app_id}"] = {
            "title": f"{manifest.get('icon', '🧩')} {manifest.get('name', app_id)}",
            "fields": fields,
        }
    return configs


os.makedirs(APPS_PATH, exist_ok=True)
load_installed_plugins()


# ============================================================
#  PLAYLIST LOOP
# ============================================================

current_playlist = []
loop_delay  = 5
stop_event  = threading.Event()
last_sent_page = None
active_app  = None
active_app_playlist = None
app_playlist_loop = True
app_playlist_name = None


def _run_app_playlist():
    """Execute one pass through the app playlist entries."""
    global active_app_playlist, active_app, last_sent_page

    entries = active_app_playlist
    if not entries:
        active_app_playlist = None
        return

    while True:
        for entry in entries:
            if stop_event.is_set():
                stop_event.clear()
                return

            etype = entry.get('type', 'app')
            duration = float(entry.get('duration', 30))

            if etype == 'compose':
                # Send composed text to display
                text = entry.get('text', '')
                style = entry.get('style', 'ltr')
                speed = int(entry.get('speed', 15))
                order = get_animation_order(style)
                max_dist = send_to_display(text, order, step_delay_ms=speed)
                last_sent_page = text
                # Wait for rotation + duration
                rotation_time = max_dist * (4.0 / 64.0)
                for _ in range(int(rotation_time * 10)):
                    if stop_event.is_set():
                        stop_event.clear()
                        return
                    time.sleep(0.1)
                for _ in range(int(duration * 10)):
                    if stop_event.is_set():
                        stop_event.clear()
                        return
                    time.sleep(0.1)

            elif etype == 'app':
                app_key = entry.get('app', '')
                if not app_key:
                    continue
                # Temporarily set active_app so existing fetch logic works
                active_app = app_key
                deadline = time.time() + duration

                while time.time() < deadline:
                    if stop_event.is_set():
                        active_app = None
                        stop_event.clear()
                        return

                    display_pages = _get_pages_for_app(app_key)
                    if not display_pages:
                        time.sleep(1)
                        continue

                    is_anim = app_key.startswith('anim_') or \
                              (app_key in _plugin_registry and _plugin_registry[app_key].get('animation'))

                    # Determine per-page delay
                    reg = app_key[7:] if app_key.startswith('plugin_') else app_key
                    if is_anim:
                        eff_delay = max(0.1, float(settings.get('anim_speed', '0.4')))
                    elif reg in _plugin_registry:
                        saved = settings.get(f'plugin_{reg}_loop_delay', '')
                        default = float(_plugin_registry[reg].get('loop_delay', settings.get('global_loop_delay', 5)))
                        eff_delay = float(saved) if saved else default
                    else:
                        eff_delay = float(settings.get('global_loop_delay', 5))

                    active_order = None
                    if is_anim:
                        active_order = get_animation_order(settings.get('anim_style', 'ltr'))

                    for page in display_pages:
                        if stop_event.is_set() or time.time() >= deadline:
                            break
                        page_text = page.get('text', '') if isinstance(page, dict) else page
                        page_order = get_animation_order(page.get('style', 'ltr')) if isinstance(page, dict) else active_order
                        page_speed = int(page.get('speed', 15)) if isinstance(page, dict) else 15
                        page_delay = float(page.get('delay', eff_delay)) if isinstance(page, dict) else eff_delay

                        if is_anim or page_text != last_sent_page:
                            max_dist = send_to_display(page_text, page_order, raw=is_anim, step_delay_ms=page_speed)
                            last_sent_page = page_text

                        rotation_time = max_dist * (4.0 / 64.0)
                        for _ in range(int(rotation_time * 10)):
                            if stop_event.is_set() or time.time() >= deadline: break
                            time.sleep(0.1)
                        for _ in range(int(page_delay * 10)):
                            if stop_event.is_set() or time.time() >= deadline: break
                            time.sleep(0.1)

                active_app = None

        # After all entries
        if not app_playlist_loop:
            active_app_playlist = None
            return
        # Otherwise loop continues


def _get_pages_for_app(app_key):
    """Fetch display pages for an app via the plugin system."""
    if app_key in _plugin_registry:
        return get_plugin_pages(app_key)
    # Try with plugin_ prefix stripped
    if app_key.startswith('plugin_'):
        return get_plugin_pages(app_key[7:])
    return []


def playlist_loop():
    global current_playlist, loop_delay, last_sent_page, active_app
    global active_app_playlist, app_playlist_loop

    while True:
        now = time.time()
        display_pages = []
        active_order  = None   # custom module send order for this cycle

        # ── App playlist mode ─────────────────────────────
        if active_app_playlist is not None:
            _run_app_playlist()
            continue

        # ── No active app — use compose playlist ──────────
        if active_app is None:
            display_pages = current_playlist

        # ── Plugin-based apps ─────────────────────────────
        elif active_app in _plugin_registry:
            manifest = _plugin_registry[active_app]
            display_pages = get_plugin_pages(active_app)
            if manifest.get('animation'):
                active_order = get_animation_order(settings.get('anim_style', 'ltr'))

        elif active_app.startswith('plugin_') and active_app[7:] in _plugin_registry:
            plugin_id = active_app[7:]
            manifest = _plugin_registry[plugin_id]
            display_pages = get_plugin_pages(plugin_id)
            if manifest.get('animation'):
                active_order = get_animation_order(settings.get('anim_style', 'ltr'))

        else:
            display_pages = current_playlist

        if not display_pages:
            time.sleep(1)
            continue

        # Resolve plugin_ prefix for registry lookups
        reg_key = active_app[7:] if (active_app and active_app.startswith('plugin_')) else active_app

        is_anim = (reg_key is not None and reg_key.startswith('anim_')) or \
                  (reg_key in _plugin_registry and _plugin_registry[reg_key].get('animation'))

        # Effective per-page delay
        if is_anim:
            eff_delay = max(0.1, float(settings.get('anim_speed', '0.4')))
            if reg_key in _plugin_registry:
                eff_delay = max(0.1, float(_plugin_registry[reg_key].get('loop_delay', eff_delay)))
        elif reg_key in _plugin_registry:
            saved = settings.get(f'plugin_{reg_key}_loop_delay', '')
            manifest = _plugin_registry[reg_key]
            default = float(manifest.get('loop_delay', settings.get('global_loop_delay', 5)))
            eff_delay = float(saved) if saved else default
        else:
            eff_delay = float(settings.get('global_loop_delay', loop_delay))

        for page in display_pages:
            if stop_event.is_set():
                break

            # Resolve per-page settings — rich playlist objects vs. plain strings
            if isinstance(page, dict):
                page_text  = page.get('text', '')
                page_delay = float(page.get('delay', eff_delay))
                page_order = get_animation_order(page.get('style', 'ltr'))
                page_speed = int(page.get('speed', 15))
            else:
                page_text  = page
                page_delay = eff_delay
                page_order = active_order
                page_speed = 15

            max_dist = 0
            # Animations always resend each frame; other apps skip unchanged pages
            if is_anim or page_text != last_sent_page:
                max_dist = send_to_display(page_text, page_order, raw=is_anim, step_delay_ms=page_speed)
                last_sent_page = page_text

            rotation_time = max_dist * (4.0 / 64.0)
            for _ in range(int(rotation_time * 10)):
                if stop_event.is_set(): break
                time.sleep(0.1)

            for _ in range(int(page_delay * 10)):
                if stop_event.is_set(): break
                time.sleep(0.1)

        if stop_event.is_set():
            stop_event.clear()


threading.Thread(target=playlist_loop, daemon=True).start()


# ============================================================
#  FLASK ROUTES
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/current_state')
def current_state():
    return jsonify(is_homed=is_homed, state=current_display_string, active_app=active_app,
                   active_app_playlist=active_app_playlist is not None,
                   app_playlist_name=app_playlist_name,
                   rows=get_rows(), cols=get_cols(), sim_mode=sim_mode, hardware_connected=ser is not None)

@app.route('/grid_config')
def grid_config():
    return jsonify(rows=get_rows(), cols=get_cols(), total=get_module_count(), sim_mode=sim_mode)

@app.route('/toggle_sim', methods=['POST'])
def toggle_sim():
    global sim_mode
    sim_mode = request.json.get('enabled', True)
    return jsonify(sim_mode=sim_mode)

@app.route('/settings', methods=['GET', 'POST'])
def handle_settings():
    global settings, is_homed, current_indices, current_display_string
    if request.method == 'POST':
        data   = request.json
        action = data.get('action')
        mod_id = str(data.get('id', '0'))

        if action == 'save_global':
            # Save any key except internal/protected ones
            protected = {'action', 'id', 'offsets', 'calibrations', 'tuned_chars', 'installed_apps', 'saved_playlists', 'saved_app_playlists'}
            for k, v in data.items():
                if k not in protected:
                    settings[k] = v
            if 'sim_rows' in data or 'sim_cols' in data:
                resize_grid()
            save_settings(settings)
            return jsonify(status="Saved")

        if action == 'adjust':
            delta      = int(data.get('delta', 0))
            new_offset = int(settings['offsets'].get(mod_id, 2832)) + delta
            settings['offsets'][mod_id] = new_offset
            save_settings(settings)
            send_raw(f"m{int(mod_id):02d}o{new_offset}")
            return jsonify(new_offset=new_offset)

        if action == 'home_one':
            send_raw(f"m{int(mod_id):02d}h")
            current_indices[int(mod_id)] = 0
            sl = list(current_display_string.ljust(get_module_count()))
            sl[int(mod_id)] = ' '
            current_display_string = "".join(sl)
            return jsonify(status="Homing")

        if action == 'calibrate':
            with serial_lock:
                if ser:
                    ser.reset_input_buffer()
                    ser.write(f"m{int(mod_id):02d}c\n".encode())
                    ser.flush()
                    start_wait = time.time()
                    buffer = ""
                    target = f"m{int(mod_id):02d}:"
                    while (time.time() - start_wait) < 45.0:
                        if ser.in_waiting > 0:
                            chunk = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                            buffer += chunk
                            if target in buffer and '\n' in buffer[buffer.find(target):]:
                                valid_part = buffer[buffer.find(target):].split('\n')[0]
                                try:
                                    val = int(valid_part.split(target)[1])
                                    settings['calibrations'][mod_id] = val
                                    save_settings(settings)
                                    ser.write(f"m{int(mod_id):02d}t{val}\n".encode())
                                    ser.flush()
                                    return jsonify(status="success", steps=val)
                                except:
                                    pass
                        time.sleep(0.1)
                    return jsonify(status="error", message="Timeout"), 500
    return jsonify(settings)

@app.route('/custom_tune', methods=['POST'])
def custom_tune():
    global current_indices, current_display_string
    data   = request.json
    action = data.get('action')
    mod_id = int(data.get('id', 0))

    if action == 'goto':
        step = int(data.get('step', 0))
        idx  = int(data.get('index', 0))
        send_raw(f"m{mod_id:02d}g{step}")
        if 0 <= idx < len(FLAP_CHARS):
            current_indices[mod_id] = idx
            sl = list(current_display_string.ljust(get_module_count()))
            sl[mod_id] = FLAP_CHARS[idx]
            current_display_string = "".join(sl)

    elif action == 'save':
        idx  = int(data.get('index', 0))
        step = int(data.get('step', 0))
        send_raw(f"m{mod_id:02d}w{idx}:{step}")
        settings['tuned_chars'][str(mod_id)][str(idx)] = step
        save_settings(settings)

    elif action == 'erase':
        idx = str(data.get('index', ''))
        if idx:
            send_raw(f"m{mod_id:02d}w{idx}:65535")
            settings['tuned_chars'][str(mod_id)].pop(idx, None)
        else:
            send_raw(f"m{mod_id:02d}e")
            settings['tuned_chars'][str(mod_id)] = {}
        save_settings(settings)

    return jsonify(status="Success")

@app.route('/sync_module', methods=['POST'])
def sync_module():
    mod_id  = int(request.json.get('id', 0))
    success = sync_hardware_data(mod_id)
    return jsonify(status="success" if success else "failed", settings=settings)

@app.route('/sync_all', methods=['POST'])
def sync_all():
    for i in range(get_module_count()):
        sync_hardware_data(i)
    return jsonify(status="success", settings=settings)

@app.route('/assign_id', methods=['POST'])
def assign_id():
    send_raw(f"m**i{int(request.json.get('id', 0)):02d}")
    return jsonify(status="ID Assigned")

@app.route('/toggle_autohome', methods=['POST'])
def toggle_autohome():
    global settings
    enabled = request.json.get('enabled', True)
    settings['auto_home'] = enabled
    save_settings(settings)
    send_raw(f"m**a{1 if enabled else 0}")
    return jsonify(status="Auto-home updated")

@app.route('/update_playlist', methods=['POST'])
def update_playlist():
    global current_playlist, loop_delay, last_sent_page, active_app, active_app_playlist
    data             = request.json
    current_playlist = data.get('pages', [])
    loop_delay       = data.get('delay', 5)
    last_sent_page   = None
    active_app       = None
    active_app_playlist = None
    stop_event.set()
    mqtt_publish_state()
    return jsonify(status="success")

@app.route('/run_app', methods=['POST'])
def run_app():
    global active_app, loop_delay, active_app_playlist
    active_app_playlist = None
    active_app   = request.json.get('app')

    # Resolve plugin_ prefix
    registry_key = active_app[7:] if active_app and active_app.startswith('plugin_') else active_app

    # Use loop_delay from user settings, then manifest, then global default
    if registry_key in _plugin_registry:
        manifest = _plugin_registry[registry_key]
        if manifest.get('animation'):
            loop_delay = max(0.1, float(settings.get('anim_speed', '0.4')))
        else:
            saved = settings.get(f'plugin_{registry_key}_loop_delay', '')
            default = float(manifest.get('loop_delay', settings.get('global_loop_delay', 5)))
            loop_delay = float(saved) if saved else default
    else:
        loop_delay = float(settings.get('global_loop_delay', 5))

    stop_event.set()
    mqtt_publish_state()
    return jsonify(status=f"App {active_app} started")

@app.route('/stop_app', methods=['POST'])
def stop_app():
    global active_app, active_app_playlist
    active_app = None
    active_app_playlist = None
    stop_event.set()
    mqtt_publish_state()
    return jsonify(status="stopped")

@app.route('/home_all')
def home_all():
    global is_homed, current_indices, current_display_string
    send_raw("m**h")
    is_homed = True
    current_indices = [0] * get_module_count()
    current_display_string = " " * get_module_count()
    return jsonify(status="Homing All")


# ============================================================
#  AUTO FINE-TUNE
# ============================================================

@app.route('/auto_tune', methods=['POST'])
def auto_tune_route():
    global is_homed, current_indices, current_display_string
    data   = request.json
    action = data.get('action')

    if action == 'home':
        send_raw("m**h")
        is_homed = True
        current_indices = [0] * get_module_count()
        current_display_string = " " * get_module_count()
        return jsonify(status="ok")

    elif action == 'goto_char':
        char_idx = int(data.get('char_index', 0))
        if 0 <= char_idx < len(FLAP_CHARS):
            ch = FLAP_CHARS[char_idx]
            # Build 45-char string of the same character and send raw
            # (raw=True so lowercase colour chars are not uppercased)
            text = ch * get_module_count()
            send_to_display(text, raw=True)
            return jsonify(status="ok", char=ch, index=char_idx)
        return jsonify(status="error", message="Invalid index"), 400

    elif action == 'adjust':
        modules   = data.get('modules', [])
        char_idx  = int(data.get('char_index', 0))
        delta     = int(data.get('delta', 0))
        adjusted  = []

        for mod_id in modules:
            mod_str = str(mod_id)
            cal     = int(settings['calibrations'].get(mod_str, 4096))
            expected = (char_idx * cal) // 64

            # Current value: tuned if available, else expected
            tuned_val = settings['tuned_chars'].get(mod_str, {}).get(str(char_idx))
            base = int(tuned_val) if tuned_val is not None else expected
            new_val = base + delta

            # Clamp to valid range
            if new_val < 0:
                new_val = 0
            if new_val >= cal:
                new_val = cal - 1

            # Update settings
            if mod_str not in settings['tuned_chars']:
                settings['tuned_chars'][mod_str] = {}
            settings['tuned_chars'][mod_str][str(char_idx)] = new_val

            # Write to firmware EEPROM
            send_raw(f"m{mod_id:02d}w{char_idx}:{new_val}")

            adjusted.append({'module': mod_id, 'old': base, 'new': new_val})

        save_settings(settings)
        return jsonify(status="ok", adjusted=adjusted)

    elif action == 'get_positions':
        char_idx = int(data.get('char_index', 0))
        positions = {}
        for i in range(get_module_count()):
            mod_str  = str(i)
            cal      = int(settings['calibrations'].get(mod_str, 4096))
            expected = (char_idx * cal) // 64
            tuned    = settings['tuned_chars'].get(mod_str, {}).get(str(char_idx))
            positions[mod_str] = {
                'expected': expected,
                'tuned':    int(tuned) if tuned is not None else None,
                'active':   int(tuned) if tuned is not None else expected,
            }
        return jsonify(positions=positions)

    return jsonify(status="error", message="Unknown action"), 400


@app.route('/tuning_status')
def tuning_status():
    char_idx = int(request.args.get('char_index', 0))
    if char_idx < 0 or char_idx >= len(FLAP_CHARS):
        return jsonify(status="error", message="Invalid char_index"), 400
    positions = {}
    for i in range(get_module_count()):
        mod_str = str(i)
        cal = int(settings['calibrations'].get(mod_str, 4096))
        expected = (char_idx * cal) // 64
        tuned = settings['tuned_chars'].get(mod_str, {}).get(str(char_idx))
        positions[mod_str] = {
            'expected': expected,
            'tuned': int(tuned) if tuned is not None else None,
            'active': int(tuned) if tuned is not None else expected,
        }
    return jsonify(
        char_index=char_idx,
        char=FLAP_CHARS[char_idx],
        flap_chars=FLAP_CHARS,
        grid={'rows': get_rows(), 'cols': get_cols(), 'total': get_module_count()},
        positions=positions,
    )


# ── Backup / Restore ─────────────────────────────────────────

@app.route('/backup_settings')
def backup_settings():
    return jsonify({
        'version':      1,
        'created':      datetime.now().isoformat(),
        'offsets':      settings['offsets'],
        'calibrations': settings['calibrations'],
        'tuned_chars':  settings['tuned_chars'],
    })

@app.route('/restore_settings', methods=['POST'])
def restore_settings():
    data = request.json
    if not data:
        return jsonify(status="error", message="No data"), 400
    if 'offsets'      in data: settings['offsets'].update(data['offsets'])
    if 'calibrations' in data: settings['calibrations'].update(data['calibrations'])
    if 'tuned_chars'  in data: settings['tuned_chars'].update(data['tuned_chars'])
    save_settings(settings)
    hw = False
    if ser:
        hw = True
        for i in range(get_module_count()):
            s = str(i)
            send_raw(f"m{i:02d}o{int(settings['offsets'].get(s, 2832))}")
            send_raw(f"m{i:02d}t{int(settings['calibrations'].get(s, 4096))}")
            send_raw(f"m{i:02d}e")
            for idx, step in settings['tuned_chars'].get(s, {}).items():
                sv = int(step)
                if sv != 65535:
                    send_raw(f"m{i:02d}w{idx}:{sv}")
            logging.info(f"Restored m{i:02d}")
    return jsonify(status="success", hardware_updated=hw, modules_updated=45)

# ── Saved Playlists ──────────────────────────────────────────

@app.route('/playlists', methods=['GET', 'POST'])
def playlists():
    if request.method == 'GET':
        return jsonify(settings.get('saved_playlists', {}))
    data = request.json
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify(status="error", message="Name required"), 400
    if 'saved_playlists' not in settings:
        settings['saved_playlists'] = {}
    settings['saved_playlists'][name] = {
        'pages': data.get('pages', []),
        'delay': data.get('delay', 5),
    }
    save_settings(settings)
    return jsonify(status="saved", name=name)

@app.route('/playlists/<path:name>', methods=['DELETE'])
def delete_playlist(name):
    plists = settings.get('saved_playlists', {})
    if name in plists:
        del plists[name]
        settings['saved_playlists'] = plists
        save_settings(settings)
    return jsonify(status="deleted")


# ============================================================
#  APP PLAYLISTS
# ============================================================

@app.route('/run_app_playlist', methods=['POST'])
def run_app_playlist():
    global active_app_playlist, app_playlist_loop, active_app, current_playlist, last_sent_page, app_playlist_name
    data = request.json
    active_app_playlist = data.get('entries', [])
    app_playlist_loop = data.get('loop', True)
    app_playlist_name = data.get('name', None)
    active_app = None
    current_playlist = []
    last_sent_page = None
    stop_event.set()
    mqtt_publish_state()
    return jsonify(status="App playlist started")

@app.route('/app_playlists', methods=['GET', 'POST'])
def app_playlists():
    if request.method == 'GET':
        return jsonify(settings.get('saved_app_playlists', {}))
    data = request.json
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify(status="error", message="Name required"), 400
    if 'saved_app_playlists' not in settings:
        settings['saved_app_playlists'] = {}
    settings['saved_app_playlists'][name] = {
        'entries': data.get('entries', []),
        'loop': data.get('loop', True),
    }
    save_settings(settings)
    mqtt_publish_discovery()
    return jsonify(status="saved", name=name)

@app.route('/app_playlists/<path:name>', methods=['DELETE'])
def delete_app_playlist(name):
    plists = settings.get('saved_app_playlists', {})
    if name in plists:
        del plists[name]
        settings['saved_app_playlists'] = plists
        save_settings(settings)
    mqtt_publish_discovery()
    return jsonify(status="deleted")


# ============================================================
#  APP LIBRARY API
# ============================================================

@app.route('/app_library')
def app_library():
    """List all apps in the apps/ directory with installed status."""
    apps = []
    if os.path.isdir(APPS_PATH):
        for app_id in os.listdir(APPS_PATH):
            manifest_path = os.path.join(APPS_PATH, app_id, 'manifest.json')
            if not os.path.isfile(manifest_path):
                continue
            try:
                with open(manifest_path, encoding='utf-8') as f:
                    m = json.load(f)
                m['id'] = app_id
                m['installed'] = app_id in _plugin_registry
                apps.append(m)
            except Exception:
                pass
    apps.sort(key=lambda a: a.get('name', '').lower())
    return jsonify({"version": 1, "apps": apps})


@app.route('/app_library/install', methods=['POST'])
def app_library_install():
    global active_app
    app_id = request.json.get("id", "").strip()
    if not app_id:
        return jsonify(status="error", message="No app ID"), 400
    if app_id in _plugin_registry:
        return jsonify(status="error", message="Already installed"), 409

    app_dir = os.path.join(APPS_PATH, app_id)
    if not os.path.isdir(app_dir):
        # Download from remote if not local
        base_url = settings.get('app_library_url', 'https://raw.githubusercontent.com/csader/splitflap-os/main/apps')
        try:
            os.makedirs(app_dir, exist_ok=True)
            manifest_url = f"{base_url}/{app_id}/manifest.json"
            req = urllib.request.Request(manifest_url, headers={"User-Agent": "SplitFlap/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                manifest_bytes = resp.read()
            with open(os.path.join(app_dir, "manifest.json"), "wb") as f:
                f.write(manifest_bytes)

            manifest = json.loads(manifest_bytes.decode())
            app_type = manifest.get("type", "channel")

            if app_type == "channel":
                data_url = f"{base_url}/{app_id}/data.json"
                req = urllib.request.Request(data_url, headers={"User-Agent": "SplitFlap/1.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    with open(os.path.join(app_dir, "data.json"), "wb") as f:
                        f.write(resp.read())
            elif app_type == "functional":
                code_url = f"{base_url}/{app_id}/app.py"
                req = urllib.request.Request(code_url, headers={"User-Agent": "SplitFlap/1.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    with open(os.path.join(app_dir, "app.py"), "wb") as f:
                        f.write(resp.read())
        except Exception as e:
            if os.path.isdir(app_dir):
                shutil.rmtree(app_dir, ignore_errors=True)
            logging.error(f"Install error for {app_id}: {e}")
            return jsonify(status="error", message=str(e)), 500

    # Add to installed_apps list
    installed = settings.get('installed_apps', [])
    if app_id not in installed:
        installed.append(app_id)
        settings['installed_apps'] = installed
        save_settings(settings)

    load_installed_plugins()
    _registry_cache['fetched_at'] = 0
    mqtt_publish_discovery()
    return jsonify(status="success", id=app_id)


@app.route('/app_library/uninstall', methods=['POST'])
def app_library_uninstall():
    global active_app
    app_id = request.json.get("id", "").strip()
    if not app_id:
        return jsonify(status="error", message="No app ID"), 400
    if active_app in (app_id, f"plugin_{app_id}"):
        active_app = None
        stop_event.set()
    # Remove from installed_apps list (keep files)
    installed = settings.get('installed_apps', [])
    if app_id in installed:
        installed.remove(app_id)
        settings['installed_apps'] = installed
        save_settings(settings)
    load_installed_plugins()
    _registry_cache['fetched_at'] = 0
    mqtt_publish_discovery()
    return jsonify(status="success", id=app_id)


_teams_cache = {}

@app.route('/sports_leagues')
def sports_leagues_route():
    """Return league list with current follow settings."""
    leagues = []
    for key, info in SPORTS_LEAGUES.items():
        followed = settings.get(f'sports_{key}', '').strip()
        leagues.append({'key': key, 'name': info['name'], 'path': info['path'],
                        'followed': followed, 'follow_all': followed == '*'})
    return jsonify(leagues=leagues)

@app.route('/sports_teams/<league_key>')
def sports_teams_route(league_key):
    """Search teams for a league. Use ?q= for search, otherwise return all (cached)."""
    info = SPORTS_LEAGUES.get(league_key)
    if not info:
        return jsonify(teams=[], error='Unknown league'), 404
    if league_key in ('pga', 'ufc'):
        return jsonify(teams=[], no_teams=True)
    query = request.args.get('q', '').strip().lower()
    # WSOC has no teams endpoint — reuse MSOC list (same schools)
    fetch_key = 'msoc' if league_key == 'wsoc' else league_key
    fetch_path = SPORTS_LEAGUES[fetch_key]['path']
    # Fetch and cache full list
    if league_key not in _teams_cache:
        try:
            all_teams = []
            for page in range(1, 4):
                url = f"https://site.api.espn.com/apis/site/v2/sports/{fetch_path}/teams?limit=200&page={page}"
                data = requests.get(url, timeout=8).json()
                batch = data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', [])
                if not batch:
                    break
                for entry in batch:
                    t = entry.get('team', entry)
                    all_teams.append({'abbr': t.get('abbreviation', '?'), 'name': t.get('displayName', '?'),
                                      'short': t.get('shortDisplayName', t.get('displayName', '?'))})
            all_teams.sort(key=lambda t: t['name'])
            # Deduplicate by abbreviation
            seen = set()
            all_teams = [t for t in all_teams if t['abbr'] not in seen and not seen.add(t['abbr'])]
            _teams_cache[league_key] = all_teams
        except Exception as e:
            return jsonify(teams=[], error=str(e)), 502
    teams = _teams_cache[league_key]
    if query:
        teams = [t for t in teams if query in t['name'].lower() or query in t['abbr'].lower()]
    return jsonify(teams=teams)

@app.route('/sports_follow', methods=['POST'])
def sports_follow():
    """Save followed teams for a league."""
    data = request.json
    league = data.get('league', '')
    teams = data.get('teams', '')  # comma-sep abbreviations or '*'
    if league not in SPORTS_LEAGUES:
        return jsonify(status='error', message='Unknown league'), 400
    settings[f'sports_{league}'] = teams
    save_settings(settings)
    return jsonify(status='success')

# ============================================================
#  SEARCH ENDPOINTS (timezone, stocks, crypto)
# ============================================================

@app.route('/timezones')
def timezones_route():
    """Search timezones with common ones first."""
    query = request.args.get('q', '').strip().lower()
    common = ['US/Eastern','US/Central','US/Mountain','US/Pacific','US/Hawaii',
              'Europe/London','Europe/Paris','Europe/Berlin','Asia/Tokyo','Asia/Shanghai',
              'Australia/Sydney','Pacific/Auckland','America/Chicago','America/Denver',
              'America/Los_Angeles','America/New_York','America/Toronto','America/Sao_Paulo']
    all_zones = pytz.common_timezones
    results = []
    seen = set()
    def add_zone(tz):
        if tz in seen: return
        seen.add(tz)
        try:
            offset = datetime.now(pytz.timezone(tz)).strftime('%z')
            label = f"{tz} (UTC{offset[:3]}:{offset[3:]})"
        except Exception:
            label = tz
        results.append({'value': tz, 'label': label})
    if not query:
        for tz in common: add_zone(tz)
    else:
        for tz in common:
            if query in tz.lower(): add_zone(tz)
        for tz in all_zones:
            if query in tz.lower(): add_zone(tz)
    return jsonify(zones=results[:20])

@app.route('/stocks_search')
def stocks_search_route():
    """Search stock tickers via Yahoo Finance autocomplete."""
    query = request.args.get('q', '').strip()
    if len(query) < 1:
        return jsonify(tickers=[])
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=8&newsCount=0&enableFuzzyQuery=false&quotesQueryId=tss_match_phrase_query"
        data = requests.get(url, timeout=5, headers={'User-Agent':'Mozilla/5.0'}).json()
        tickers = []
        for q in data.get('quotes', []):
            sym = q.get('symbol', '')
            name = q.get('shortname') or q.get('longname') or ''
            if sym:
                tickers.append({'value': sym, 'label': f"{sym} — {name}" if name else sym})
        return jsonify(tickers=tickers)
    except Exception as e:
        logging.error(f"Stock search error: {e}")
        return jsonify(tickers=[], error=str(e)), 502

_crypto_cache = []

@app.route('/crypto_search')
def crypto_search_route():
    """Search CoinGecko coins (cached)."""
    global _crypto_cache
    query = request.args.get('q', '').strip().lower()
    if len(query) < 1:
        return jsonify(coins=[])
    if not _crypto_cache:
        try:
            data = requests.get('https://api.coingecko.com/api/v3/coins/list', timeout=10).json()
            _crypto_cache = [{'id': c['id'], 'symbol': c['symbol'].upper(), 'name': c['name']} for c in data]
        except Exception as e:
            logging.error(f"CoinGecko fetch error: {e}")
            return jsonify(coins=[], error=str(e)), 502
    results = []
    for c in _crypto_cache:
        if query in c['name'].lower() or query in c['symbol'].lower() or query in c['id']:
            results.append({'value': c['id'], 'label': f"{c['name']} ({c['symbol']})",
                            '_exact': c['id']==query or c['name'].lower()==query or c['symbol'].lower()==query})
            if len(results) >= 30: break
    results.sort(key=lambda r: (not r['_exact'], r['label'].lower()))
    for r in results: del r['_exact']
    return jsonify(coins=results[:12])

# ============================================================
#  NETWORK STATUS
# ============================================================

_network_mode = 'unknown'
_is_online = False

def _check_network():
    """Detect network mode and internet connectivity."""
    global _network_mode, _is_online
    # Check mode file written by network-check.sh
    try:
        with open('/tmp/splitflap-network-mode', 'r') as f:
            _network_mode = f.read().strip()
    except FileNotFoundError:
        _network_mode = 'wifi'  # assume normal if no file (dev mode)

    # Check internet connectivity
    try:
        requests.get('https://httpbin.org/status/200', timeout=3)
        _is_online = True
    except Exception:
        _is_online = False

    # Publish network state via MQTT
    _mqtt_publish_network()

def check_online():
    """Return cached online status. Refreshed periodically."""
    return _is_online


def _mqtt_publish_network():
    """Publish network status to MQTT."""
    if not mqtt_client or not mqtt_client.is_connected():
        return
    import subprocess
    ip = '?'
    ssid = '?'
    try:
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=2)
        ip = result.stdout.strip().split()[0] if result.stdout.strip() else '?'
    except Exception:
        pass
    try:
        result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True, timeout=2)
        ssid = result.stdout.strip() or ('SplitflapOS' if _network_mode == 'hotspot' else '?')
    except Exception:
        if _network_mode == 'hotspot':
            ssid = settings.get('hotspot_ssid', 'SplitflapOS')
    mqtt_client.publish(f"{MQTT_TOPIC_PREFIX}/network/mode", _network_mode, retain=True)
    mqtt_client.publish(f"{MQTT_TOPIC_PREFIX}/network/ssid", ssid, retain=True)
    mqtt_client.publish(f"{MQTT_TOPIC_PREFIX}/network/ip", ip, retain=True)
    mqtt_client.publish(f"{MQTT_TOPIC_PREFIX}/network/online", "ON" if _is_online else "OFF", retain=True)


# Initial check on startup
threading.Thread(target=_check_network, daemon=True).start()

# Periodic connectivity check every 60s
def _periodic_network_check():
    while True:
        time.sleep(60)
        _check_network()

threading.Thread(target=_periodic_network_check, daemon=True).start()


@app.route('/mqtt_reconnect', methods=['POST'])
def mqtt_reconnect_route():
    """Reconnect MQTT with current settings."""
    mqtt_reconnect()
    return jsonify(status="reconnecting")


@app.route('/network_status')
def network_status():
    """Return current network mode and connectivity."""
    import subprocess
    ip = '?'
    ssid = '?'
    try:
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=2)
        ip = result.stdout.strip().split()[0] if result.stdout.strip() else '?'
    except Exception:
        pass
    try:
        result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True, timeout=2)
        ssid = result.stdout.strip() or ('SplitflapOS' if _network_mode == 'hotspot' else '?')
    except Exception:
        if _network_mode == 'hotspot':
            ssid = settings.get('hotspot_ssid', 'SplitflapOS')
    return jsonify(mode=_network_mode, online=_is_online, ip=ip, ssid=ssid)

@app.route('/network_config', methods=['POST'])
def network_config():
    """Save hotspot configuration."""
    data = request.json
    if data.get('hotspot_ssid'):
        settings['hotspot_ssid'] = data['hotspot_ssid']
    if data.get('hotspot_password'):
        settings['hotspot_password'] = data['hotspot_password']
    save_settings(settings)
    # Update systemd service environment
    service_path = '/etc/systemd/system/splitflap-network.service'
    if os.path.isfile(service_path):
        try:
            with open(service_path, 'r') as f:
                lines = f.readlines()
            with open(service_path, 'w') as f:
                for line in lines:
                    if line.startswith('Environment=SPLITFLAP_HOTSPOT_SSID='):
                        f.write(f"Environment=SPLITFLAP_HOTSPOT_SSID={settings['hotspot_ssid']}\n")
                    elif line.startswith('Environment=SPLITFLAP_HOTSPOT_PASS='):
                        f.write(f"Environment=SPLITFLAP_HOTSPOT_PASS={settings['hotspot_password']}\n")
                    else:
                        f.write(line)
            os.system('systemctl daemon-reload')
        except Exception as e:
            logging.error(f"Failed to update network service: {e}")
    return jsonify(status="saved")

@app.route('/wifi_scan')
def wifi_scan():
    """Scan for available WiFi networks."""
    import subprocess
    try:
        result = subprocess.run(
            ['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'dev', 'wifi', 'list', '--rescan', 'yes'],
            capture_output=True, text=True, timeout=15)
        networks = []
        seen = set()
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split(':')
            ssid = parts[0] if parts else ''
            if not ssid or ssid in seen:
                continue
            seen.add(ssid)
            signal = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            security = parts[2] if len(parts) > 2 else ''
            networks.append({'ssid': ssid, 'signal': signal, 'security': security})
        networks.sort(key=lambda n: -n['signal'])
        return jsonify(networks=networks)
    except Exception as e:
        logging.error(f"WiFi scan error: {e}")
        return jsonify(networks=[], error=str(e))

@app.route('/wifi_connect', methods=['POST'])
def wifi_connect():
    """Connect to a WiFi network via NetworkManager."""
    import subprocess
    data = request.json
    ssid = data.get('ssid', '').strip()
    password = data.get('password', '').strip()
    if not ssid:
        return jsonify(status="error", message="SSID required"), 400
    try:
        # Remove existing connection with same name if any
        subprocess.run(['nmcli', 'con', 'delete', ssid], capture_output=True, timeout=5)
        # Connect
        cmd = ['nmcli', 'dev', 'wifi', 'connect', ssid]
        if password:
            cmd += ['password', password]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return jsonify(status="success", message=f"Connected to {ssid}")
        else:
            return jsonify(status="error", message=result.stderr.strip() or "Connection failed"), 400
    except Exception as e:
        return jsonify(status="error", message=str(e)), 500


@app.route('/installed_apps')
def installed_apps():
    return jsonify(
        apps=get_plugin_app_list(),
        settings_config=get_plugin_settings_config(),
    )


# ============================================================
#  UPDATE CHECK
# ============================================================

_update_cache = {'checked_at': 0, 'result': None}

@app.route('/version')
def version_route():
    return jsonify(version=_read_version())

@app.route('/check_update')
def check_update():
    now = time.time()
    force = request.args.get('force') == '1'
    if not force and _update_cache['result'] and (now - _update_cache['checked_at']) < 3600:
        return jsonify(_update_cache['result'])
    try:
        repo_url = 'https://api.github.com/repos/csader/splitflap-os/releases/latest'
        resp = requests.get(repo_url, timeout=5, headers={'User-Agent': 'SplitflapOS'})
        resp.raise_for_status()
        data = resp.json()
        latest = data.get('tag_name', '').lstrip('v')
        current = _read_version()
        has_update = latest and latest != current
        result = {
            'current': current,
            'latest': latest,
            'has_update': has_update,
            'release_name': data.get('name', ''),
            'release_url': data.get('html_url', ''),
        }
        _update_cache['result'] = result
        _update_cache['checked_at'] = now
        return jsonify(result)
    except Exception as e:
        logging.error(f"Update check error: {e}")
        return jsonify({'current': _read_version(), 'latest': None, 'has_update': False, 'error': str(e)})

@app.route('/apply_update', methods=['POST'])
def apply_update():
    """Pull latest from main and restart the service."""
    import subprocess
    repo_dir = os.path.join(os.path.dirname(__file__), '..')
    try:
        subprocess.run(['git', 'pull', 'origin', 'main'], cwd=repo_dir, timeout=60, check=True)
        _update_cache['checked_at'] = 0  # invalidate cache
        # Restart via systemd if available, otherwise just reload
        def _restart():
            time.sleep(1)
            try:
                subprocess.run(['systemctl', 'restart', 'splitflap.service'], timeout=10)
            except Exception:
                os.execv('/usr/bin/python3', ['/usr/bin/python3'] + os.sys.argv)
        threading.Thread(target=_restart, daemon=True).start()
        return jsonify(status='updating')
    except Exception as e:
        logging.error(f"Update error: {e}")
        return jsonify(status='error', message=str(e)), 500


if __name__ == '__main__':
    logging.info("Web UI running on 0.0.0.0:80")
    app.run(host='0.0.0.0', port=80)