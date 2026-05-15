AQI_LABELS = {1: 'GOOD', 2: 'FAIR', 3: 'MODERATE', 4: 'POOR', 5: 'V.POOR'}

OPENMETEO_WEATHER_CODES = {
    0: 'CLEAR',
    1: 'MAINLY CLEAR',
    2: 'PARTLY CLOUDY',
    3: 'OVERCAST',
    45: 'FOG',
    48: 'RIME FOG',
    51: 'LIGHT DRIZZLE',
    53: 'DRIZZLE',
    55: 'HEAVY DRIZZLE',
    61: 'LIGHT RAIN',
    63: 'RAIN',
    65: 'HEAVY RAIN',
    66: 'LIGHT FREEZING RAIN',
    67: 'FREEZING RAIN',
    71: 'LIGHT SNOW',
    73: 'SNOW',
    75: 'HEAVY SNOW',
    77: 'SNOW GRAINS',
    80: 'RAIN SHOWERS',
    81: 'RAIN SHOWERS',
    82: 'HEAVY SHOWERS',
    85: 'SNOW SHOWERS',
    86: 'HEAVY SNOW SHOWERS',
    95: 'THUNDERSTORM',
    96: 'THUNDER HAIL',
    99: 'SEVERE TSTORM',
}


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


def _uv_level(val):
    if val is None:
        return 'UNKNOWN'
    if val < 3:
        return 'LOW'
    if val < 6:
        return 'MOD'
    if val < 8:
        return 'HIGH'
    if val < 11:
        return 'V.HIGH'
    return 'EXTREME'


def _us_aqi_level(val):
    if val is None:
        return 'UNKNOWN'
    if val <= 50:
        return 'GOOD'
    if val <= 100:
        return 'MOD'
    if val <= 150:
        return 'USG'
    if val <= 200:
        return 'UNHEALTHY'
    if val <= 300:
        return 'V.UNHLTHY'
    return 'HAZARDOUS'


def _weatherapi_aqi_level(val):
    labels = {
        1: 'GOOD',
        2: 'MOD',
        3: 'USG',
        4: 'UNHEALTHY',
        5: 'V.UNHLTHY',
        6: 'HAZARDOUS',
    }
    return labels.get(val, 'UNKNOWN')


def _aqi_color_from_us(value):
    if value is None:
        return 'UNKNOWN'
    if value <= 50:
        return 'GREEN'
    if value <= 100:
        return 'YELLOW'
    if value <= 150:
        return 'ORANGE'
    return 'RED'


def _aqi_color_from_openweather(value):
    if value is None:
        return 'UNKNOWN'
    if value <= 1:
        return 'GREEN'
    if value == 2:
        return 'YELLOW'
    if value == 3:
        return 'ORANGE'
    return 'RED'


def _aqi_color_from_weatherapi(value):
    if value is None:
        return 'UNKNOWN'
    if value <= 1:
        return 'GREEN'
    if value == 2:
        return 'YELLOW'
    if value == 3:
        return 'ORANGE'
    return 'RED'


def _uv_color(val):
    if val is None:
        return 'UNKNOWN'
    if val < 3:
        return 'GREEN'
    if val < 6:
        return 'YELLOW'
    if val < 8:
        return 'ORANGE'
    return 'RED'


def _pollen_color(val):
    if val is None or val < 1:
        return 'NONE'
    if val < 10:
        return 'GREEN'
    if val < 50:
        return 'YELLOW'
    if val < 200:
        return 'ORANGE'
    return 'RED'


def _to_int(value, default=0):
    try:
        return int(round(float(value)))
    except Exception:
        return default


def _convert_temp_from_f(value, temp_unit):
    if value is None:
        return None
    try:
        f_val = float(value)
    except Exception:
        return None
    if temp_unit == 'c':
        return (f_val - 32.0) * (5.0 / 9.0)
    if temp_unit == 'k':
        return (f_val - 32.0) * (5.0 / 9.0) + 273.15
    return f_val


def _format_temp(value, temp_unit):
    converted = _convert_temp_from_f(value, temp_unit)
    if converted is None:
        return '--'
    return f"{int(round(converted))}{temp_unit.upper()}"


def _compact_color(color):
    return {
        'GREEN': '🟩',
        'YELLOW': '🟨',
        'ORANGE': '🟧',
        'RED': '🟥',
        'NONE': '⬛',
        'UNKNOWN': '⬜',
    }.get(color, color)


