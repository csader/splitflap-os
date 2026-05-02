def fetch(settings, format_lines, get_rows, get_cols):
    from datetime import datetime
    import pytz
    import math

    tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    now = datetime.now(tz)

    # Known new moon: January 6, 2000 18:14 UTC
    ref = datetime(2000, 1, 6, 18, 14, 0, tzinfo=pytz.utc)
    diff = (now.astimezone(pytz.utc) - ref).total_seconds()
    synodic = 29.53058867
    days_into_cycle = (diff / 86400) % synodic

    # Phase name
    phase_idx = int(days_into_cycle / (synodic / 8))
    phases = [
        'NEW MOON', 'WAXING CRESCENT', 'FIRST QUARTER', 'WAXING GIBBOUS',
        'FULL MOON', 'WANING GIBBOUS', 'LAST QUARTER', 'WANING CRESCENT'
    ]
    phase_name = phases[phase_idx % 8]

    # Illumination percentage
    illumination = (1 - math.cos(2 * math.pi * days_into_cycle / synodic)) / 2
    illum_pct = int(illumination * 100)

    # Days to next full and new moon
    full_moon_day = synodic / 2
    if days_into_cycle < full_moon_day:
        days_to_full = full_moon_day - days_into_cycle
    else:
        days_to_full = synodic - days_into_cycle + full_moon_day
    days_to_new = synodic - days_into_cycle

    cols = get_cols()

    # Visual bar: w for illuminated, space for dark
    filled = int(illumination * cols)
    bar = 'w' * filled + ' ' * (cols - filled)

    pages = [
        format_lines(phase_name, f'{illum_pct}% LIT', f'FULL IN {int(days_to_full)}D'),
        format_lines(phase_name, bar, f'NEW IN {int(days_to_new)}D'),
    ]
    return pages
