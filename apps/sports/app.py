"""Sports scores via ESPN API — multi-league."""

LEAGUES = {
    'nfl':    {'path': 'football/nfl',                       'name': 'NFL'},
    'nba':    {'path': 'basketball/nba',                     'name': 'NBA'},
    'mlb':    {'path': 'baseball/mlb',                       'name': 'MLB'},
    'nhl':    {'path': 'hockey/nhl',                         'name': 'NHL'},
    'ncaaf':  {'path': 'football/college-football',          'name': 'NCAAF'},
    'ncaab':  {'path': 'basketball/mens-college-basketball', 'name': 'NCAAB'},
    'mls':    {'path': 'soccer/usa.1',                       'name': 'MLS'},
    'epl':    {'path': 'soccer/eng.1',                       'name': 'EPL'},
    'laliga': {'path': 'soccer/esp.1',                       'name': 'LALIGA'},
    'ucl':    {'path': 'soccer/uefa.champions',              'name': 'UCL'},
    'wnba':   {'path': 'basketball/wnba',                    'name': 'WNBA'},
    'ncaaw':  {'path': 'basketball/womens-college-basketball','name': 'NCAAW'},
    'soft':   {'path': 'baseball/college-softball',          'name': 'SOFTBALL'},
    'msoc':   {'path': 'soccer/usa.ncaa.m.1',               'name': 'MSOC'},
    'wsoc':   {'path': 'soccer/usa.ncaa.w.1',               'name': 'WSOC'},
    'pga':    {'path': 'golf/pga',                           'name': 'PGA'},
    'ufc':    {'path': 'mma/ufc',                            'name': 'UFC'},
}

def fetch(settings, format_lines, get_rows, get_cols):
    import requests, logging
    # One-time migration from old nhl_teams key
    if settings.get('nhl_teams') and not settings.get('sports_nhl'):
        settings['sports_nhl'] = settings['nhl_teams']
        settings['nhl_teams'] = ''
    pages = []
    for key, info in LEAGUES.items():
        teams_str = settings.get(f'sports_{key}', '').strip()
        if not teams_str:
            continue
        team_filter = [t.strip().upper() for t in teams_str.split(',') if t.strip()]
        show_all = '*' in team_filter
        try:
            pages.extend(_fetch_league(key, info, team_filter, show_all, format_lines, get_cols, requests))
        except Exception as e:
            logging.error(f"ESPN {key} error: {e}")
    return pages or [format_lines("SPORTS", "NO GAMES", "CONFIGURED")]

def _fetch_league(key, info, team_filter, show_all, format_lines, get_cols, requests):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{info['path']}/scoreboard"
    data = requests.get(url, timeout=8).json()
    events = data.get('events', [])
    if key == 'pga':
        return _golf(events, info, format_lines)
    if key == 'ufc':
        return _mma(events, info, format_lines)
    live, upcoming, final = [], [], []
    for event in events:
        comp = event.get('competitions', [{}])[0]
        competitors = comp.get('competitors', [])
        if len(competitors) < 2:
            continue
        away = home = None
        for c in competitors:
            if c.get('homeAway') == 'home': home = c
            else: away = c
        if not away or not home:
            continue
        aa = away['team'].get('abbreviation', '???').upper()
        ha = home['team'].get('abbreviation', '???').upper()
        if not show_all and aa not in team_filter and ha not in team_filter:
            continue
        state = event.get('status', {}).get('type', {}).get('state', 'pre')
        detail = event.get('status', {}).get('type', {}).get('shortDetail', '')
        if state == 'pre':
            r2 = f"{aa} VS {ha}"
        else:
            r2 = f"{aa} {away.get('score','0')}  {ha} {home.get('score','0')}"
        r3 = "FINAL" if state == 'post' else detail.upper()[:15]
        page = format_lines(info['name'], r2, r3)
        (live if state == 'in' else upcoming if state == 'pre' else final).append(page)
    return live + upcoming + final

def _golf(events, info, format_lines):
    if not events:
        return [format_lines("PGA TOUR", "NO EVENT", "THIS WEEK")]
    comps = events[0].get('competitions', [{}])
    if not comps:
        return [format_lines("PGA TOUR", "NO DATA", "")]
    competitors = comps[0].get('competitors', [])
    competitors.sort(key=lambda c: int(c.get('order', 999)))
    pages = []
    for i in range(0, min(9, len(competitors)), 3):
        chunk = competitors[i:i+3]
        lines = []
        for c in chunk:
            name = c.get('athlete', {}).get('shortName', '?')
            score = c.get('score', {}).get('displayValue', '') if isinstance(c.get('score'), dict) else str(c.get('score', ''))
            lines.append(f"{c.get('order','?')} {name[:8]} {score}"[:15])
        while len(lines) < 3: lines.append('')
        pages.append(format_lines(*lines))
    return pages or [format_lines("PGA TOUR", "NO LEADERS", "")]

def _mma(events, info, format_lines):
    if not events:
        return [format_lines("UFC", "NO EVENT", "SCHEDULED")]
    pages = []
    for comp in events[0].get('competitions', [])[:5]:
        competitors = comp.get('competitors', [])
        if len(competitors) < 2: continue
        n1 = competitors[0].get('athlete', {}).get('shortName', '?').upper()[:7]
        n2 = competitors[1].get('athlete', {}).get('shortName', '?').upper()[:7]
        state = comp.get('status', {}).get('type', {}).get('state', 'pre')
        detail = comp.get('status', {}).get('type', {}).get('shortDetail', '')
        r3 = detail.upper()[:15] if detail else ("LIVE" if state == 'in' else "UPCOMING")
        pages.append(format_lines("UFC", f"{n1} V {n2}", r3))
    return pages or [format_lines("UFC", "NO FIGHTS", "SCHEDULED")]
