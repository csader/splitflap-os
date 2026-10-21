"""Recent significant earthquakes worldwide (USGS FDSN, keyless)."""


def _wrap(text, cols, maxlines):
    words, lines, cur = text.split(), [], ''
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= cols:
            cur = f'{cur} {w}'.strip()
        else:
            lines.append(cur)
            cur = w[:cols]
            if len(lines) >= maxlines:
                break
    if cur and len(lines) < maxlines:
        lines.append(cur)
    return lines[:maxlines] or ['']


def fetch(settings, format_lines, get_rows, get_cols):
    import requests
    from datetime import datetime, timezone
    rows, cols = get_rows(), get_cols()
    try:
        minmag = str(settings.get('min_magnitude', '4.5') or '4.5')
        data = requests.get('https://earthquake.usgs.gov/fdsnws/event/1/query',
                            params={'format': 'geojson', 'orderby': 'time', 'limit': 5,
                                    'minmagnitude': minmag}, timeout=8).json()
        feats = data.get('features', []) or []
        now = datetime.now(timezone.utc).timestamp()
        pages = []
        for ft in feats[:5]:
            p = ft.get('properties', {}) or {}
            mag = p.get('mag')
            place = str(p.get('place', '') or 'UNKNOWN').upper()
            mags = f'M{mag:.1f}' if isinstance(mag, (int, float)) else 'M?'
            ago = ''
            ms = p.get('time')
            if isinstance(ms, (int, float)):
                mins = int((now - ms / 1000) / 60)
                ago = f'{mins}M AGO' if mins < 120 else f'{mins // 60}H AGO'
            # USGS place is like "134 KM E OF BITUNG, INDONESIA": show the distance
            # on the header line and give the location name the remaining rows so
            # it isn't cut off.
            if ' OF ' in place:
                dist, loc = place.split(' OF ', 1)
                head = f'{mags} {dist.strip()}'
            else:
                loc, head = place, f'{mags}  {ago}'.strip()
            if rows == 1:
                pages.append(f'{mags} {loc}'[:cols].center(cols))
            elif rows == 2:
                pages.append(format_lines(head, *_wrap(loc, cols, 1)))
            else:
                pages.append(format_lines(head, *_wrap(loc, cols, rows - 1)))
        return pages or [format_lines('EARTHQUAKES', 'NONE RECENT', '')]
    except Exception:
        return [format_lines('EARTHQUAKES', 'OFFLINE', '')]
