# Split-Flap OS

A web-based control interface for modular split-flap displays. Manage apps, compose messages, and calibrate hardware from any device.

Built on [Adam G Makes' Split-Flap Display](https://github.com/adamgmakes/SplitFlapDisplay) hardware platform.

## Features

- **App system** — installable/removable apps (weather, stocks, sports, crypto, countdown, animations, and more)
- **Compose** — click-to-type grid editor with color tile support
- **Live preview** — animated flap simulation in the browser
- **Calibration tools** — hardware inspector, auto fine-tune, teach mode
- **MQTT** — Home Assistant integration
- **Plugin architecture** — community apps via manifest + fetch pattern
- **Mobile-friendly** — hamburger menu, sticky bottom tabs, responsive layout

## Quick Start

```bash
cd server
pip install -r requirements.txt
python app.py
```

Open `http://<your-pi-ip>` in a browser. On first launch, install apps from ☰ → App Library.

## Hardware

This project is the **software only**. For the physical display (3D printed parts, PCBs, firmware, BOM), see the original project:

- **Build video:** https://www.youtube.com/watch?v=-C8_AtxEEQc
- **Hardware repo:** https://github.com/adamgmakes/SplitFlapDisplay
- **OnShape model:** https://cad.onshape.com/documents/87c916b33ca5d6492b457485

## Repo Structure

```
server/          — Flask web app (backend + frontend)
apps/            — Plugin library (all installable apps)
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

## Attribution

Based on the [Split-Flap Display](https://github.com/adamgmakes/SplitFlapDisplay) by **Adam G Makes**, licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

## License

[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

You are free to share and adapt this project for non-commercial purposes, as long as you give appropriate credit and distribute derivatives under the same license.
