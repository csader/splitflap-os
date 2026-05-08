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
