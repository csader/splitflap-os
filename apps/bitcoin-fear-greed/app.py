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
