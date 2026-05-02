def fetch(settings, format_lines, get_rows, get_cols):
    from datetime import datetime
    import pytz
    tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    now = datetime.now(tz)
    h = now.hour
    m = now.minute
    h12 = h % 12

    hours = ['TWELVE', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE',
             'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN', 'ELEVEN']

    rounded = round(m / 5) * 5
    if rounded == 60:
        rounded = 0
        h = (h + 1) % 24
        h12 = h % 12

    hour_word = hours[h12]
    next_word = hours[(h12 + 1) % 12]

    # Special cases for noon and midnight
    if h == 0 and rounded == 0:
        return [format_lines("IT'S", 'MIDNIGHT', '')]
    if h == 12 and rounded == 0:
        return [format_lines("IT'S", 'NOON', '')]

    if rounded == 0:
        return [format_lines("IT'S", hour_word, "O'CLOCK")]
    elif rounded == 5:
        return [format_lines("IT'S", 'FIVE PAST', hour_word)]
    elif rounded == 10:
        return [format_lines("IT'S", 'TEN PAST', hour_word)]
    elif rounded == 15:
        return [format_lines("IT'S", 'A QUARTER PAST', hour_word)]
    elif rounded == 20:
        return [format_lines("IT'S", 'TWENTY PAST', hour_word)]
    elif rounded == 25:
        return [format_lines("IT'S", 'TWENTY FIVE', 'PAST ' + hour_word)]
    elif rounded == 30:
        return [format_lines("IT'S", 'HALF PAST', hour_word)]
    elif rounded == 35:
        return [format_lines("IT'S", 'TWENTY FIVE TO', next_word)]
    elif rounded == 40:
        return [format_lines("IT'S", 'TWENTY TO', next_word)]
    elif rounded == 45:
        return [format_lines("IT'S", 'A QUARTER TO', next_word)]
    elif rounded == 50:
        return [format_lines("IT'S", 'TEN TO', next_word)]
    elif rounded == 55:
        return [format_lines("IT'S", 'FIVE TO', next_word)]
    return [format_lines("IT'S", hour_word, "O'CLOCK")]
