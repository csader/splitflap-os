def fetch(settings, format_lines, get_rows, get_cols):
    from datetime import datetime
    import pytz
    tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    now = datetime.now(tz)
    h = now.hour
    m = now.minute
    h12 = h % 12

    interval = int(settings.get('interval', '5'))

    hours = ['TWELVE', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE',
             'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN', 'ELEVEN']

    ones = ['', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE',
            'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN',
            'ELEVEN', 'TWELVE', 'THIRTEEN', 'FOURTEEN', 'FIFTEEN',
            'SIXTEEN', 'SEVENTEEN', 'EIGHTEEN', 'NINETEEN']
    tens = ['', '', 'TWENTY', 'THIRTY', 'FORTY', 'FIFTY']

    def minute_word(n):
        if n == 0:
            return ''
        if n == 15:
            return 'A QUARTER'
        if n == 30:
            return 'HALF'
        if n < 20:
            return ones[n]
        t, o = divmod(n, 10)
        return (tens[t] + ' ' + ones[o]).strip() if o else tens[t]

    # Round to interval
    rounded = round(m / interval) * interval
    if rounded == 60:
        rounded = 0
        h = (h + 1) % 24
        h12 = h % 12

    hour_word = hours[h12]
    next_word = hours[(h12 + 1) % 12]
    cols = get_cols()

    # Special cases for noon and midnight
    if h == 0 and rounded == 0:
        return [format_lines("IT'S", 'MIDNIGHT', '')]
    if h == 12 and rounded == 0:
        return [format_lines("IT'S", 'NOON', '')]

    if rounded == 0:
        return [format_lines("IT'S", hour_word, "O'CLOCK")]
    elif rounded <= 30:
        mw = minute_word(rounded)
        direction = 'PAST'
        target = hour_word
    else:
        mw = minute_word(60 - rounded)
        direction = 'TO'
        target = next_word

    # Fit into 3 lines: try "MW PAST" on line 2, else split
    combined = mw + ' ' + direction
    if len(combined) <= cols:
        return [format_lines("IT'S", combined, target)]
    else:
        return [format_lines("IT'S", mw, direction + ' ' + target)]
