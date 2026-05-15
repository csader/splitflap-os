def fetch(settings, format_lines, get_rows, get_cols):
    import requests
    coins = [s.strip() for s in settings.get('crypto_list', 'bitcoin,ethereum,solana').split(',')]
    try:
        r = requests.get(
            'https://api.coingecko.com/api/v3/simple/price',
            params={'ids': ','.join(coins), 'vs_currencies': 'usd', 'include_24hr_change': 'true'},
            timeout=10
        ).json()
    except Exception:
        return [format_lines('CRYPTO', 'ERROR', 'API FAIL')]
    rows = get_rows()
    pages = []
    for i in range(0, len(coins), rows):
        chunk = coins[i:i+rows]
        price_lines, change_lines = [], []
        for c in chunk:
            d = r.get(c, {})
            price = d.get('usd')
            chg = d.get('usd_24h_change')
            sym = c[:5].upper()
            if price is not None:
                price_lines.append(f'{sym} ${price:,.0f}' if price >= 1 else f'{sym} ${price:.4f}')
                icon = '🟩' if (chg or 0) >= 0 else '🟥'
                change_lines.append(f'{sym} {icon}{chg:+.1f}%' if chg is not None else f'{sym} N/A')
            else:
                price_lines.append(f'{sym} ERR')
                change_lines.append(f'{sym} ERR')
        pad = [''] * (rows - len(chunk))
        pages.append(format_lines(*(price_lines + pad)))
        pages.append(format_lines(*(change_lines + pad)))
    return pages or [format_lines('CRYPTO', 'NO DATA', '')]


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
        pass
    return False
