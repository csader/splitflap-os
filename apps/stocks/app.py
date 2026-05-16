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
    """Fire when any followed ticker moves beyond the configured threshold or hits a price target."""
    import yfinance as yf

    condition_type = conditions.get('condition_type', 'pct_change')
    tickers = [s.strip() for s in settings.get('stocks_list', '').split(',') if s.strip()]
    if not tickers:
        return False

    state = getattr(trigger, '_state', None)
    if state is None:
        state = {'fired_targets': set()}
        setattr(trigger, '_state', state)

    try:
        for sym in tickers:
            t = yf.Ticker(sym)
            info = t.fast_info
            price = info['lastPrice']
            prev = info['previousClose']

            if condition_type == 'pct_change':
                threshold = float(conditions.get('threshold', 3))
                direction = conditions.get('direction', 'either')
                if not prev:
                    continue
                chg = ((price - prev) / prev) * 100
                if direction == 'up' and chg >= threshold:
                    return True
                if direction == 'down' and chg <= -threshold:
                    return True
                if direction == 'either' and abs(chg) >= threshold:
                    return True

            elif condition_type == 'price_target':
                target = float(conditions.get('price_target', 0))
                direction = conditions.get('direction', 'above')
                if not target:
                    continue
                key = f"{sym}:{direction}:{target}"
                crossed = (direction == 'above' and price >= target) or \
                          (direction == 'below' and price <= target)
                if crossed and key not in state['fired_targets']:
                    state['fired_targets'].add(key)
                    return True
                if not crossed and key in state['fired_targets']:
                    state['fired_targets'].discard(key)  # reset when price moves away

            elif condition_type == '52w_extreme':
                extreme = conditions.get('extreme', 'high')
                try:
                    hist = yf.Ticker(sym).history(period='1y')
                    if hist.empty:
                        continue
                    week52_high = hist['High'].max()
                    week52_low = hist['Low'].min()
                    key_h = f"{sym}:52wh"
                    key_l = f"{sym}:52wl"
                    if extreme in ('high', 'either') and price >= week52_high * 0.995:
                        if key_h not in state['fired_targets']:
                            state['fired_targets'].add(key_h)
                            return True
                    else:
                        state['fired_targets'].discard(key_h)
                    if extreme in ('low', 'either') and price <= week52_low * 1.005:
                        if key_l not in state['fired_targets']:
                            state['fired_targets'].add(key_l)
                            return True
                    else:
                        state['fired_targets'].discard(key_l)
                except Exception:
                    continue

            elif condition_type == 'market_hours':
                from datetime import datetime
                import pytz
                event = conditions.get('market_event', 'open')
                et = pytz.timezone('US/Eastern')
                now = datetime.now(et)
                # Skip weekends
                if now.weekday() >= 5:
                    return False
                hour, minute = now.hour, now.minute
                key = f"market:{event}:{now.strftime('%Y-%m-%d')}"
                if event == 'open' and hour == 9 and 30 <= minute < 35:
                    if key not in state['fired_targets']:
                        state['fired_targets'].add(key)
                        return True
                elif event == 'close' and hour == 16 and minute < 5:
                    if key not in state['fired_targets']:
                        state['fired_targets'].add(key)
                        return True
                return False

    except Exception:
        pass
    return False
