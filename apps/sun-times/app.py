"""Sunrise / sunset / day length for the configured location (keyless: Open-Meteo).

Times track the location: Open-Meteo returns them in the place's own local time
(timezone=auto), just like the weather app — no separate timezone setting needed."""


def _latlon(settings, requests):
    """Global precise location, else geocode of the ZIP, else a Boston fallback."""
    lat = str(settings.get('location_lat', '') or '').strip()
    lon = str(settings.get('location_lon', '') or '').strip()
    if lat and lon:
        try:
            return float(lat), float(lon)
        except ValueError:
            pass
    zip_code = str(settings.get('zip_code', '02118') or '02118').strip()
    try:
        import re
        params = {'q': zip_code, 'format': 'json', 'limit': 1}
        if re.fullmatch(r'\d{5}', zip_code):     # a US ZIP — disambiguate (02118 also exists abroad)
            params['countrycodes'] = 'us'
        geo = requests.get('https://nominatim.openstreetmap.org/search', params=params,
                           headers={'User-Agent': 'SplitFlapGatewayCompanion/1.0'},
                           timeout=6).json()
        if geo:
            return float(geo[0]['lat']), float(geo[0]['lon'])
    except Exception:
        pass
    return 42.3601, -71.0589


def fetch(settings, format_lines, get_rows, get_cols, i18n=None):
    import requests
    from datetime import datetime
    rows, cols = get_rows(), get_cols()

    def t(s):
        return i18n.t(s, "sun") if i18n is not None else s

    def u(k):                               # localized H/M duration suffix (Dutch U for uur, etc.)
        return i18n.unit(k) if i18n is not None else k

    def line(label, value):                 # label trimmed to fit — never the time
        return f'{label[:max(1, cols - len(value) - 1)]} {value}'

    def fmt_time(iso):                       # ISO is already the location's local time
        if not iso:
            return '--:--'
        dt = datetime.fromisoformat(str(iso))
        # AM/PM is English-only — everyone else gets 24h.
        if i18n is not None:
            return i18n.time(dt, ampm_space=False)
        return dt.strftime('%I:%M%p').lstrip('0')

    try:
        lat, lon = _latlon(settings, requests)
        data = requests.get('https://api.open-meteo.com/v1/forecast',
                            params={'latitude': lat, 'longitude': lon,
                                    'daily': 'sunrise,sunset,daylight_duration',
                                    'timezone': 'auto', 'forecast_days': 1},
                            timeout=8).json()
        daily = data.get('daily', {})
        rise = fmt_time((daily.get('sunrise') or [None])[0])
        sett = fmt_time((daily.get('sunset') or [None])[0])
        secs = int((daily.get('daylight_duration') or [0])[0] or 0)
        length = f'{secs // 3600}{u("H")}{(secs % 3600) // 60:02d}{u("M")}'
        if rows == 1:
            return [format_lines(f'{t("UP")} {rise} {t("DN")} {sett}')]
        if rows == 2:
            return [format_lines(line(t('SUNRISE'), rise), line(t('SUNSET'), sett))]
        return [format_lines(line(t('SUNRISE'), rise), line(t('SUNSET'), sett),
                             line(t('DAYLIGHT'), length))]
    except Exception:
        return [format_lines('SUN TIMES', 'OFFLINE', '')]
