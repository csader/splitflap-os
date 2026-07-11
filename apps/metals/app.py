"""Precious metal spot prices, USD per troy ounce (keyless: gold-api.com)."""


def fetch(settings, format_lines, get_rows, get_cols, i18n=None, get_location=None):
    import requests
    rows, cols = get_rows(), get_cols()

    def t(s):
        return i18n.t(s, "metals") if i18n is not None else s

    def n(v, d):        # locale decimal/grouping (2,345 vs 2.345 vs 2 345)
        return i18n.number(v, d) if i18n is not None else f'{v:,.{d}f}'

    # gold-api.com quotes in USD/oz; show the local currency (Location -> Language ->
    # USD) by converting through a keyless ECB rate. Falls back to USD if no rate.
    loc = get_location() if get_location is not None else None
    ccy = loc.get('currency') if isinstance(loc, dict) and loc.get('ok') else None
    if not ccy and i18n is not None:
        ccy = i18n.base_currency()
    ccy = (ccy or 'USD').upper()
    rate = 1.0
    if ccy != 'USD':
        try:
            rate = float(requests.get('https://api.frankfurter.app/latest',
                                      params={'from': 'USD', 'to': ccy}, timeout=8).json()['rates'][ccy])
        except Exception:
            ccy, rate = 'USD', 1.0
    # With i18n the display can render € £ ¥ (Windows-1252); without it the modules
    # are the basic charset, so use '$' for USD and the ASCII ISO code otherwise.
    cur_sym = i18n.currency_symbol(ccy) if i18n is not None else ('$' if ccy == 'USD' else ccy)
    sep = '' if cur_sym != ccy else ' '

    def price(sym):
        try:
            return requests.get(f'https://api.gold-api.com/price/{sym}', timeout=8).json().get('price')
        except Exception:
            return None

    def fmt(p):
        if not isinstance(p, (int, float)):
            return '--'
        p = p * rate
        body = n(p, 0) if p >= 100 else n(p, 2)
        return f'{cur_sym}{sep}{body}'

    try:
        gold, silver = price('XAU'), price('XAG')
        if gold is None and silver is None:
            return [format_lines('METALS', t('OFFLINE'), '')]
        # Localized names vary in length — pad both to the same width so they align.
        g, s = t('GOLD'), t('SILVER')
        w = max(len(g), len(s))
        if rows == 1:
            pages = []
            if gold is not None:
                pages.append(f'{g} {fmt(gold)}/OZ'[:cols].center(cols))
            if silver is not None:
                pages.append(f'{s} {fmt(silver)}/OZ'[:cols].center(cols))
            return pages
        if rows == 2:
            return [format_lines(f'{g:<{w}} {fmt(gold)}', f'{s:<{w}} {fmt(silver)}')]
        return [format_lines(f'{t("SPOT PRICE")} /OZ', f'{g:<{w}} {fmt(gold)}', f'{s:<{w}} {fmt(silver)}')]
    except Exception:
        return [format_lines('METALS', t('OFFLINE'), '')]
