def fetch(settings, format_lines, get_rows, get_cols, i18n=None):
    from datetime import datetime
    import pytz
    cols = get_cols()
    zones = [s.strip() for s in settings.get('world_clock_zones', 'US/Eastern,US/Pacific,Europe/London').split(',') if s.strip()]
    lines = []
    for z in zones[:get_rows()]:
        try:
            tz = pytz.timezone(z)
        except pytz.UnknownTimeZoneError:
            continue
        now = datetime.now(tz)
        # Compact time leaves room for the city; a long city is trimmed so the time
        # is never cut off. AM/PM is an English convention — everyone else is 24h.
        if i18n is not None:
            t = i18n.time(now, ampm_space=False)
        else:
            t = now.strftime('%I:%M%p').lstrip('0')
        city = z.split('/')[-1].replace('_', ' ').upper()
        avail = max(1, cols - len(t) - 1)
        lines.append(f'{city[:avail]} {t}')
    if not lines:
        lines = ['NO VALID', 'TIMEZONES']
    lines += [''] * max(0, get_rows() - len(lines))
    return [format_lines(*lines)]


def trigger(settings, conditions):
    """Fire when business hours start or end in a followed timezone."""
    from datetime import datetime
    import pytz

    event = conditions.get('event', 'open')
    zones = [s.strip() for s in settings.get('world_clock_zones', 'US/Eastern,US/Pacific,Europe/London').split(',')]

    state = getattr(trigger, '_state', None)
    if state is None:
        state = {'fired_today': set()}
        setattr(trigger, '_state', state)

    # Reset daily
    today = datetime.utcnow().strftime('%Y-%m-%d')
    if state.get('date') != today:
        state['fired_today'] = set()
        state['date'] = today

    for z in zones:
        try:
            tz = pytz.timezone(z)
            now = datetime.now(tz)
            hour, minute = now.hour, now.minute
            city = z.split('/')[-1].replace('_', ' ')
            key = f"{event}:{z}:{today}"

            if event == 'open' and hour == 9 and minute < 5:
                if key not in state['fired_today']:
                    state['fired_today'].add(key)
                    return True
            elif event == 'close' and hour == 17 and minute < 5:
                if key not in state['fired_today']:
                    state['fired_today'].add(key)
                    return True
        except Exception:
            continue
    return False
