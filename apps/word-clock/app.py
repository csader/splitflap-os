"""Word clock — spells the time out ("IT'S HALF PAST TEN").

Localized into the major Western-European languages when the companion injects
i18n (honoring the global Language). Each language has its own grammar — Romance
languages name the hour first (IL EST DIX HEURES ET QUART), Germanic ones lead
with the minutes (VIERTEL NACH ZEHN), and German/Dutch "half" points at the *next*
hour (HALB DREI = 2:30). Anything without a builder (or a bare host) falls back to
the original English behavior.
"""

# Hour words 1..12 (index 0 unused) and minute-number words 1..29, accent-free to
# match the display's Windows-1252 rendering. Gender follows each language (es
# UNA/UNO for hour/minute, pt UMA/UM).
_HOURS = {
    'fr': ['', 'UNE', 'DEUX', 'TROIS', 'QUATRE', 'CINQ', 'SIX', 'SEPT', 'HUIT', 'NEUF', 'DIX', 'ONZE', 'DOUZE'],
    'de': ['', 'EINS', 'ZWEI', 'DREI', 'VIER', 'FUNF', 'SECHS', 'SIEBEN', 'ACHT', 'NEUN', 'ZEHN', 'ELF', 'ZWOLF'],
    'es': ['', 'UNA', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE', 'DIEZ', 'ONCE', 'DOCE'],
    'it': ['', 'UNA', 'DUE', 'TRE', 'QUATTRO', 'CINQUE', 'SEI', 'SETTE', 'OTTO', 'NOVE', 'DIECI', 'UNDICI', 'DODICI'],
    'pt': ['', 'UMA', 'DUAS', 'TRES', 'QUATRO', 'CINCO', 'SEIS', 'SETE', 'OITO', 'NOVE', 'DEZ', 'ONZE', 'DOZE'],
    'nl': ['', 'EEN', 'TWEE', 'DRIE', 'VIER', 'VIJF', 'ZES', 'ZEVEN', 'ACHT', 'NEGEN', 'TIEN', 'ELF', 'TWAALF'],
}
_MINS = {
    'fr': ['', 'UNE', 'DEUX', 'TROIS', 'QUATRE', 'CINQ', 'SIX', 'SEPT', 'HUIT', 'NEUF', 'DIX', 'ONZE', 'DOUZE',
           'TREIZE', 'QUATORZE', 'QUINZE', 'SEIZE', 'DIX-SEPT', 'DIX-HUIT', 'DIX-NEUF', 'VINGT', 'VINGT ET UNE',
           'VINGT-DEUX', 'VINGT-TROIS', 'VINGT-QUATRE', 'VINGT-CINQ', 'VINGT-SIX', 'VINGT-SEPT', 'VINGT-HUIT', 'VINGT-NEUF'],
    'de': ['', 'EINS', 'ZWEI', 'DREI', 'VIER', 'FUNF', 'SECHS', 'SIEBEN', 'ACHT', 'NEUN', 'ZEHN', 'ELF', 'ZWOLF',
           'DREIZEHN', 'VIERZEHN', 'FUNFZEHN', 'SECHZEHN', 'SIEBZEHN', 'ACHTZEHN', 'NEUNZEHN', 'ZWANZIG', 'EINUNDZWANZIG',
           'ZWEIUNDZWANZIG', 'DREIUNDZWANZIG', 'VIERUNDZWANZIG', 'FUNFUNDZWANZIG', 'SECHSUNDZWANZIG', 'SIEBENUNDZWANZIG',
           'ACHTUNDZWANZIG', 'NEUNUNDZWANZIG'],
    'es': ['', 'UNO', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE', 'DIEZ', 'ONCE', 'DOCE',
           'TRECE', 'CATORCE', 'QUINCE', 'DIECISEIS', 'DIECISIETE', 'DIECIOCHO', 'DIECINUEVE', 'VEINTE', 'VEINTIUNO',
           'VEINTIDOS', 'VEINTITRES', 'VEINTICUATRO', 'VEINTICINCO', 'VEINTISEIS', 'VEINTISIETE', 'VEINTIOCHO', 'VEINTINUEVE'],
    'it': ['', 'UNO', 'DUE', 'TRE', 'QUATTRO', 'CINQUE', 'SEI', 'SETTE', 'OTTO', 'NOVE', 'DIECI', 'UNDICI', 'DODICI',
           'TREDICI', 'QUATTORDICI', 'QUINDICI', 'SEDICI', 'DICIASSETTE', 'DICIOTTO', 'DICIANNOVE', 'VENTI', 'VENTUNO',
           'VENTIDUE', 'VENTITRE', 'VENTIQUATTRO', 'VENTICINQUE', 'VENTISEI', 'VENTISETTE', 'VENTOTTO', 'VENTINOVE'],
    'pt': ['', 'UM', 'DOIS', 'TRES', 'QUATRO', 'CINCO', 'SEIS', 'SETE', 'OITO', 'NOVE', 'DEZ', 'ONZE', 'DOZE',
           'TREZE', 'CATORZE', 'QUINZE', 'DEZESSEIS', 'DEZESSETE', 'DEZOITO', 'DEZENOVE', 'VINTE', 'VINTE E UM',
           'VINTE E DOIS', 'VINTE E TRES', 'VINTE E QUATRO', 'VINTE E CINCO', 'VINTE E SEIS', 'VINTE E SETE',
           'VINTE E OITO', 'VINTE E NOVE'],
    'nl': ['', 'EEN', 'TWEE', 'DRIE', 'VIER', 'VIJF', 'ZES', 'ZEVEN', 'ACHT', 'NEGEN', 'TIEN', 'ELF', 'TWAALF',
           'DERTIEN', 'VEERTIEN', 'VIJFTIEN', 'ZESTIEN', 'ZEVENTIEN', 'ACHTTIEN', 'NEGENTIEN', 'TWINTIG', 'EENENTWINTIG',
           'TWEEENTWINTIG', 'DRIEENTWINTIG', 'VIERENTWINTIG', 'VIJFENTWINTIG', 'ZESENTWINTIG', 'ZEVENENTWINTIG',
           'ACHTENTWINTIG', 'NEGENENTWINTIG'],
}


def _ctx(h):
    """Displayed current hour (1..12) and next hour (1..12)."""
    h12 = h % 12
    disp = 12 if h12 == 0 else h12
    n12 = (h12 + 1) % 12
    dispn = 12 if n12 == 0 else n12
    return disp, dispn


def _b_fr(h, rounded):
    if h == 0 and rounded == 0:
        return ['IL', 'EST', 'MINUIT']
    if h == 12 and rounded == 0:
        return ['IL', 'EST', 'MIDI']
    disp, dispn = _ctx(h)
    H, M = _HOURS['fr'], _MINS['fr']
    heure = lambda d: 'HEURE' if d == 1 else 'HEURES'
    if rounded == 0:
        return ['IL', 'EST', H[disp], heure(disp)]
    if rounded <= 30:
        head = ['IL', 'EST', H[disp], heure(disp)]
        if rounded == 15:
            return head + ['ET', 'QUART']
        if rounded == 30:
            return head + ['ET', 'DEMIE']
        return head + ['ET', M[rounded]]
    mm = 60 - rounded
    head = ['IL', 'EST', H[dispn], heure(dispn)]
    if mm == 15:
        return head + ['MOINS', 'LE', 'QUART']
    return head + ['MOINS', M[mm]]


def _b_de(h, rounded):
    if h == 0 and rounded == 0:
        return ['ES', 'IST', 'MITTERNACHT']
    if h == 12 and rounded == 0:
        return ['ES', 'IST', 'MITTAG']
    disp, dispn = _ctx(h)
    H, M = _HOURS['de'], _MINS['de']
    if rounded == 0:
        return ['ES', 'IST', 'EIN' if disp == 1 else H[disp], 'UHR']
    if rounded <= 30:
        if rounded == 15:
            return ['ES', 'IST', 'VIERTEL', 'NACH', H[disp]]
        if rounded == 30:
            return ['ES', 'IST', 'HALB', H[dispn]]      # halb points at the next hour
        return ['ES', 'IST', M[rounded], 'NACH', H[disp]]
    mm = 60 - rounded
    if mm == 15:
        return ['ES', 'IST', 'VIERTEL', 'VOR', H[dispn]]
    return ['ES', 'IST', M[mm], 'VOR', H[dispn]]


def _b_es(h, rounded):
    if h == 0 and rounded == 0:
        return ['ES', 'MEDIANOCHE']
    if h == 12 and rounded == 0:
        return ['ES', 'MEDIODIA']
    disp, dispn = _ctx(h)
    H, M = _HOURS['es'], _MINS['es']
    pre = lambda d: ['ES', 'LA'] if d == 1 else ['SON', 'LAS']
    if rounded == 0:
        return pre(disp) + [H[disp]]
    if rounded <= 30:
        head = pre(disp) + [H[disp]]
        if rounded == 15:
            return head + ['Y', 'CUARTO']
        if rounded == 30:
            return head + ['Y', 'MEDIA']
        return head + ['Y', M[rounded]]
    mm = 60 - rounded
    head = pre(dispn) + [H[dispn]]
    if mm == 15:
        return head + ['MENOS', 'CUARTO']
    return head + ['MENOS', M[mm]]


def _b_it(h, rounded):
    if h == 0 and rounded == 0:
        return ["E'", 'MEZZANOTTE']
    if h == 12 and rounded == 0:
        return ["E'", 'MEZZOGIORNO']
    disp, dispn = _ctx(h)
    H, M = _HOURS['it'], _MINS['it']
    named = lambda d: ["E'", "L'UNA"] if d == 1 else ['SONO', 'LE', H[d]]
    if rounded == 0:
        return named(disp)
    if rounded <= 30:
        head = named(disp)
        if rounded == 15:
            return head + ['E', 'UN', 'QUARTO']
        if rounded == 30:
            return head + ['E', 'MEZZA']
        return head + ['E', M[rounded]]
    mm = 60 - rounded
    head = named(dispn)
    if mm == 15:
        return head + ['MENO', 'UN', 'QUARTO']
    return head + ['MENO', M[mm]]


def _b_pt(h, rounded):
    if h == 0 and rounded == 0:
        return ["E'", 'MEIA-NOITE']
    if h == 12 and rounded == 0:
        return ["E'", 'MEIO-DIA']
    disp, dispn = _ctx(h)
    H, M = _HOURS['pt'], _MINS['pt']
    if rounded == 0:
        return ["E'", 'UMA', 'HORA'] if disp == 1 else ['SAO', H[disp], 'HORAS']
    if rounded <= 30:
        head = ["E'", 'UMA'] if disp == 1 else ['SAO', H[disp]]
        if rounded == 15:
            return head + ['E', 'QUINZE']
        if rounded == 30:
            return head + ['E', 'MEIA']
        return head + ['E', M[rounded]]
    mm = 60 - rounded
    tail = 'QUINZE' if mm == 15 else M[mm]
    if dispn == 1:
        return [tail, 'PARA', 'A', 'UMA']
    return [tail, 'PARA', 'AS', H[dispn]]


def _b_nl(h, rounded):
    if h == 0 and rounded == 0:
        return ['HET', 'IS', 'MIDDERNACHT']
    if h == 12 and rounded == 0:
        return ['HET', 'IS', 'MIDDAG']
    disp, dispn = _ctx(h)
    H, M = _HOURS['nl'], _MINS['nl']
    if rounded == 0:
        return ['HET', 'IS', H[disp], 'UUR']
    if rounded <= 30:
        if rounded == 15:
            return ['HET', 'IS', 'KWART', 'OVER', H[disp]]
        if rounded == 30:
            return ['HET', 'IS', 'HALF', H[dispn]]      # half points at the next hour
        return ['HET', 'IS', M[rounded], 'OVER', H[disp]]
    mm = 60 - rounded
    if mm == 15:
        return ['HET', 'IS', 'KWART', 'VOOR', H[dispn]]
    return ['HET', 'IS', M[mm], 'VOOR', H[dispn]]


_BUILDERS = {'fr': _b_fr, 'de': _b_de, 'es': _b_es, 'it': _b_it, 'pt': _b_pt, 'nl': _b_nl}


def _wrap(words, cols):
    """Greedily pack words into lines no wider than the display."""
    lines, cur = [], ''
    for w in words:
        cand = w if not cur else f'{cur} {w}'
        if len(cand) <= cols or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _fit(words, cols, rows):
    lines = _wrap(words, cols)
    if rows and rows >= 1 and len(lines) > rows:      # collapse overflow into the last visible row
        lines = lines[:rows - 1] + [' '.join(lines[rows - 1:])]
    return lines


def _english(h, rounded, cols):
    h12 = h % 12
    hours = ['TWELVE', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE',
             'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN', 'ELEVEN']
    ones = ['', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN',
            'ELEVEN', 'TWELVE', 'THIRTEEN', 'FOURTEEN', 'FIFTEEN', 'SIXTEEN', 'SEVENTEEN', 'EIGHTEEN', 'NINETEEN']
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

    hour_word = hours[h12]
    next_word = hours[(h12 + 1) % 12]

    if h == 0 and rounded == 0:
        return ["IT'S", 'MIDNIGHT', '']
    if h == 12 and rounded == 0:
        return ["IT'S", 'NOON', '']
    if rounded == 0:
        return ["IT'S", hour_word, "O'CLOCK"]
    if rounded <= 30:
        mw, direction, target = minute_word(rounded), 'PAST', hour_word
    else:
        mw, direction, target = minute_word(60 - rounded), 'TO', next_word

    combined = mw + ' ' + direction
    if len(combined) <= cols:
        return ["IT'S", combined, target]
    return ["IT'S", mw, direction + ' ' + target]


def fetch(settings, format_lines, get_rows, get_cols, i18n=None):
    from datetime import datetime
    import pytz
    try:
        tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    except pytz.UnknownTimeZoneError:
        tz = pytz.timezone('US/Eastern')
    now = datetime.now(tz)
    h, m = now.hour, now.minute

    try:
        interval = int(settings.get('interval', '5'))
    except (TypeError, ValueError):
        interval = 5
    interval = max(1, min(30, interval))

    rounded = round(m / interval) * interval
    if rounded == 60:
        rounded = 0
        h = (h + 1) % 24

    cols, rows = get_cols(), get_rows()
    lang = (i18n.lang if i18n is not None else 'en')[:2].lower()

    if lang in _BUILDERS:
        lines = _fit(_BUILDERS[lang](h, rounded), cols, rows)
    else:
        lines = _english(h, rounded, cols)
    return [format_lines(*lines)]
