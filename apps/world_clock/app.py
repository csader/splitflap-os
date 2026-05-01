def fetch(settings, format_lines, get_rows, get_cols):
    from datetime import datetime
    import pytz
    zones = [s.strip() for s in settings.get('world_clock_zones', 'US/Eastern,US/Pacific,Europe/London').split(',')]
    lines = []
    for z in zones[:get_rows()]:
        tz = pytz.timezone(z)
        now = datetime.now(tz)
        city = z.split('/')[-1].replace('_', ' ').upper()
        lines.append(f'{city} {now.strftime("%I:%M %p")}')
    lines += [''] * (get_rows() - len(lines))
    return [format_lines(*lines)]