def _decorate_status(label, color, cols):
    swatch = _compact_color(color)
    text = str(label or '').strip()
    if not text:
        return swatch

    # Ideal form: multiple swatches on both sides, scaled by available columns.
    # Example: 🟩🟩 GOOD 🟩🟩
    max_side = max(0, (cols - len(text) - 2) // 2)
    if max_side >= 1:
        side = swatch * min(4, max_side)
        return f'{side} {text} {side}'

    # Degrade gracefully as width shrinks.
    if cols >= len(text) + 2:
        return f'{swatch} {text}'
    if cols >= len(text):
        return text[:cols]
    return swatch


def fetch(settings, format_lines, get_rows, get_cols):
    import time
    import requests

    # --- Polling state (persists across calls on this plugin instance) ---
    state = getattr(fetch, '_state', None)
    if state is None:
        state = {
            'last_sig': None,
            'last_polled_at': 0.0,
            'last_pages': None,
        }
        setattr(fetch, '_state', state)

    api_key = settings.get('weather_api_key', '')
    zip_code = settings.get('zip_code', '02118')
    weather_provider = settings.get('weather_provider', 'openweather')
    temp_unit = str(settings.get('temperature_unit', 'f')).lower()
    if temp_unit not in ('f', 'c', 'k'):
        temp_unit = 'f'
    show_aqi = settings.get('show_aqi', 'yes') == 'yes'
    show_uv = settings.get('show_uv', 'yes') == 'yes' and weather_provider in ('openmeteo', 'weatherapi')
    show_pollen = settings.get('show_pollen', 'yes') == 'yes' and weather_provider in ('openmeteo', 'weatherapi')
    polling_seconds = max(30.0, min(86400.0, float(settings.get('polling_rate', 300) or 300)))
    openmeteo_air = None

    settings_sig = (
        api_key, zip_code, weather_provider, temp_unit,
        show_aqi, show_uv, show_pollen, polling_seconds,
    )
    now_ts = time.time()
    sig_changed = settings_sig != state['last_sig']
    due_for_poll = (now_ts - state['last_polled_at']) >= polling_seconds
    if not sig_changed and not due_for_poll and state['last_pages'] is not None:
        return state['last_pages']

    def _normalize_weatherapi_pollen(payload):
        if not isinstance(payload, dict):
            return {}
        pollen = {str(k).lower(): v for k, v in payload.items()}
        tree_vals = [pollen.get(name) for name in ('hazel', 'alder', 'birch', 'oak') if pollen.get(name) is not None]
        weed_vals = [pollen.get(name) for name in ('mugwort', 'ragweed') if pollen.get(name) is not None]
        grass = pollen.get('grass')
        tree = max(tree_vals) if tree_vals else None
        weed = max(weed_vals) if weed_vals else None
        vals = [v for v in (grass, tree, weed) if v is not None]
        return {
            'grass': grass,
            'tree': tree,
            'weed': weed,
            'overall': max(vals) if vals else None,
        }

    def _fetch_openweather_weather():
        payload = requests.get(
            'https://api.openweathermap.org/data/2.5/weather',
            params={'zip': f'{zip_code},us', 'appid': api_key, 'units': 'imperial'},
            timeout=10
        ).json()
        return {
            'city': payload['name'].upper(),
            'temp': int(payload['main']['temp']),
            'feels_like': int(payload['main']['feels_like']),
            'hi': int(payload['main']['temp_max']),
            'lo': int(payload['main']['temp_min']),
            'desc': payload['weather'][0]['description'].upper(),
            'lat': payload['coord']['lat'],
            'lon': payload['coord']['lon'],
        }

    def _fetch_openmeteo_weather():
        geo = requests.get(f'https://api.zippopotam.us/us/{zip_code}', timeout=10).json()
        place = (geo.get('places') or [{}])[0]
        lat = float(place['latitude'])
        lon = float(place['longitude'])
        city = str(place.get('place name', zip_code)).upper()
        weather = requests.get(
            'https://api.open-meteo.com/v1/forecast',
            params={
                'latitude': lat,
                'longitude': lon,
                'current': 'temperature_2m,apparent_temperature,weather_code,uv_index',
                'daily': 'temperature_2m_max,temperature_2m_min',
                'temperature_unit': 'fahrenheit',
                'timezone': 'auto',
                'forecast_days': 1,
            },
            timeout=10
        ).json()
        current = weather.get('current', {})
        daily = weather.get('daily', {})
        hi_values = daily.get('temperature_2m_max') or [current.get('temperature_2m')]
        lo_values = daily.get('temperature_2m_min') or [current.get('temperature_2m')]
        return {
            'city': city,
            'temp': int(round(current.get('temperature_2m', 0))),
            'feels_like': int(round(current.get('apparent_temperature', current.get('temperature_2m', 0)))),
            'hi': int(round(hi_values[0] if hi_values else 0)),
            'lo': int(round(lo_values[0] if lo_values else 0)),
            'desc': OPENMETEO_WEATHER_CODES.get(current.get('weather_code'), 'CURRENT CONDITIONS'),
            'lat': lat,
            'lon': lon,
            'uv': current.get('uv_index'),
        }

    def _fetch_weatherapi_weather():
        payload = requests.get(
            'https://api.weatherapi.com/v1/forecast.json',
            params={
                'key': api_key,
                'q': zip_code,
                'days': 1,
                'aqi': 'yes',
                'pollen': 'yes',
            },
            timeout=10
        ).json()
        location = payload.get('location', {})
        current = payload.get('current', {})
        forecast = ((payload.get('forecast') or {}).get('forecastday') or [{}])[0]
        day = forecast.get('day', {})
        pollen = forecast.get('pollen') or current.get('pollen') or day.get('pollen') or {}
        return {
            'city': str(location.get('name', zip_code)).upper(),
            'temp': int(round(current.get('temp_f', 0))),
            'feels_like': int(round(current.get('feelslike_f', current.get('temp_f', 0)))),
            'hi': int(round(day.get('maxtemp_f', current.get('temp_f', 0)))),
            'lo': int(round(day.get('mintemp_f', current.get('temp_f', 0)))),
            'desc': str((current.get('condition') or {}).get('text', 'CURRENT CONDITIONS')).upper(),
            'lat': location.get('lat'),
            'lon': location.get('lon'),
            'uv': current.get('uv'),
            'weatherapi_aqi': ((current.get('air_quality') or {}).get('us-epa-index')),
            'pollen': _normalize_weatherapi_pollen(pollen),
        }

    def _fetch_qweather_weather():
        geo = requests.get(f'https://api.zippopotam.us/us/{zip_code}', timeout=10).json()
        place = (geo.get('places') or [{}])[0]
        lat = float(place['latitude'])
        lon = float(place['longitude'])
        city = str(place.get('place name', zip_code)).upper()
        location = f'{lon:.2f},{lat:.2f}'
        headers = {'Authorization': f'Bearer {api_key}'}

        now_r = requests.get(
            'https://devapi.qweather.com/v7/weather/now',
            params={'location': location, 'lang': 'en', 'unit': 'i'},
            headers=headers,
            timeout=10
        ).json()
        now = now_r.get('now', {})

        daily_r = requests.get(
            'https://devapi.qweather.com/v7/weather/3d',
            params={'location': location, 'lang': 'en', 'unit': 'i'},
            headers=headers,
            timeout=10
        ).json()
        first_day = (daily_r.get('daily') or [{}])[0]

        return {
            'city': city,
            'temp': _to_int(now.get('temp')),
            'feels_like': _to_int(now.get('feelsLike'), _to_int(now.get('temp'))),
            'hi': _to_int(first_day.get('tempMax'), _to_int(now.get('temp'))),
            'lo': _to_int(first_day.get('tempMin'), _to_int(now.get('temp'))),
            'desc': str(now.get('text', 'CURRENT CONDITIONS')).upper(),
            'lat': lat,
            'lon': lon,
        }

    def _fetch_openweather_aqi(lat, lon):
        aq = requests.get(
            'https://api.openweathermap.org/data/2.5/air_pollution',
            params={'lat': lat, 'lon': lon, 'appid': api_key},
            timeout=10
        ).json()
        return aq['list'][0]['main']['aqi']

    def _fetch_openmeteo_air(lat, lon):
        return requests.get(
            'https://air-quality-api.open-meteo.com/v1/air-quality',
            params={
                'latitude': lat,
                'longitude': lon,
                'current': 'us_aqi,uv_index,grass_pollen,birch_pollen,ragweed_pollen,weed_pollen',
            },
            timeout=10
        ).json().get('current', {})

    def _fetch_qweather_aqi(lat, lon):
        headers = {'Authorization': f'Bearer {api_key}'}
        location = f'{lon:.2f},{lat:.2f}'
        aq = requests.get(
            'https://devapi.qweather.com/v7/air/now',
            params={'location': location, 'lang': 'en'},
            headers=headers,
            timeout=10
        ).json()
        return _to_int((aq.get('now') or {}).get('aqi'), None)

    def _get_openmeteo_air(lat, lon):
        nonlocal openmeteo_air
        if openmeteo_air is None:
            openmeteo_air = _fetch_openmeteo_air(lat, lon)
        return openmeteo_air

    try:
        if weather_provider == 'openmeteo':
            weather = _fetch_openmeteo_weather()
        elif weather_provider == 'weatherapi':
            weather = _fetch_weatherapi_weather()
        elif weather_provider == 'qweather':
            weather = _fetch_qweather_weather()
        else:
            weather = _fetch_openweather_weather()

        cols = get_cols()
        narrow = cols <= 12
        feels_word = 'FLS' if narrow else 'FEELS'
        pollen_word = 'POL' if narrow else 'POLLEN'
        overall_word = 'OVR' if narrow else 'OVERALL'
        provider_word = 'PRV' if narrow else 'PROV'
        sun_exposure_text = 'SUN UV' if narrow else 'SUN EXPOSURE'
        grass_word = 'GRS' if narrow else 'GRASS'
        tree_word = 'TRE' if narrow else 'TREE'
        weed_word = 'WED' if narrow else 'WEED'

        city = weather['city']
        temp = _format_temp(weather.get('temp'), temp_unit)
        feels = f"{feels_word} {_format_temp(weather.get('feels_like'), temp_unit)}"
        desc = weather['desc']
        hi = f"H {_format_temp(weather.get('hi'), temp_unit)}"
        lo = f"L {_format_temp(weather.get('lo'), temp_unit)}"
        lat = weather['lat']
        lon = weather['lon']

        rows = get_rows()
        if rows == 1:
            pages = [format_lines(f'{temp} {desc}')]
        elif rows == 2:
            pages = [
                format_lines(f'{temp} {feels}', desc),
                format_lines(f'{hi} {lo}', desc),
            ]
        elif rows == 3:
            pages = [
                format_lines(city, f'{temp} {feels}', desc),
                format_lines(city, f'{hi} {lo}', desc),
            ]
        else:
            pages = [
                format_lines(city, f'{temp} {feels}', desc, f'{hi} {lo}'),
                format_lines(city, f'{hi} {lo}', desc, f'ZIP {zip_code}', f'{provider_word} {weather_provider.upper()}'),
            ]

        if show_aqi:
            try:
                if weather_provider == 'openmeteo':
                    raw_aqi = _get_openmeteo_air(lat, lon).get('us_aqi')
                    if raw_aqi is None:
                        aqi_num = None
                    else:
                        aqi_num = int(round(float(raw_aqi)))
                    aqi_label = _us_aqi_level(aqi_num)
                    aqi_color = _aqi_color_from_us(aqi_num)
                elif weather_provider == 'weatherapi':
                    raw_aqi = weather.get('weatherapi_aqi')
                    aqi_num = int(raw_aqi) if raw_aqi is not None else None
                    aqi_label = _weatherapi_aqi_level(aqi_num)
                    aqi_color = _aqi_color_from_weatherapi(aqi_num)
                elif weather_provider == 'qweather':
                    aqi_num = _fetch_qweather_aqi(lat, lon)
                    aqi_label = _us_aqi_level(aqi_num)
                    aqi_color = _aqi_color_from_us(aqi_num)
                else:
                    aqi_num = _fetch_openweather_aqi(lat, lon)
                    aqi_label = AQI_LABELS.get(aqi_num, 'UNKNOWN')
                    aqi_color = _aqi_color_from_openweather(aqi_num)

                # Missing/invalid provider value: skip AQI page for this cycle.
                if aqi_num is None or aqi_num <= 0:
                    raise ValueError('AQI unavailable')

                aqi_display = _decorate_status(aqi_label, aqi_color, cols)
                if rows == 1:
                    pages.append(format_lines(f'AQI {aqi_display}'))
                elif rows == 2:
                    pages.append(format_lines(f'AQI {aqi_num}', aqi_display))
                elif rows == 3:
                    pages.append(format_lines(city, f'AQI {aqi_num}', aqi_display))
                else:
                    pages.append(format_lines(city, f'AQI {aqi_num}', aqi_display, f'{provider_word} {weather_provider.upper()}'))
            except Exception:
                pass

        if show_uv:
            try:
                uv_value = None
                if weather_provider in ('openmeteo', 'weatherapi'):
                    uv_value = weather.get('uv')

                if uv_value is not None:
                    uv_num = int(round(float(uv_value)))
                    uv_label = _uv_level(float(uv_value))
                    uv_color = _uv_color(float(uv_value))
                    uv_display = _decorate_status(uv_label, uv_color, cols)
                    if rows == 1:
                        pages.append(format_lines(f'UV {uv_display}'))
                    elif rows == 2:
                        pages.append(format_lines(f'UV {uv_num}', uv_display))
                    elif rows == 3:
                        pages.append(format_lines(city, f'UV {uv_num}', uv_display))
                    else:
                        pages.append(format_lines(city, f'UV {uv_num}', uv_display, sun_exposure_text))
            except Exception:
                pass

        if show_pollen:
            try:
                if weather_provider == 'weatherapi':
                    pollen = weather.get('pollen') or {}
                    grass = pollen.get('grass')
                    birch = pollen.get('tree')
                    ragweed = pollen.get('weed')
                    weed = pollen.get('weed')
                elif weather_provider == 'openmeteo':
                    curr = _get_openmeteo_air(lat, lon)
                    grass = curr.get('grass_pollen')
                    birch = curr.get('birch_pollen')
                    ragweed = curr.get('ragweed_pollen')
                    weed = curr.get('weed_pollen')
                else:
                    grass = None
                    birch = None
                    ragweed = None
                    weed = None

                vals = [v for v in [grass, birch, ragweed, weed] if v is not None]
                if not vals:
                    raise ValueError('Pollen unavailable')

                overall = max(vals) if vals else None
                overall_label = _pollen_level(overall)
                overall_color = _pollen_color(overall)
                grass_label = _pollen_level(grass)
                tree_label = _pollen_level(birch)
                weed_label = _pollen_level(weed or ragweed)
                overall_display = _decorate_status(overall_label, overall_color, cols)
                component_displays = []
                if grass is not None:
                    grass_display = f'{grass_word} {grass_label} {_compact_color(_pollen_color(grass))}'
                    component_displays.append(grass_display)
                if birch is not None:
                    tree_display = f'{tree_word} {tree_label} {_compact_color(_pollen_color(birch))}'
                    component_displays.append(tree_display)
                weed_value = weed or ragweed
                if weed_value is not None:
                    weed_display = f'{weed_word} {weed_label} {_compact_color(_pollen_color(weed_value))}'
                    component_displays.append(weed_display)

                if rows == 1:
                    pages.append(format_lines(f'{pollen_word} {overall_display}'))
                elif rows == 2:
                    pages.append(format_lines(pollen_word, overall_display))
                    if component_displays:
                        pages.append(format_lines(*component_displays))
                elif rows == 3:
                    pages.append(format_lines(city, pollen_word, overall_display))
                    if component_displays:
                        pages.append(format_lines(*component_displays))
                else:
                    pages.append(format_lines(city, pollen_word, overall_display, f'{provider_word} {weather_provider.upper()}'))
                    detail_lines = [city] + component_displays
                    if rows >= 5:
                        detail_lines.append(f'{overall_word} {overall_display}')
                    pages.append(format_lines(*detail_lines))
            except Exception:
                pass

        state['last_pages'] = pages
        state['last_polled_at'] = now_ts
        state['last_sig'] = settings_sig
        return pages
    except Exception:
        # On transient error, reuse last good pages if available
        if state['last_pages'] is not None:
            return state['last_pages']
        return [format_lines('WEATHER', 'ERROR', 'CHECK API KEY')]


def trigger(settings, conditions):
    """Fire on severe weather or when temperature crosses a threshold."""
    import requests

    condition = conditions.get('condition', 'severe')
    threshold_f = float(conditions.get('temp_threshold', 90))
    zip_code = settings.get('zip_code', '02118')

    # Severe weather codes (WMO): thunderstorm, heavy rain, snow, hail
    SEVERE_CODES = {65, 67, 75, 77, 82, 86, 95, 96, 99}

    try:
        # Geocode zip to lat/lon
        geo = requests.get(
            f'https://nominatim.openstreetmap.org/search?postalcode={zip_code}&country=US&format=json&limit=1',
            timeout=5, headers={'User-Agent': 'SplitFlapOS/1.0'}
        ).json()
        if not geo:
            return False
        lat, lon = geo[0]['lat'], geo[0]['lon']

        data = requests.get(
            f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}'
            '&current=temperature_2m,weather_code&temperature_unit=fahrenheit',
            timeout=8
        ).json()
        current = data.get('current', {})
        temp_f = current.get('temperature_2m')
        code = current.get('weather_code')

        if condition == 'severe':
            return int(code or 0) in SEVERE_CODES
        if condition == 'temp_above' and temp_f is not None:
            return float(temp_f) >= threshold_f
        if condition == 'temp_below' and temp_f is not None:
            return float(temp_f) <= threshold_f
    except Exception:
        pass
    return False
