"""On This Day in History plugin for Split-Flap Display."""

def fetch(settings, format_lines, get_rows, get_cols):
    import urllib.request
    import json
    import random
    from datetime import datetime
    import pytz

    cols = get_cols()
    rows = get_rows()
    tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    now = datetime.now(tz)

    fallback = [
        (1776, "DECLARATION OF INDEPENDENCE SIGNED"),
        (1969, "FIRST MOON LANDING BY APOLLO 11"),
        (1989, "BERLIN WALL FALLS IN GERMANY"),
        (1903, "WRIGHT BROTHERS FIRST FLIGHT"),
        (1865, "CIVIL WAR ENDS IN AMERICA"),
        (1945, "WORLD WAR 2 ENDS"),
        (1963, "I HAVE A DREAM SPEECH BY MLK"),
        (1912, "TITANIC SINKS ON MAIDEN VOYAGE"),
        (1929, "STOCK MARKET CRASH BLACK TUESDAY"),
        (1955, "ROSA PARKS REFUSES TO GIVE UP SEAT"),
    ]

    def split_text(text, width):
        words = text.split()
        lines = []
        current = ''
        for word in words:
            if current and len(current) + 1 + len(word) > width:
                lines.append(current)
                current = word
            elif not current:
                current = word[:width]
            else:
                current += ' ' + word
        if current:
            lines.append(current)
        return lines

    try:
        url = f"https://byabbe.se/on-this-day/{now.month}/{now.day}/events.json"
        req = urllib.request.Request(url, headers={"User-Agent": "SplitFlap/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        events = data.get("events", [])
        if not events:
            raise ValueError("No events")
        event = random.choice(events)
        year = event.get("year", "")
        desc = event.get("description", "").upper()
    except Exception:
        year, desc = random.choice(fallback)
        year = str(year)
        desc = desc.upper()

    allowed = set(" ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$&()-+=;:%'.,/?*")
    desc = ''.join(c if c in allowed else ' ' for c in desc)

    text_lines = split_text(desc, cols)
    pages = []
    header = f'ON THIS DAY {year}'
    first_page = [header] + text_lines[:rows - 1]
    pages.append(format_lines(*first_page[:rows]))

    remaining = text_lines[rows - 1:]
    for i in range(0, len(remaining), rows):
        chunk = remaining[i:i + rows]
        pages.append(format_lines(*chunk))

    return pages
