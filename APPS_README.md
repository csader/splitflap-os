# App Development Guide

For high-level project setup, usage, and hardware notes, see [README.md](README.md).

## Build Your First App

Each app lives under `apps/<app-id>/` and typically has two files.

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

How runtime behavior works:

- `fetch()` returns a list of page strings.
- Each page is shown for `loop_delay` seconds.
- Fetch results are cached for `refresh_interval` seconds.

## Define Settings in manifest.json

`manifest.json` `settings` supports these field `type` values:

- `text`, `number`, `password`, `datetime-local`, `textarea`
- `select` with `options`
- `search_chips` with `searchUrl`, `resultKey`, and optional `maxItems`
- `toggle` with `options` (segmented control)
- `computed` with `compute` and `watches` (read-only derived info)

Common optional keys:

- `number`: `min`, `max`, `step`, optional `stepper: true`
- `toggle`: optional `size` (`"sm"`, `"md"`, `"lg"`)
- Any field: `visible_when` for conditional show/hide

For `select` and `toggle`, options can be either:

- string form: `"MI"`
- object form: `{ "value": "mi", "label": "MI" }`

## Recommended Minimal Pattern

Use this structure for most new apps:

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

Conventions:

- Use stable lowercase keys with underscores (example: `refresh_minutes`).
- Always define a `default`.
- Prefer object options (`value` + `label`) for `select` and `toggle`.
- Only add sync rules when dependent behavior is needed.

## Add Optional Setting Features

### Number Stepper Buttons

Add explicit `- / +` controls to a `number` field:

```json
{
  "key": "polling_rate",
  "label": "Polling Rate (seconds)",
  "type": "number",
  "stepper": true,
  "default": 60,
  "min": 15,
  "max": 3600,
  "step": 15
}
```

### Conditional Visibility

Show a field only when other setting values match.

- format: `{ "other_key": "expected_value" }`
- multiple keys are combined with AND logic

```json
{
  "key": "flightaware_api_key",
  "label": "FlightAware API Key",
  "type": "password",
  "default": "",
  "visible_when": { "data_source": "flightaware" }
}
```

### Computed Read-Only Fields

Render live derived text in settings:

- `compute`: compute function name in frontend registry
- `watches`: keys that trigger recomputation

```json
{
  "key": "_polling_stats",
  "label": "API Usage Estimate",
  "type": "computed",
  "compute": "polling_rate_stats",
  "watches": ["polling_rate", "data_source"]
}
```

### Inline Toggle Next to Input

Attach a segmented toggle to a text/number field via `inline_toggle`:

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

`inline_toggle` keys:

- `key` (required): setting key persisted alongside the main input
- `options` (required): string/object option list
- `default` (optional): default selected option
- `position` (optional): `"before"` or `"after"` (default)
- `size` (optional): `"sm"`, `"md"`, or `"lg"`

### Declarative Settings Sync

Use these keys to synchronize related fields:

- `sync_values` on source field: maps source value to updates for target fields
- `sync_parent` on child field: parent key to set when child changes manually
- `sync_parent_custom_value` on child field: parent value to set (default: `"custom"`)

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

## Final Checklist

- Confirm your app directory contains `manifest.json` and `app.py`.
- Ensure every setting has a stable `key` and sensible `default`.
- Use `visible_when` and sync rules only when they improve UX.
- Keep `fetch()` fast and resilient to network/API errors.

---

## App Triggers

Triggers let your app interrupt the display when something worth showing happens — a live game, a rare bird, a weather alert. Users configure triggers in the **Triggers** page and can create multiple triggers from the same app with different conditions.

### How it works

1. You declare a `trigger_conditions` schema in `manifest.json` — the fields a user fills in when creating a trigger from your app.
2. You implement a `trigger(settings, conditions)` function in `app.py` that returns `True` when the condition is met.
3. The OS calls `trigger()` on a background thread at `trigger_interval` seconds. When it returns `True`, the app's pages are fetched and shown as an interrupt.

### manifest.json additions

