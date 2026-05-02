def fetch(settings, format_lines, get_rows, get_cols):
    from datetime import datetime
    import pytz
    tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    now = datetime.now(tz)
    event = settings.get('event_name', 'THE START').upper()
    date_str = settings.get('event_date', '2024-01-01')
    try:
        start = datetime.strptime(date_str, '%Y-%m-%d')
        start = tz.localize(start)
    except Exception:
        return [format_lines(event, 'INVALID DATE', '')]
    diff = now - start
    if diff.total_seconds() < 0:
        return [format_lines(event, 'NOT YET', 'STARTED')]
    days = diff.days
    hrs, rem = divmod(diff.seconds, 3600)
    mins, secs = divmod(rem, 60)
    years = days // 365
    remaining_days = days % 365
    if years > 0:
        elapsed = f'{years}Y {remaining_days}D {hrs}H'
    else:
        elapsed = f'{days}D {hrs}H {mins}M {secs}S'
    return [format_lines(event, elapsed, 'TIME SINCE')]
