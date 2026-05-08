def fetch(settings, format_lines, get_rows, get_cols):
    import requests
    from datetime import datetime, timezone
    stop = settings.get('mbta_stop', 'place-bbsta')
    route = settings.get('mbta_route', 'Orange')
    try:
        r = requests.get(
            'https://api-v3.mbta.com/predictions',
            params={'filter[stop]': stop, 'filter[route]': route, 'sort': 'arrival_time'},
            timeout=10
        ).json()
        preds = {}
        now = datetime.now(timezone.utc)
        for p in r.get('data', []):
            arr = p['attributes'].get('arrival_time')
            d_id = p['attributes'].get('direction_id', 0)
            if arr and d_id not in preds:
                dt = datetime.fromisoformat(arr)
                mins = max(0, int((dt - now).total_seconds() // 60))
                preds[d_id] = f'{mins} MIN'
        header = f'🟧 {route.upper()} LINE 🟧'
        line0 = preds.get(0, 'NO DATA')
        line1 = preds.get(1, 'NO DATA')
        rows = get_rows()
        if rows == 1:
            return [format_lines(f'DIR0 {line0} DIR1 {line1}')]
        if rows == 2:
            return [format_lines(f'DIR0 {line0}', f'DIR1 {line1}')]
        return [format_lines(header, f'DIR0 {line0}', f'DIR1 {line1}')]
    except Exception:
        return [format_lines('METRO', 'ERROR', 'CHECK CONFIG')]
