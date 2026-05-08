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
