def fetch(settings, format_lines, get_rows, get_cols):
    import requests
    api_key = settings.get('weather_api_key', '')
    zip_code = settings.get('zip_code', '02118')
    try:
        r = requests.get(
            'https://api.openweathermap.org/data/2.5/weather',
            params={'zip': f'{zip_code},us', 'appid': api_key, 'units': 'imperial'},
            timeout=10
        ).json()
        city = r['name'].upper()
        temp = f"{int(r['main']['temp'])}F"
        feels = f"FEELS {int(r['main']['feels_like'])}F"
        desc = r['weather'][0]['description'].upper()
        hi = f"H {int(r['main']['temp_max'])}F"
        lo = f"L {int(r['main']['temp_min'])}F"
        return [
            format_lines(city, f'{temp} {feels}', desc),
            format_lines(city, f'{hi} {lo}', desc),
        ]
    except Exception:
        return [format_lines('WEATHER', 'ERROR', 'CHECK API KEY')]
