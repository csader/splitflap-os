"""National Today - Holiday of the Day plugin for Split-Flap Display."""

def fetch(settings, format_lines, get_rows, get_cols):
    from datetime import datetime
    import pytz
    import json
    import os

    tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    now = datetime.now(tz)
    key = f'{now.month}/{now.day}'

    # Load bundled holidays
    holidays_path = os.path.join(os.path.dirname(__file__), 'holidays.json')
    try:
        with open(holidays_path) as f:
            holidays = json.load(f)
    except Exception:
        holidays = {}

    names = holidays.get(key, ['A GREAT DAY'])
    pages = []
    for name in names:
        name = name.upper()
        cols = get_cols()
        if len(name) <= cols:
            pages.append(format_lines('TODAY IS', name, ''))
        else:
            words = name.split()
            line1 = ''
            line2 = ''
            for word in words:
                if not line1 or len(line1) + 1 + len(word) <= cols:
                    line1 = (line1 + ' ' + word).strip() if line1 else word
                elif not line2 or len(line2) + 1 + len(word) <= cols:
                    line2 = (line2 + ' ' + word).strip() if line2 else word
            pages.append(format_lines('TODAY IS', line1, line2))

    return pages or [format_lines('TODAY IS', 'A GREAT DAY', '')]
