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


def trigger(settings, conditions):
    """Fire when the next train is arriving within the configured window, or on service alerts."""
    import requests
    from datetime import datetime, timezone

    condition_type = conditions.get('condition_type', 'arriving')
    minutes = int(conditions.get('minutes', 5))
    direction = conditions.get('direction', 'either')
    stop = settings.get('mbta_stop', 'place-bbsta')
    route = settings.get('mbta_route', 'Orange')

    state = getattr(trigger, '_state', None)
    if state is None:
        state = {'seen_alert_ids': set()}
        setattr(trigger, '_state', state)

    try:
        if condition_type == 'arriving':
            r = requests.get(
                'https://api-v3.mbta.com/predictions',
                params={'filter[stop]': stop, 'filter[route]': route, 'sort': 'arrival_time'},
                timeout=10
            ).json()
            now = datetime.now(timezone.utc)
            for p in r.get('data', []):
                arr = p['attributes'].get('arrival_time')
                d_id = p['attributes'].get('direction_id', 0)
                if not arr:
                    continue
                if direction == '0' and d_id != 0:
                    continue
                if direction == '1' and d_id != 1:
                    continue
                dt = datetime.fromisoformat(arr)
                mins_away = (dt - now).total_seconds() / 60
                if 0 <= mins_away <= minutes:
                    return True

        elif condition_type == 'alert':
            r = requests.get(
                'https://api-v3.mbta.com/alerts',
                params={'filter[route]': route, 'filter[stop]': stop},
                timeout=10
            ).json()
            for alert in r.get('data', []):
                aid = alert.get('id', '')
                effect = alert.get('attributes', {}).get('effect', '')
                # Only fire for service-affecting alerts
                if effect in ('DELAY', 'SUSPENSION', 'SHUTTLE', 'STOP_CLOSURE', 'DETOUR'):
                    if aid not in state['seen_alert_ids']:
                        state['seen_alert_ids'].add(aid)
                        return True
            # Prune old alert IDs
            if len(state['seen_alert_ids']) > 200:
                state['seen_alert_ids'] = set(list(state['seen_alert_ids'])[-100:])

    except Exception:
        pass
    return False
