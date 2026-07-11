"""Currency exchange rates via Frankfurter (European Central Bank data, keyless)."""


def fetch(settings, format_lines, get_rows, get_cols, i18n=None, get_location=None):
    import requests
    rows, cols = get_rows(), get_cols()

    # Base currency: an explicit setting wins; otherwise the configured LOCATION
    # decides (a French speaker in Canada wants CAD, in Switzerland CHF — the
    # language can't tell), falling back to the Language only if no location is set.
    base = str(settings.get('base', '') or '').strip().upper()[:3]
    if not base and get_location is not None:
        base = str((get_location() or {}).get('currency') or '')
    if not base:
        base = i18n.base_currency() if i18n is not None else 'USD'
    targets = [t.strip().upper()[:3] for t in str(settings.get('targets', 'EUR,GBP,JPY')).split(',') if t.strip()]
    targets = targets[:8] or ['EUR', 'GBP', 'JPY']

    # Rates use the locale's decimal/grouping (150,25 vs 150.25; 1.350 vs 1,350).
    def n(v, d):
        return i18n.number(v, d) if i18n is not None else f'{v:,.{d}f}'

    def fmt(v):
        return n(v, 3) if v < 10 else (n(v, 2) if v < 1000 else n(v, 0))

    try:
        data = requests.get('https://api.frankfurter.app/latest',
                            params={'from': base, 'to': ','.join(targets)}, timeout=8).json()
        rates = data.get('rates', {})
        if not rates:
            return [format_lines('FX RATES', 'NO DATA', 'CHECK CODES')]

        pairs = [(t, rates[t]) for t in targets if t in rates]
        if rows == 1:
            return [f'1{base}={fmt(v)}{t}'.center(cols)[:cols] for t, v in pairs]
        lines = [f'1 {base} ='] + [f'{t} {fmt(v)}' for t, v in pairs]
        return [format_lines(*lines[i:i + rows]) for i in range(0, len(lines), rows)]
    except Exception:
        return [format_lines('FX RATES', 'OFFLINE', '')]
