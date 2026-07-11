"""Today on Wikipedia — featured article & most-read (keyless: Wikimedia REST)."""


def _wrap(text, cols, maxlines):
    words, lines, cur = text.split(), [], ''
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= cols:
            cur = f'{cur} {w}'.strip()
        else:
            lines.append(cur)
            cur = w[:cols]
            if len(lines) >= maxlines:
                break
    if cur and len(lines) < maxlines:
        lines.append(cur)
    return lines[:maxlines] or ['']


def fetch(settings, format_lines, get_rows, get_cols, i18n=None):
    import requests
    from datetime import datetime
    import pytz
    rows, cols = get_rows(), get_cols()

    def t(s):
        return i18n.t(s, "content") if i18n is not None else s

    # Pull from the language's own Wikipedia edition (fr.wikipedia, de.wikipedia, …);
    # the English variants all use en.wikipedia. Defaults to (American) English.
    wl = i18n.lang_base if i18n is not None else 'en'
    try:
        try:
            tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
        except pytz.UnknownTimeZoneError:
            tz = pytz.timezone('US/Eastern')
        now = datetime.now(tz)
        d = requests.get(f'https://{wl}.wikipedia.org/api/rest_v1/feed/featured/{now:%Y/%m/%d}',
                         headers={'User-Agent': 'SplitFlapGatewayCompanion/1.0'}, timeout=10).json()
        pages = []
        tfa = d.get('tfa') or {}
        title = str(tfa.get('normalizedtitle', '') or '').upper()
        if title:
            if rows == 1:
                pages.append(f'WIKI {title}'[:cols].center(cols))
            else:
                pages.append(format_lines(f'WIKI {t("FEATURED")}', *_wrap(title, cols, rows - 1)))
        for a in ((d.get('mostread') or {}).get('articles', []) or [])[:3]:
            art = str(a.get('normalizedtitle', '') or '').upper()
            if not art:
                continue
            if rows == 1:
                pages.append(f'WIKI {art}'[:cols].center(cols))
            else:
                pages.append(format_lines(f'WIKI {t("MOST READ")}', *_wrap(art, cols, rows - 1)))
        return pages or [format_lines('WIKIPEDIA', 'NO DATA', '')]
    except Exception:
        return [format_lines('WIKIPEDIA', 'OFFLINE', '')]
