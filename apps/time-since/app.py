def fetch(settings, format_lines, get_rows, get_cols, i18n=None):
    from datetime import datetime
    import pytz

    def t(s):
        return i18n.t(s, "time") if i18n is not None else s

    def u(k):                       # localized Y/D/H/M/S suffix
        return i18n.unit(k) if i18n is not None else k

    tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    now = datetime.now(tz)
    event = settings.get('event_name', 'THE START').upper()
    date_str = settings.get('event_date', '2024-01-01')
    try:
        start = datetime.strptime(date_str, '%Y-%m-%d')
        start = tz.localize(start)
    except Exception:
        return [format_lines(event, t('INVALID DATE'), '')]
    diff = now - start
    if diff.total_seconds() < 0:
        return [format_lines(event, t('NOT YET'), t('STARTED'))]
    days = diff.days
    hrs, rem = divmod(diff.seconds, 3600)
    mins, secs = divmod(rem, 60)
    years = days // 365
    remaining_days = days % 365
    if years > 0:
        elapsed = f'{years}{u("Y")} {remaining_days}{u("D")} {hrs}{u("H")}'
    else:
        elapsed = f'{days}{u("D")} {hrs}{u("H")} {mins}{u("M")} {secs}{u("S")}'
    return [format_lines(event, elapsed, t('TIME SINCE'))]


def trigger(settings, conditions):
    """Fire when the elapsed time hits a round milestone."""
    from datetime import datetime
    import pytz

    milestone = conditions.get('milestone', '1y')
    tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    now = datetime.now(tz)
    date_str = settings.get('event_date', '2024-01-01')

    state = getattr(trigger, '_state', None)
    if state is None:
        state = {'fired_milestone': None}
        setattr(trigger, '_state', state)

    try:
        start = tz.localize(datetime.strptime(date_str, '%Y-%m-%d'))
        diff = now - start
        if diff.total_seconds() < 0:
            return False
        days = diff.days

        # Map milestone to day windows
        windows = {
            '100d': (100, 101),
            '365d': (365, 366),
            '1y':   (365, 366),
            '2y':   (730, 731),
            '5y':   (1825, 1826),
            '10y':  (3650, 3651),
        }
        lo, hi = windows.get(milestone, (365, 366))
        in_window = lo <= days < hi
        key = f"{milestone}:{date_str}:{lo}"

        if in_window and state['fired_milestone'] != key:
            state['fired_milestone'] = key
            return True
        if not in_window and state['fired_milestone'] == key:
            state['fired_milestone'] = None
    except Exception:
        raise
    return False
