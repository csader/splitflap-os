def fetch(settings, format_lines, get_rows, get_cols, i18n=None):
    from datetime import datetime
    import pytz
    try:
        tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    except pytz.UnknownTimeZoneError:
        tz = pytz.timezone('US/Eastern')
    now = datetime.now(tz)
    # When the companion injects i18n, honor the global Language: localized weekday,
    # locale-ordered date (9 JUILLET, not JUILLET 9), and 24h time outside English.
    if i18n is not None:
        time_str = i18n.time(now)
        weekday = i18n.weekday(now)
        month_day = i18n.date(now)
    else:
        time_str = now.strftime('%I:%M %p').lstrip('0')
        weekday = now.strftime('%A').upper()
        month_day = f"{now.strftime('%B').upper()} {now.day}"
    rows = get_rows()
    if rows == 2:
        return [format_lines(month_day, weekday)]
    return [format_lines(time_str, month_day, weekday)]
