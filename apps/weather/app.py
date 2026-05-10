AQI_LABELS = {1: 'GOOD', 2: 'FAIR', 3: 'MODERATE', 4: 'POOR', 5: 'V.POOR'}


def _pollen_level(val):
    if val is None or val < 1:
        return 'NONE'
    if val < 10:
        return 'LOW'
    if val < 50:
        return 'MOD'
    if val < 200:
        return 'HIGH'
    return 'V.HIGH'


def fetch(settings, format_lines, get_rows, get_cols):
    import requests
    api_key = settings.get('weather_api_key', '')
    zip_code = settings.get('zip_code', '02118')
    show_aqi = settings.get('show_aqi', 'yes') == 'yes'
    show_pollen = settings.get('show_pollen', 'yes') == 'yes'
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
        lat = r['coord']['lat']
        lon = r['coord']['lon']

        rows = get_rows()
        if rows == 1:
            pages = [format_lines(f'{temp} {desc}')]
        elif rows == 2:
            pages = [
                format_lines(f'{temp} {feels}', desc),
                format_lines(f'{hi} {lo}', desc),
            ]
        else:
            pages = [
                format_lines(city, f'{temp} {feels}', desc),
                format_lines(city, f'{hi} {lo}', desc),
            ]

        if show_aqi:
            try:
                aq = requests.get(
                    'https://api.openweathermap.org/data/2.5/air_pollution',
                    params={'lat': lat, 'lon': lon, 'appid': api_key},
                    timeout=10
                ).json()
                aqi_num = aq['list'][0]['main']['aqi']
                aqi_label = AQI_LABELS.get(aqi_num, 'UNKNOWN')
                if rows == 1:
                    pages.append(format_lines(f'AQI {aqi_label}'))
                elif rows == 2:
                    pages.append(format_lines(f'AQI {aqi_num}', aqi_label))
                else:
                    pages.append(format_lines(city, f'AQI {aqi_num}', aqi_label))
            except Exception:
                pass

        if show_pollen:
            try:
                pollen_r = requests.get(
                    'https://air-quality-api.open-meteo.com/v1/air-quality',
                    params={
                        'latitude': lat,
                        'longitude': lon,
                        'current': 'grass_pollen,birch_pollen,ragweed_pollen,weed_pollen',
                    },
                    timeout=10
                ).json()
                curr = pollen_r.get('current', {})
                grass = curr.get('grass_pollen')
                birch = curr.get('birch_pollen')
                ragweed = curr.get('ragweed_pollen')
                weed = curr.get('weed_pollen')

                vals = [v for v in [grass, birch, ragweed, weed] if v is not None]
                overall = max(vals) if vals else None
                overall_label = _pollen_level(overall)
                grass_label = _pollen_level(grass)
                tree_label = _pollen_level(birch)
                weed_label = _pollen_level(weed or ragweed)

                if rows == 1:
                    pages.append(format_lines(f'POLLEN {overall_label}'))
                elif rows == 2:
                    pages.append(format_lines('POLLEN', overall_label))
                    pages.append(format_lines(f'GRS {grass_label}', f'TRE {tree_label}', f'WED {weed_label}'))
                else:
                    pages.append(format_lines(city, 'POLLEN', overall_label))
                    pages.append(format_lines(city, f'GRS {grass_label}', f'TRE {tree_label}', f'WED {weed_label}'))
            except Exception:
                pass

        return pages
    except Exception:
        return [format_lines('WEATHER', 'ERROR', 'CHECK API KEY')]
