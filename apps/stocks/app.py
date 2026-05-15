def fetch(settings, format_lines, get_rows, get_cols):
    import yfinance as yf
    tickers = [s.strip() for s in settings.get('stocks_list', 'MSFT,GOOG,NVDA').split(',')]
    rows = get_rows()
    pages = []
    for i in range(0, len(tickers), rows):
        chunk = tickers[i:i+rows]
        price_lines, change_lines = [], []
        for sym in chunk:
            try:
                t = yf.Ticker(sym)
                info = t.fast_info
                price = info['lastPrice']
                prev = info['previousClose']
                chg = ((price - prev) / prev) * 100
                icon = '🟩' if chg >= 0 else '🟥'
                price_lines.append(f'{sym} ${price:.2f}')
                change_lines.append(f'{sym} {icon}{chg:+.1f}%')
            except Exception:
                price_lines.append(f'{sym} ERR')
                change_lines.append(f'{sym} ERR')
        pad = [''] * (rows - len(chunk))
        pages.append(format_lines(*(price_lines + pad)))
        pages.append(format_lines(*(change_lines + pad)))
    return pages or [format_lines('STOCKS', 'NO DATA', '')]


def trigger(settings, conditions):
    """Fire when any followed ticker moves beyond the configured threshold."""
    import yfinance as yf

    threshold = float(conditions.get('threshold', 3))
    direction = conditions.get('direction', 'either')
    tickers = [s.strip() for s in settings.get('stocks_list', '').split(',') if s.strip()]
    if not tickers:
        return False

    try:
        for sym in tickers:
            t = yf.Ticker(sym)
            info = t.fast_info
            price = info['lastPrice']
            prev = info['previousClose']
            if not prev:
                continue
            chg = ((price - prev) / prev) * 100
            if direction == 'up' and chg >= threshold:
                return True
            if direction == 'down' and chg <= -threshold:
                return True
            if direction == 'either' and abs(chg) >= threshold:
                return True
    except Exception:
        pass
    return False
