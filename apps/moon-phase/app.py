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


def trigger(settings, conditions):
    """Fire on full moon or new moon."""
    from datetime import datetime
    import pytz, math

    phase_type = conditions.get('phase', 'full')
    tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    now = datetime.now(tz)

    ref = datetime(2000, 1, 6, 18, 14, 0, tzinfo=pytz.utc)
    diff = (now.astimezone(pytz.utc) - ref).total_seconds()
    synodic = 29.53058867
    days_into_cycle = (diff / 86400) % synodic

    state = getattr(trigger, '_state', None)
    if state is None:
        state = {'fired_phase': None}
        setattr(trigger, '_state', state)

    # Full moon: days 13.5–15.5 into cycle; new moon: days 0–1 or 28.5–29.5
    if phase_type == 'full':
        in_phase = 13.5 <= days_into_cycle <= 15.5
    else:  # new
        in_phase = days_into_cycle <= 1.0 or days_into_cycle >= 28.5

    phase_key = f"{phase_type}:{int(days_into_cycle)}"
    if in_phase and state['fired_phase'] != phase_key:
        state['fired_phase'] = phase_key
        return True
    if not in_phase:
        state['fired_phase'] = None  # reset so next occurrence fires
    return False
