"""Art Clock - time displayed as color pixel art for Split-Flap Display."""

def fetch(settings, format_lines, get_rows, get_cols):
    from datetime import datetime
    import pytz

    tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    now = datetime.now(tz)
    h = now.hour % 12
    if h == 0:
        h = 12
    m = now.minute

    # 3x3 pixel font for digits 0-9 (# = filled, space = empty)
    font = {
        '0': ['###', '# #', '###'],
        '1': [' # ', '## ', ' # '],
        '2': ['###', ' ##', '## '],
        '3': ['###', ' ##', '###'],
        '4': ['# #', '###', '  #'],
        '5': ['###', '## ', '###'],
        '6': ['# #', '## ', '###'],
        '7': ['###', '  #', '  #'],
        '8': ['###', '###', '###'],
        '9': ['###', '###', '  #'],
    }

    colon = [' ', '#', ' ']

    # Color palette cycles with the hour
    colors = ['r', 'o', 'g', 'b', 'p', 'w']
    c1 = colors[h % len(colors)]
    c2 = colors[(h + 3) % len(colors)]

    h_str = f'{h:02d}'
    m_str = f'{m:02d}'

    # Build 3 rows of 15 chars: D D : D D = 3+1+3+1+3+1+3 = 15
    raw = ''
    for row in range(3):
        line = ''
        line += font[h_str[0]][row].replace('#', c1)
        line += ' '
        line += font[h_str[1]][row].replace('#', c1)
        line += colon[row].replace('#', 'w')
        line += font[m_str[0]][row].replace('#', c2)
        line += ' '
        line += font[m_str[1]][row].replace('#', c2)
        raw += line

    return [raw]
