"""Dashboard plugin: time + current weather (via the shared weather helper)."""

def fetch(settings, format_lines, get_rows, get_cols, get_weather=None, i18n=None):
    from datetime import datetime
    import pytz
    try:
        tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    except pytz.UnknownTimeZoneError:
        tz = pytz.timezone('US/Eastern')
    dt = datetime.now(tz)
    if i18n is not None:                     # localized names, locale date order, 24h outside English
        weekday = i18n.weekday(dt)
        date_line = i18n.date(dt, short=True, year=True)
        time_str = i18n.time(dt)
    else:
        weekday = dt.strftime("%A").upper()
        date_line = dt.strftime("%b %d %Y").upper()
        time_str = dt.strftime("%I:%M %p").lstrip("0")
    time_page = format_lines(weekday, date_line, time_str)

    # Weather comes from the companion's shared helper (global provider + key +
    # location). With no helper (e.g. a bare host), just show the time.
    if get_weather is None:
        return [time_page]
    w = get_weather()
    if not w or not w.get('ok'):
        return [time_page, format_lines("NO WEATHER", "DATA", "TRY LATER")]

    c = get_cols()
    city = str(w.get('city') or 'LOCATION').upper()
    temp = w.get('temp_f')
    feels = w.get('feels_like_f')
    desc = str(w.get('desc') or '').upper()
    if i18n is not None:                     # translate shared-helper condition text where we can
        desc = i18n.t(desc, "weather")
    high = w.get('hi_f')
    low = w.get('lo_f')
    now_t = i18n.time(dt, ampm_space=False) if i18n is not None else dt.strftime("%I:%M%p").lstrip("0")
    mcl = max(1, c - 1 - len(now_t))
    l1 = f"{city[:mcl]} {now_t}".center(c)
    pfx = f"{temp}F ({feels}F) "
    l2 = (pfx + desc[:max(0, c - len(pfx))]).center(c)
    l3 = f"H:{high}F L:{low}F".center(c)
    return [time_page, format_lines(l1, l2, l3)]
