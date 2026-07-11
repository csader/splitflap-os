"""Upcoming public holidays for your location (keyless: Nager.Date).

Which calendar to show is driven by the configured LOCATION (the language can't tell
France from Canada from Switzerland), down to the province/state: in Quebec you get
Quebec's holidays, not the other provinces'. Names use the source's native localName,
or a localized translation for the common holidays (so a French speaker in Quebec —
where the source only has English — still reads Fête du Travail, Action de grâce…).
An explicit Country setting overrides the location; the Language is the last resort.
"""


def fetch(settings, format_lines, get_rows, get_cols, i18n=None, get_location=None):
    import requests
    from datetime import datetime, date
    rows, cols = get_rows(), get_cols()

    def t(s, ctx="time"):
        return i18n.t(s, ctx) if i18n is not None else s

    loc = (get_location() or {}) if get_location is not None else {}
    country = str(settings.get('country', '') or '').strip().upper()[:2]
    if not country:
        country = str(loc.get('country') or '') or (i18n.country() if i18n is not None else 'US')
    # Province/state (e.g. CA-QC) — only trusted when it belongs to the country we're
    # actually showing (an explicit Country setting can differ from the location).
    subdivision = str(loc.get('subdivision') or '')
    if subdivision and not subdivision.startswith(country):
        subdivision = ''
    try:
        data = requests.get(f'https://date.nager.at/api/v3/NextPublicHolidays/{country}', timeout=8).json()
        if not isinstance(data, list) or not data:
            return [format_lines('HOLIDAYS', 'NONE FOUND', country)]
        # Keep nationwide holidays + the ones for our own province/state; drop other
        # regions' (so Quebec doesn't list British Columbia Day).
        if subdivision:
            data = [h for h in data if h.get('global') or subdivision in (h.get('counties') or [])]
        pages, today = [], date.today()
        for h in data[:4]:
            localized = i18n.holiday(h.get('name')) if i18n is not None else None
            name = str(localized or h.get('localName') or h.get('name') or '').upper()
            cd = ''
            try:
                days = (datetime.strptime(h.get('date', ''), '%Y-%m-%d').date() - today).days
                if days == 0:
                    cd = t('TODAY')
                elif days > 0:
                    cd = f'{t("IN")} {days} {t("DAYS")}'
            except ValueError:
                pass
            if rows == 1:
                pages.append(f'{name} {cd}'[:cols].center(cols))
            elif rows == 2:
                pages.append(format_lines(name, cd))
            else:
                pages.append(format_lines(t('NEXT HOLIDAY', 'holidays'), name, cd))
        return pages or [format_lines('HOLIDAYS', 'NONE', '')]
    except Exception:
        return [format_lines('HOLIDAYS', 'OFFLINE', '')]