```json
{
  "trigger_interval": 60,
  "trigger_display_seconds": 30,
  "trigger_cooldown": 300,
  "trigger_conditions": [
    {
      "key": "events",
      "label": "Fire when",
      "type": "toggle",
      "options": [
        {"value": "game_start", "label": "Game starts"},
        {"value": "score_change", "label": "Score changes"},
        {"value": "close_game", "label": "Close game (within 5)"},
        {"value": "final", "label": "Game ends"}
      ],
      "default": "game_start"
    },
    {
      "key": "teams",
      "label": "Specific teams (empty = all followed)",
      "type": "text",
      "default": ""
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `trigger_interval` | How often (seconds) the OS calls `trigger()`. Keep this reasonable — 30–300s for most apps. |
| `trigger_display_seconds` | How long to show the interrupt. Default shown in trigger UI; user can override. |
| `trigger_cooldown` | Minimum seconds between fires for the same trigger. Prevents spam. |
| `trigger_conditions` | Schema for per-trigger condition fields. Same field types as `settings`. |

`trigger_conditions` supports all the same field types as `settings`: `text`, `number`, `toggle`, `select`, `search_chips`, `visible_when`, etc.

### app.py trigger function

```python
def trigger(settings, conditions):
    """
    Called periodically by the OS. Return True to interrupt the display.

    Args:
        settings: dict — full app settings (same as fetch() receives)
        conditions: dict — the user-configured condition values for this trigger

    Returns:
        bool — True to fire, False to skip
    """
    event_type = conditions.get('events', 'game_start')
    teams = conditions.get('teams', '').split(',') if conditions.get('teams') else []
    # ... check your data source ...
    return False
```

The function must be **fast and non-blocking** — it runs on the trigger thread and blocks other trigger checks. If you need to make a network call, cache the result and return quickly.

### State between calls

Use the same `setattr` pattern as `fetch()` to persist state across calls:

```python
def trigger(settings, conditions):
    state = getattr(trigger, '_state', None)
    if state is None:
        state = {'last_seen': set()}
        setattr(trigger, '_state', state)

    # check for new items not in last_seen
    new_items = fetch_new_items(settings)
    fired = bool(new_items - state['last_seen'])
    state['last_seen'] = new_items
    return fired
```

### Example: BirdNET rare species trigger

```json
// manifest.json trigger_conditions
[
  {
    "key": "species_filter",
    "label": "Fire for",
    "type": "toggle",
    "options": [
      {"value": "any", "label": "Any detection"},
      {"value": "new", "label": "New species (not seen today)"},
      {"value": "specific", "label": "Specific species"}
    ],
    "default": "any"
  },
  {
    "key": "species_name",
    "label": "Species name",
    "type": "text",
    "default": "",
    "visible_when": {"species_filter": "specific"}
  }
]
```

```python
# app.py
def trigger(settings, conditions):
    import requests
    host = settings.get('birdnet_host', '192.168.86.139')
    port = settings.get('birdnet_port', '80')
    min_conf = int(settings.get('min_confidence', '70')) / 100
    species_filter = conditions.get('species_filter', 'any')
    species_name = conditions.get('species_name', '').lower()

    state = getattr(trigger, '_state', None)
    if state is None:
        state = {'seen_today': set(), 'last_id': None}
        setattr(trigger, '_state', state)

    try:
        r = requests.get(f"http://{host}:{port}/api/v1/detections/recent?limit=5", timeout=5)
        detections = [d for d in r.json() if d['confidence'] >= min_conf]
        if not detections:
            return False
        latest = detections[0]
        if latest.get('id') == state['last_id']:
            return False  # nothing new
        state['last_id'] = latest.get('id')

        if species_filter == 'any':
            return True
        if species_filter == 'specific':
            return species_name in latest['species'].lower()
        if species_filter == 'new':
            sp = latest['species']
            if sp not in state['seen_today']:
                state['seen_today'].add(sp)
                return True
        return False
    except Exception:
        return False
```

### Triggers that don't need conditions

If your app has a single obvious trigger condition (e.g. "ISS is overhead"), you can omit `trigger_conditions` entirely. The trigger UI will show just the display duration and cooldown controls.

```json
{
  "trigger_interval": 60,
  "trigger_display_seconds": 30,
  "trigger_cooldown": 600
}
```

```python
def trigger(settings, conditions):
    return is_iss_overhead(settings)
```


## Optional: Lucide Icon in Settings Modal

The settings modal title uses the emoji from `manifest.json` by default. If you want a Lucide icon instead, add your app to the `LUCIDE_APP_ICONS` map in `server/static/app.js`:

```js
const LUCIDE_APP_ICONS = {
  // ...existing entries...
  'my-app': 'plane',  // any Lucide icon name
};
```

Browse available icons at [lucide.dev](https://lucide.dev). The emoji in `manifest.json` is still used as a fallback on app tiles and in the App Library.
