"""Formula 1 — next Grand Prix & championship leader (keyless: Jolpica / Ergast)."""


def fetch(settings, format_lines, get_rows, get_cols, i18n=None):
    import requests
    from datetime import datetime, timezone
    rows, cols = get_rows(), get_cols()

    def t(s, ctx="sports"):
        return i18n.t(s, ctx) if i18n is not None else s

    def u(k):                                 # localized D/H duration suffix
        return i18n.unit(k) if i18n is not None else k

    pages = []
    try:
        nxt = requests.get('https://api.jolpi.ca/ergast/f1/current/next.json', timeout=10).json()
        races = nxt.get('MRData', {}).get('RaceTable', {}).get('Races', [])
        if races:
            r = races[0]
            name = str(r.get('raceName', '')).upper().replace('GRAND PRIX', 'GP')
            cd = ''
            try:
                dt = datetime.fromisoformat(
                    f"{r.get('date', '')}T{r.get('time', '00:00:00Z')}".replace('Z', '+00:00'))
                secs = int((dt - datetime.now(timezone.utc)).total_seconds())
                if secs > 0:
                    d, h = secs // 86400, (secs % 86400) // 3600
                    in_ = t('IN', 'time')
                    cd = f'{in_} {d}{u("D")} {h}{u("H")}' if d else f'{in_} {h}{u("H")}'
                else:
                    cd = t('RACE WEEKEND')
            except ValueError:
                pass
            if rows == 1:
                pages.append(f'{name} {cd}'[:cols].center(cols))
            elif rows == 2:
                pages.append(format_lines(t('NEXT GP'), name))
                pages.append(format_lines(name, cd))
            else:
                pages.append(format_lines(t('NEXT GRAND PRIX'), name, cd))
        else:
            pages.append(format_lines('FORMULA 1', t('SEASON'), t('OVER')))
    except Exception:
        return [format_lines('FORMULA 1', t('OFFLINE'), '')]

    try:
        st = requests.get('https://api.jolpi.ca/ergast/f1/current/driverStandings.json', timeout=10).json()
        lists = st.get('MRData', {}).get('StandingsTable', {}).get('StandingsLists', [])
        ds = lists[0].get('DriverStandings', []) if lists else []
        if ds:
            top = ds[0]
            nm = str(top.get('Driver', {}).get('familyName', '')).upper()
            pts = top.get('points', '')
            if rows == 1:
                pages.append(f'{t("LEADER")} {nm} {pts}'[:cols].center(cols))
            elif rows == 2:
                pages.append(format_lines(t('CHAMPIONSHIP'), f'{nm} {pts}{t("PTS")}'))
            else:
                pages.append(format_lines(t('LEADER'), nm, f'{pts} {t("POINTS")}'))
    except Exception:
        pass
    return pages or [format_lines('FORMULA 1', t('NO DATA'), '')]
