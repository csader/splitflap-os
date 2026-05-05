# SplitFlap OS

A web-based control interface for modular split-flap displays. Manage apps, compose messages, and calibrate hardware from any device.

Built on [Adam G Makes' Split-Flap Display](https://github.com/adamgmakes/SplitFlapDisplay) hardware platform.

## Features

- **40+ apps** — weather, stocks, sports scores, crypto, word clock, trivia, news headlines, quotes, and more
- **App Library** — browse and install apps by category (time, entertainment, news, lifestyle, education, finance, sports)
- **Compose** — click-to-type grid editor with color tile support
- **Playlists** — sequence apps and composed messages with per-entry timing and transitions
- **Live preview** — animated flap simulation in the browser
- **Calibration tools** — hardware inspector, auto fine-tune, teach mode
- **MQTT** — Home Assistant integration with auto-discovery
- **WiFi hotspot fallback** — Pi creates its own network when no WiFi is found, so you can always access the UI
- **Offline resilience** — internet-dependent apps degrade gracefully, offline apps keep running
- **Plugin architecture** — community apps via manifest + fetch pattern
- **Mobile-friendly** — hamburger menu, sticky bottom tabs, responsive layout


<img width="250" alt="Apps" src="https://github.com/user-attachments/assets/002634e8-00d5-48ae-97a3-5d3ee3ee0ad4" />  <img width="250" alt="Compose" src="https://github.com/user-attachments/assets/13aa01ed-aaa7-48e3-8c95-bbb158ab4fe4" />  <img width="250" alt="Playlists" src="https://github.com/user-attachments/assets/463dc2ca-ffff-4560-a4f0-7409b86f03e4" /> 

<img width="800" alt="Desktop" src="https://github.com/user-attachments/assets/5d67f2aa-ea38-4db9-a7fd-6181e8535f1b" />


## Quick Start

On your Split-Flap Display's Raspberry Pi:

```bash
git clone https://github.com/csader/splitflap-os.git
cd splitflap-os
sudo bash setup/install.sh
```

The installer sets up auto-start, WiFi hotspot fallback, and all dependencies. Access the UI at `http://<your-pi-ip>`.

If no WiFi is available, the Pi creates a hotspot:
- SSID: `SplitflapOS`
- Password: `splitflap`
- UI: `http://192.168.4.1`

Configure WiFi from Settings > WiFi / Network in the UI.

## Hardware

This project is the **web UI only**. For the firmware and physical display hardware (3D printed parts, PCBs, BOM), see the original project by Adam G Makes:

**https://github.com/adamgmakes/SplitFlapDisplay**

## Repo Structure

```
server/          — Flask web app (backend + frontend)
apps/            — Plugin library (all installable apps)
setup/           — Raspberry Pi setup scripts and systemd services
```

## Creating an App

Each app is a directory in `apps/` with two files:

**manifest.json**
```json
{
  "id": "my-app",
  "name": "My App",
  "icon": "🎯",
  "description": "What it does",
  "category": "entertainment",
  "type": "functional",
  "refresh_interval": 60,
  "loop_delay": 5,
  "settings": []
}
```

**app.py**
```python
def fetch(settings, format_lines, get_rows, get_cols):
    return [format_lines("LINE 1", "LINE 2", "LINE 3")]
```

`fetch()` returns a list of page strings. Each page is displayed for `loop_delay` seconds. Data is cached for `refresh_interval` seconds.

### App settings field types

`manifest.json` `settings` entries support these input types:

- `text`, `number`, `password`, `datetime-local`, `textarea`
- `select` with `options`
- `search_chips` with `searchUrl`, `resultKey`, and `maxItems`
- `toggle` with `options` (segmented buttons)

For `select`/`toggle`, each option can be either:

- a string: `"MI"`
- or an object: `{ "value": "mi", "label": "MI" }`

For `toggle`, optional sizing:

- `size`: `"sm"`, `"md"` (default), or `"lg"`

### Minimal pattern (recommended)

For most apps, keep settings to this simple structure:

```json
{
  "settings": [
    {
      "key": "units",
      "label": "Units",
      "type": "toggle",
      "default": "imperial",
      "options": [
        { "value": "imperial", "label": "Imperial" },
        { "value": "metric", "label": "Metric" }
      ]
    },
    {
      "key": "refresh_minutes",
      "label": "Refresh Minutes",
      "type": "number",
      "default": 15,
      "min": 1,
      "max": 60
    }
  ]
}
```

Recommended conventions:

- use stable lowercase keys with underscores (`refresh_minutes`)
- always include a `default`
- use object options (`value` + `label`) for toggles/selects
- only add `sync_values` / `sync_parent` when you need dependent fields

### Inline unit toggle next to an input

You can attach a segmented toggle to a text/number field using `inline_toggle`.

Example:

```json
{
  "key": "search_radius",
  "label": "Search Radius",
  "type": "number",
  "default": 100,
  "inline_toggle": {
    "key": "search_radius_unit",
    "options": [
      { "value": "mi", "label": "MI" },
      { "value": "km", "label": "KM" }
    ],
    "default": "mi",
    "position": "after",
    "size": "md"
  }
}
```

`inline_toggle` fields:

- `key` (required): setting key saved alongside the main input
- `options` (required): list of string/object options
- `default` (optional): default selected value
- `position` (optional): `"before"` or `"after"` (default)
- `size` (optional): `"sm"`, `"md"`, or `"lg"`

### Settings sync rules (optional)

You can declaratively sync setting values across fields in `manifest.json`.

- `sync_values` on a source field: maps the field value to one or more target key/value updates.
- `sync_parent` on a child field: identifies a parent key to set when this child is manually changed.
- `sync_parent_custom_value` on a child field: value to set on the parent (default: `"custom"`).

Example:

```json
{
  "key": "units_preset",
  "type": "toggle",
  "options": ["aviation", "metric", "imperial", "custom"],
  "sync_values": {
    "aviation": {"distance_unit": "nm", "altitude_unit": "fl", "speed_unit": "kt"},
    "metric":   {"distance_unit": "km", "altitude_unit": "m",  "speed_unit": "kmh"},
    "imperial": {"distance_unit": "mi", "altitude_unit": "ft", "speed_unit": "mph"}
  }
}
```

```json
{
  "key": "distance_unit",
  "type": "toggle",
  "sync_parent": "units_preset",
  "sync_parent_custom_value": "custom"
}
```

## Attribution

Based on the [Split-Flap Display](https://github.com/adamgmakes/SplitFlapDisplay) by **Adam G Makes**, licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

## License

[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

You are free to share and adapt this project for non-commercial purposes, as long as you give appropriate credit and distribute derivatives under the same license.
