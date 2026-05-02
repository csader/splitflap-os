# Split-Flap OS

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
- **Plugin architecture** — community apps via manifest + fetch pattern
- **Mobile-friendly** — hamburger menu, sticky bottom tabs, responsive layout


<img width="250" alt="Apps" src="https://github.com/user-attachments/assets/002634e8-00d5-48ae-97a3-5d3ee3ee0ad4" />  <img width="250" alt="Compose" src="https://github.com/user-attachments/assets/13aa01ed-aaa7-48e3-8c95-bbb158ab4fe4" />  <img width="250" alt="Playlists" src="https://github.com/user-attachments/assets/463dc2ca-ffff-4560-a4f0-7409b86f03e4" /> 

<img width="800" alt="Desktop" src="https://github.com/user-attachments/assets/5d67f2aa-ea38-4db9-a7fd-6181e8535f1b" />


## Quick Start

On your Split-Flap Display's Raspberry Pi:

```bash
git clone https://github.com/csader/splitflap-os.git
cd splitflap-os/server
pip install -r requirements.txt
sudo python app.py
```

Open `http://<your-pi-ip>` on any device on the same network. On first launch, install apps from ☰ → App Library.

## Hardware

This project is the **web UI only**. For the firmware and physical display hardware (3D printed parts, PCBs, BOM), see the original project by Adam G Makes:

**https://github.com/adamgmakes/SplitFlapDisplay**

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

## Attribution

Based on the [Split-Flap Display](https://github.com/adamgmakes/SplitFlapDisplay) by **Adam G Makes**, licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

## License

[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

You are free to share and adapt this project for non-commercial purposes, as long as you give appropriate credit and distribute derivatives under the same license.
