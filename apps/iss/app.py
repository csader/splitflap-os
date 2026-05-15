def fetch(settings, format_lines, get_rows, get_cols):
    import requests
    try:
        pos = requests.get('http://api.open-notify.org/iss-now.json', timeout=10).json()
        ppl = requests.get('http://api.open-notify.org/astros.json', timeout=10).json()
        lat = pos['iss_position']['latitude']
        lon = pos['iss_position']['longitude']
        num = ppl['number']
        rows = get_rows()
        if rows == 1:
            return [format_lines(f'ISS LAT{lat} LON{lon}')]
        if rows == 2:
            return [format_lines('ISS TRACKER', f'LAT{lat} LON{lon}')]
        return [format_lines('ISS TRACKER', f'LAT {lat} LON {lon}', f'{num} IN SPACE')]
    except Exception:
        return [format_lines('ISS TRACKER', 'ERROR', 'API FAIL')]


def trigger(settings, conditions):
    """Fire when ISS is overhead, or on crew milestone."""
    import requests, math
    from datetime import datetime
    import pytz

    condition_type = conditions.get('condition_type', 'overhead')
    zip_code = settings.get('zip_code', '02118')

    state = getattr(trigger, '_state', None)
    if state is None:
        state = {'last_crew_count': None, 'last_crew_names': None}
        setattr(trigger, '_state', state)

    try:
        if condition_type in ('overhead', 'visible_pass'):
            geo = requests.get(
                f'https://nominatim.openstreetmap.org/search?postalcode={zip_code}&country=US&format=json&limit=1',
                timeout=5, headers={'User-Agent': 'SplitFlapOS/1.0'}
            ).json()
            if not geo:
                return False
            user_lat = float(geo[0]['lat'])
            user_lon = float(geo[0]['lon'])

            pos = requests.get('http://api.open-notify.org/iss-now.json', timeout=5).json()
            iss_lat = float(pos['iss_position']['latitude'])
            iss_lon = float(pos['iss_position']['longitude'])

            R = 6371
            dlat = math.radians(iss_lat - user_lat)
            dlon = math.radians(iss_lon - user_lon)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(user_lat)) * math.cos(math.radians(iss_lat)) * math.sin(dlon/2)**2
            dist = R * 2 * math.asin(math.sqrt(a))

            if dist >= 500:
                return False

            if condition_type == 'visible_pass':
                # Check nighttime and clear sky
                tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
                hour = datetime.now(tz).hour
                is_night = hour >= 20 or hour <= 5

                weather = requests.get(
                    f'https://api.open-meteo.com/v1/forecast?latitude={user_lat}&longitude={user_lon}'
                    '&current=cloud_cover',
                    timeout=5
                ).json()
                cloud_cover = weather.get('current', {}).get('cloud_cover', 100)
                is_clear = cloud_cover <= 30

                return is_night and is_clear

            return True  # overhead, no visibility check

        elif condition_type == 'crew_change':
            ppl = requests.get('http://api.open-notify.org/astros.json', timeout=5).json()
            iss_crew = [p['name'] for p in ppl.get('people', []) if p.get('craft') == 'ISS']
            crew_set = frozenset(iss_crew)

            if state['last_crew_names'] is None:
                state['last_crew_names'] = crew_set
                return False
            if crew_set != state['last_crew_names']:
                state['last_crew_names'] = crew_set
                return True

    except Exception:
        pass
    return False
