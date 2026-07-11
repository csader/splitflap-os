def fetch(settings, format_lines, get_rows, get_cols, i18n=None):
    from datetime import datetime
    import pytz
    tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    now = datetime.now(tz)
    # An explicit Time Format wins; otherwise the Language decides (12h AM/PM for
    # English, 24h elsewhere) via the injected i18n helper.
    tf = settings.get('time_format')
    if tf in ('12hr', '24hr'):
        time_str = now.strftime("%H:%M" if tf == '24hr' else "%I:%M%p").lstrip("0")
    elif i18n is not None:
        time_str = i18n.time(now, ampm_space=False)
    else:
        time_str = now.strftime("%I:%M%p").lstrip("0")
    rows = get_rows()
    if rows == 1:
        return [format_lines(time_str)]
    return [format_lines('', time_str, '')]
