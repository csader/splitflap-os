def fetch(settings, format_lines, get_rows, get_cols):
    from datetime import datetime
    import pytz
    tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    now = datetime.now(tz)
    time_str = now.strftime('%I:%M:%S %p')
    return [format_lines('', time_str, '')]
