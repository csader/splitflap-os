def fetch(settings, format_lines, get_rows, get_cols):
    from datetime import datetime
    import pytz
    tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    now = datetime.now(tz)
    fmt = "%H:%M" if settings.get('time_format') == '24hr' else "%I:%M%p"
    time_str = now.strftime(fmt).lstrip("0")
    rows = get_rows()
    if rows == 1:
        return [format_lines(time_str)]
    return [format_lines('', time_str, '')]
