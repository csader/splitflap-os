# Inbox App

The Inbox app turns your split-flap display into a push-based notification board. Instead of polling an API, external services send messages to your display via a simple HTTP endpoint.

## Endpoint

```
POST http://<splitflap-host>/inbox
```

### Request Body (JSON)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `text` | string | **yes** | — | Message to display (auto-uppercased) |
| `source` | string | no | `"unknown"` | Sender identifier for filtering/display |
| `priority` | string | no | `"normal"` | `"low"`, `"normal"`, or `"high"` |
| `ttl` | number | no | app setting | Minutes before message expires |
| `animation` | string | no | none | Animation order (e.g. `"rain"`, `"spiral"`) |
| `style` | object | no | `{}` | Extra display hints (reserved for future use) |

### Response

```json
{"id": "msg_1715367890123", "position": 3}
```

### Additional Endpoints

```
GET    /inbox              — List current messages in queue
DELETE /inbox              — Clear all messages
DELETE /inbox?source=drift — Clear messages from a specific source
```

---

## Examples

### Basic message

```bash
curl -X POST http://splitflap.local/inbox \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}'
```

### Hermes Agent cron job — Daily briefing

Set up a Hermes cron job that composes a morning summary and pushes it:

```bash
# In Hermes, create a cron job:
# Schedule: "0 7 * * *" (7am daily)
# Prompt: "Check weather for Austin TX, summarize in under 40 chars, 
#          then POST to http://splitflap.local/inbox with source 'briefing'"

curl -X POST http://splitflap.local/inbox \
  -H "Content-Type: application/json" \
  -d '{"text": "72F SUNNY HIGH 88", "source": "briefing", "ttl": 120}'
```

### OpenClaw agent status notifications

Agents report task completions or alerts:

```bash
# Agent completed a PR
curl -X POST http://splitflap.local/inbox \
  -H "Content-Type: application/json" \
  -d '{
    "text": "PR MERGED SATYR-OS #47",
    "source": "openclaw",
    "priority": "normal",
    "ttl": 30
  }'

# Drift alert — portfolio change
curl -X POST http://splitflap.local/inbox \
  -H "Content-Type: application/json" \
  -d '{
    "text": "DRIFT AAPL +2.3% REBALANCE",
    "source": "drift",
    "priority": "high",
    "ttl": 60
  }'
```

### Frigate camera alerts

Trigger from Frigate's webhook or Home Assistant automation:

```bash
# Person detected at front door
curl -X POST http://splitflap.local/inbox \
  -H "Content-Type: application/json" \
  -d '{
    "text": "PERSON AT FRONT DOOR",
    "source": "frigate",
    "priority": "high",
    "ttl": 5,
    "animation": "center_out"
  }'

# Package delivered
curl -X POST http://splitflap.local/inbox \
  -H "Content-Type: application/json" \
  -d '{
    "text": "PACKAGE DELIVERED",
    "source": "frigate",
    "priority": "normal",
    "ttl": 30
  }'
```

### Home Assistant automations

Use HA's `rest_command` or `shell_command` integration:

```yaml
# configuration.yaml
rest_command:
  splitflap_message:
    url: "http://splitflap.local/inbox"
    method: POST
    content_type: "application/json"
    payload: '{"text": "{{ message }}", "source": "homeassistant", "priority": "{{ priority | default(''normal'') }}", "ttl": {{ ttl | default(60) }}}'

# automations.yaml
- alias: "Splitflap - Washer Done"
  trigger:
    - platform: state
      entity_id: sensor.washer_status
      to: "complete"
  action:
    - service: rest_command.splitflap_message
      data:
        message: "WASHER DONE"
        priority: "normal"
        ttl: 30
```

### Generic webhook (n8n, Make, Zapier)

Any webhook service can POST JSON to the endpoint:

```bash
# Slack notification relay
curl -X POST http://splitflap.local/inbox \
  -H "Content-Type: application/json" \
  -d '{
    "text": "NEW MSG FROM BOSS",
    "source": "slack",
    "priority": "high",
    "ttl": 15
  }'

# Calendar reminder
curl -X POST http://splitflap.local/inbox \
  -H "Content-Type: application/json" \
  -d '{
    "text": "MEETING IN 10 MIN",
    "source": "calendar",
    "priority": "high",
    "ttl": 10
  }'
```

### Python script

```python
import requests

def notify_splitflap(text, source="script", priority="normal", ttl=60):
    requests.post("http://splitflap.local/inbox", json={
        "text": text,
        "source": source,
        "priority": priority,
        "ttl": ttl,
    })

# Usage
notify_splitflap("BUILD PASSED", source="ci", ttl=15)
notify_splitflap("DEPLOY FAILED", source="ci", priority="high", ttl=30)
```

### MQTT (via Home Assistant or direct)

If your splitflap-os instance has MQTT enabled, you can also publish to the inbox via MQTT topic. Configure a Home Assistant automation or mosquitto_pub:

```bash
mosquitto_pub -h mqtt-broker.local -t "splitflap/inbox" \
  -m '{"text": "GARAGE OPEN 5 MIN", "source": "mqtt", "priority": "high"}'
```

> Note: MQTT inbox support requires the MQTT topic to be configured in splitflap-os settings. The HTTP endpoint works out of the box.

---

## Behavior

- Messages are displayed in priority order (high first), then newest first
- Expired messages (past TTL) are automatically pruned
- Queue persists across server restarts (saved to `apps/inbox/queue.json`)
- When the inbox app is active, it rotates through all queued messages
- If no messages are in the queue, displays "INBOX NO MESSAGES"
- High priority messages show a `!` indicator

## Settings

Configure in the splitflap-os UI under the Inbox app settings:

- **Max Messages in Queue** — oldest messages are dropped when exceeded (default: 20)
- **Default Message TTL** — minutes before a message expires if no TTL specified (default: 60)
- **Show Timestamp** — display the time each message was received (default: on)
- **Minimum Priority** — filter out low-priority messages (default: all)

## Tips

- Keep messages short — split-flap displays are typically 15-20 chars wide
- Use `source` consistently so you can clear all messages from one sender
- Set short TTLs for transient alerts (camera, doorbell) and longer for informational
- High priority messages always display first regardless of age
- Use `DELETE /inbox?source=briefing` to clear old briefings before pushing new ones
