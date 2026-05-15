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
    """Fire when the ISS is passing overhead (within ~500km)."""
    import requests, math

    try:
        # Get user's approximate location from zip code via geocoding
        zip_code = settings.get('zip_code', '02118')
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

        # Haversine distance in km
        R = 6371
        dlat = math.radians(iss_lat - user_lat)
        dlon = math.radians(iss_lon - user_lon)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(user_lat)) * math.cos(math.radians(iss_lat)) * math.sin(dlon/2)**2
        dist = R * 2 * math.asin(math.sqrt(a))

        return dist < 500  # within ~500km ground track
    except Exception:
        return False
