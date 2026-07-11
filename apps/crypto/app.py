def fetch(settings, format_lines, get_rows, get_cols, i18n=None, get_location=None):
    import requests

    def t(s):
        return i18n.t(s, "crypto") if i18n is not None else s

    coins = [s.strip() for s in settings.get('crypto_list', '').split(',') if s.strip()]
    if not coins:
        return [format_lines('CRYPTO', t('NO COINS'), t('CONFIGURE'))]

    # Price in the local currency: where you are (Location) -> your Language -> USD.
    # CoinGecko quotes natively in the target currency, so no FX conversion is needed.
    loc = get_location() if get_location is not None else None
    ccy = loc.get('currency') if isinstance(loc, dict) and loc.get('ok') else None
    if not ccy and i18n is not None:
        ccy = i18n.base_currency()
    ccy = (ccy or 'USD').upper()
    vs = ccy.lower()
    # With i18n the display can render € £ ¥ (Windows-1252); without it the modules
    # are the basic charset, so use '$' for USD and the ASCII ISO code otherwise.
    cur_sym = i18n.currency_symbol(ccy) if i18n is not None else ('$' if ccy == 'USD' else ccy)
    sep = '' if cur_sym != ccy else ' '    # 3-letter-code fallback reads better spaced

    try:
        r = requests.get(
            'https://api.coingecko.com/api/v3/simple/price',
            params={'ids': ','.join(coins), 'vs_currencies': vs, 'include_24hr_change': 'true'},
            timeout=10
        ).json()
    except Exception:
        return [format_lines('CRYPTO', t('ERROR'), t('API FAIL'))]
    rows, cols = get_rows(), get_cols()
    no_color = settings.get('disable_colors', 'no') == 'yes'

    # Numbers follow the global Language (1,234.50 vs 1.234,50 vs 1 234,50).
    def n(v, d=2, grouping=True):
        if i18n is not None:
            return i18n.number(v, d, grouping)
        return f'{v:,.{d}f}' if grouping else f'{v:.{d}f}'

    def pct(v):
        return f"{'+' if v >= 0 else '-'}{n(abs(v), 1, grouping=False)}%"

    def price_str(price):
        body = n(price, 0) if price >= 1 else n(price, 4, grouping=False)
        return f'{cur_sym}{sep}{body}'

    def block(c):
        """The lines for one coin, sized to the display: price+change together on
        2+ row displays (with the name too when there are 3+ rows)."""
        d = r.get(c, {})
        price, chg = d.get(vs), d.get(f'{vs}_24h_change')
        sym = c[:6].upper()
        if price is None:
            return [f'{sym} ERR']
        if chg is None:
            chg_str = 'N/A'
        elif no_color:
            chg_str = pct(chg)
        else:
            chg_str = ('🟩' if chg >= 0 else '🟥') + f' {pct(chg)}'
        if rows == 1:
            return [f'{sym} {price_str(price)}']
        if rows == 2:
            return [f'{sym} {price_str(price)}', chg_str]
        return [c.upper()[:cols], price_str(price), chg_str]   # name / price / change

    lines_per = 1 if rows == 1 else (2 if rows == 2 else 3)
    per_page = max(1, rows // lines_per)   # how many coins fit on one page
    pages = []
    for i in range(0, len(coins), per_page):
        lines = []
        for c in coins[i:i + per_page]:
            b = block(c)
            lines += b + [''] * (lines_per - len(b))   # pad each block so coins align
        pages.append(format_lines(*lines))
    return pages or [format_lines('CRYPTO', t('NO DATA'), '')]


def trigger(settings, conditions):
    """Fire when any followed coin moves beyond threshold or hits a price target."""
    import requests

    condition_type = conditions.get('condition_type', 'pct_change')
    coins = [s.strip() for s in settings.get('crypto_list', '').split(',') if s.strip()]
    if not coins:
        return False

    state = getattr(trigger, '_state', None)
    if state is None:
        state = {'fired_targets': set()}
        setattr(trigger, '_state', state)

    try:
        r = requests.get(
            'https://api.coingecko.com/api/v3/simple/price',
            params={'ids': ','.join(coins), 'vs_currencies': 'usd', 'include_24hr_change': 'true'},
            timeout=10
        ).json()

        for c in coins:
            d = r.get(c, {})
            price = d.get('usd')
            chg = d.get('usd_24h_change')

            if condition_type == 'pct_change':
                threshold = float(conditions.get('threshold', 5))
                direction = conditions.get('direction', 'either')
                if chg is None:
                    continue
                if direction == 'up' and chg >= threshold:
                    return True
                if direction == 'down' and chg <= -threshold:
                    return True
                if direction == 'either' and abs(chg) >= threshold:
                    return True

            elif condition_type == 'price_target' and price is not None:
                target = float(conditions.get('price_target', 0))
                direction = conditions.get('direction', 'above')
                if not target:
                    continue
                key = f"{c}:{direction}:{target}"
                crossed = (direction == 'above' and price >= target) or \
                          (direction == 'below' and price <= target)
                if crossed and key not in state['fired_targets']:
                    state['fired_targets'].add(key)
                    return True
                if not crossed:
                    state['fired_targets'].discard(key)

    except Exception:
        raise
    return False
