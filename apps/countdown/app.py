def fetch(settings, format_lines, get_rows, get_cols):
    from datetime import datetime
    import pytz
    event = settings.get('countdown_event', 'NEW YEAR')
    target_str = settings.get('countdown_target', '')
    tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    now = datetime.now(tz)
    if not target_str:
        target = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        target = datetime.fromisoformat(target_str)
        if target.tzinfo is None:
            target = tz.localize(target)
    diff = target - now
    if diff.total_seconds() <= 0:
        return [format_lines(event.upper(), 'EVENT ARRIVED', '🎉🎉🎉')]
    days = diff.days
    hrs, rem = divmod(diff.seconds, 3600)
    mins, secs = divmod(rem, 60)
    return [format_lines(event.upper(), f'{days}D {hrs}H {mins}M {secs}S', 'REMAINING')]
