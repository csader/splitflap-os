"""Aurora / geomagnetic activity — planetary K-index (NOAA SWPC, keyless)."""


def _label(kp):
    if kp < 3:
        return 'QUIET'
    if kp < 5:
        return 'UNSETTLED'
    if kp < 6:
        return 'MINOR STORM'
    if kp < 7:
        return 'MODERATE'
    if kp < 8:
        return 'STRONG STORM'
    if kp < 9:
        return 'SEVERE STORM'
    return 'EXTREME'


def fetch(settings, format_lines, get_rows, get_cols, i18n=None):
    import requests
    rows = get_rows()

    def t(s):
        return i18n.t(s, "aurora") if i18n is not None else s

    def num(kp):                              # integer Kp shows no decimal
        whole = (kp == int(kp))
        if i18n is not None:
            return i18n.number(kp, decimals=0 if whole else 1, grouping=False)
        return f'{kp:.0f}' if whole else f'{kp:.1f}'

    try:
        data = requests.get('https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json',
                            timeout=8).json()
        if not isinstance(data, list) or not data:
            return [format_lines(t('AURORA'), t('NO DATA'), '')]
        latest = data[-1]
        # The feed is a list of {time_tag, Kp, ...} records (newest last).
        kp = float(latest.get('Kp') if isinstance(latest, dict) else latest[1])
        kps = num(kp)
        label = t(_label(kp))
        if rows == 1:
            return [format_lines(f'{t("AURORA")} KP {kps}')]
        if rows == 2:
            return [format_lines(f'{t("AURORA")} KP {kps}', label)]
        return [format_lines(t('AURORA'), f'KP INDEX {kps}', label)]
    except Exception:
        return [format_lines(t('AURORA'), t('OFFLINE'), '')]
