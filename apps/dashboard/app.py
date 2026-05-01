"""Dashboard plugin: time + weather combined."""

def fetch(settings, format_lines, get_rows, get_cols):
    from datetime import datetime
    import pytz
    tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    dt = datetime.now(tz)
    time_page = format_lines(dt.strftime("%A").upper(),
                             dt.strftime("%b %d %Y").upper(),
                             dt.strftime("%I:%M %p").upper())
    # Weather
    try:
        import requests
        api_key = settings.get('weather_api_key', '').strip()
        zip_code = settings.get('zip_code', '02118').strip()
        if not api_key:
            return [time_page, format_lines("NO WEATHER DATA", "", "CHECK API KEY")]
        url = f"http://api.openweathermap.org/data/2.5/weather?zip={zip_code},us&appid={api_key}&units=imperial"
        res = requests.get(url, timeout=5).json()
        c = get_cols()
        city = res['name'].upper()
        temp = round(res['main']['temp'])
        feels = round(res['main']['feels_like'])
        desc = res['weather'][0]['main'].upper()
        high = round(res['main']['temp_max'])
        low = round(res['main']['temp_min'])
        now_t = dt.strftime("%I:%M%p").lstrip("0")
        mcl = c - 1 - len(now_t)
        l1 = f"{city[:mcl]} {now_t}".center(c)
        pfx = f"{temp}F ({feels}F) "
        l2 = (pfx + desc[:c - len(pfx)]).center(c)
        l3 = f"H:{high}F L:{low}F".center(c)
        return [time_page, format_lines(l1, l2, l3)]
    except Exception:
        return [time_page, format_lines("WEATHER ERROR", "", "")]
