"""Today's tide predictions for a NOAA station (keyless: NOAA CO-OPS)."""


def fetch(settings, format_lines, get_rows, get_cols, i18n=None):
    import requests
    from datetime import datetime
    rows, cols = get_rows(), get_cols()

    def t(s):
        return i18n.t(s, "tides") if i18n is not None else s

    def fmt_time(hhmm):                       # NOAA gives 24h local time ("15:48")
        try:
            dt = datetime.strptime(hhmm, '%H:%M')
        except ValueError:
            return hhmm
        # AM/PM is English-only — everyone else gets 24h.
        if i18n is not None:
            return i18n.time(dt, ampm_space=False)
        return dt.strftime('%I:%M%p').lstrip('0')

    station = str(settings.get('tide_station', '8443970') or '8443970').strip()
    try:
        data = requests.get(
            'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter',
            params={'product': 'predictions', 'application': 'SplitFlapCompanion',
                    'datum': 'MLLW', 'station': station, 'time_zone': 'lst_ldt',
                    'units': 'english', 'interval': 'hilo', 'format': 'json', 'date': 'today'},
            timeout=8).json()
        preds = data.get('predictions') or []
        if not preds:
            return [format_lines(t('TIDES'), t('NO DATA'), t('CHECK STATION'))]
        pages = []
        for p in preds[:6]:
            raw = str(p.get('t', ''))
            hhmm = fmt_time(raw.split(' ')[-1] if ' ' in raw else raw)
            is_high = p.get('type') == 'H'
            v = str(p.get('v', ''))
            if rows == 1:
                # Compact single row: the short generic high/low word keeps the
                # time + height on one line (the full "X TIDE" would crowd them out).
                kind = t('HIGH') if is_high else t('LOW')
                pages.append(f'{kind} {hhmm} {v}FT'[:cols].center(cols))
            elif rows == 2:
                kind = t('HIGH TIDE') if is_high else t('LOW TIDE')
                pages.append(format_lines(kind, f'{hhmm}  {v}FT'))
            else:
                kind = t('HIGH TIDE') if is_high else t('LOW TIDE')
                pages.append(format_lines(kind, hhmm, f'{v} FT'))
        return pages or [format_lines(t('TIDES'), t('NO DATA'), '')]
    except Exception:
        return [format_lines(t('TIDES'), t('OFFLINE'), '')]
