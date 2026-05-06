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
