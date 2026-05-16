"""Bitcoin Fear & Greed Index plugin for Split-Flap Display."""

def fetch(settings, format_lines, get_rows, get_cols):
    import urllib.request
    import json
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "SplitFlap/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        entry = data["data"][0]
        value = entry["value"]
        label = entry["value_classification"].upper()
        return [format_lines("BTC FEAR&GREED", f"INDEX: {value}/100", label)]
    except Exception:
        return [format_lines("FEAR & GREED", "FETCH ERROR", "")]


def trigger(settings, conditions):
    """Fire when the Fear & Greed index crosses into extreme territory."""
    import urllib.request, json

    zone = conditions.get('zone', 'extreme_fear')
    threshold = int(conditions.get('threshold', 20))

    state = getattr(trigger, '_state', None)
    if state is None:
        state = {'last_zone': None}
        setattr(trigger, '_state', state)

    try:
        url = "https://api.alternative.me/fng/?limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "SplitFlap/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        value = int(data["data"][0]["value"])

        if zone == 'extreme_fear':
            in_zone = value <= threshold
        elif zone == 'extreme_greed':
            in_zone = value >= (100 - threshold)
        else:  # either
            in_zone = value <= threshold or value >= (100 - threshold)

        current_zone = zone if in_zone else None
        if in_zone and state['last_zone'] != current_zone:
            state['last_zone'] = current_zone
            return True
        if not in_zone:
            state['last_zone'] = None
    except Exception:
        pass
    return False
