def fetch(settings, format_lines, get_rows, get_cols):
    from datetime import datetime
    import pytz
    tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    now = datetime.now(tz)
    time_str = now.strftime('%I:%M %p')
    month_day = now.strftime('%B %d')
    weekday = now.strftime('%A')
    rows = get_rows()
    if rows == 2:
        return [format_lines(month_day, weekday)]
    return [format_lines(time_str, month_day, weekday)]
