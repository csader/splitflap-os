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

    game_filter = settings.get('sports_filter', 'all')
    show_league = settings.get('sports_show_league', 'yes') == 'yes'
    compact = settings.get('sports_compact', 'no') == 'yes'

    all_games = []
    for key, info in LEAGUES.items():
        teams_str = settings.get(f'sports_{key}', '').strip()
        if not teams_str:
            continue
        team_filter = [t.strip().upper() for t in teams_str.split(',') if t.strip()]
        show_all = '*' in team_filter
        try:
            games = _fetch_league(key, info, team_filter, show_all, format_lines, get_cols, requests, game_filter)
            all_games.extend(games)
        except Exception as e:
            logging.error(f"ESPN {key} error: {e}")

    if not all_games:
        if any(settings.get(f'sports_{key}', '').strip() for key in LEAGUES):
            filter_labels = {'all': 'ALL', 'live': 'LIVE', 'live+upcoming': 'LIVE/UPCOMING', 'live+final': 'LIVE/FINAL'}
            return [format_lines("SPORTS", "NO GAMES", filter_labels.get(game_filter, 'FOUND'))]
        return [format_lines("SPORTS", "NO TEAMS", "CONFIGURED")]

    if not compact:
        # Standard 1-game-per-page
        if show_league:
            return [g['page'] for g in all_games]
        else:
            cols = get_cols()
            return [g['score_line'][:cols].center(cols) + (' ' * cols) + g['status'][:cols].center(cols) for g in all_games]

    # Compact mode: 2 games per page
    pages = []
    for i in range(0, len(all_games), 2):
        g1 = all_games[i]
        cols = get_cols()
        if i + 1 < len(all_games):
            g2 = all_games[i + 1]
            r1 = g1['score_line'][:cols].center(cols)
            r2 = g2['score_line'][:cols].center(cols)
            s1 = g1['status'][:7].ljust(7)
            s2 = g2['status'][:7].rjust(cols - 7)
            r3 = (s1 + s2)[:cols]
            pages.append(r1 + r2 + r3)
        else:
            r1 = g1['score_line'][:cols].center(cols)
            r2 = ' ' * cols
            r3 = g1['status'][:cols].center(cols)
            pages.append(r1 + r2 + r3)
    return pages

def _fetch_league(key, info, team_filter, show_all, format_lines, get_cols, requests, game_filter):
    from datetime import datetime, timedelta
    # Expand date range to catch recent finals and upcoming games
    start = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
    end = (datetime.now() + timedelta(days=7)).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/{info['path']}/scoreboard?dates={start}-{end}&limit=100"
    data = requests.get(url, timeout=8).json()
    events = data.get('events', [])
    if key == 'pga':
        return [{'page': p, 'score_line': '', 'status': ''} for p in _golf(events, info, format_lines)]
    if key == 'ufc':
        return [{'page': p, 'score_line': '', 'status': ''} for p in _mma(events, info, format_lines)]

    games = _parse_events(events, info, team_filter, show_all, format_lines, get_cols, game_filter)

    # If no games found from scoreboard, check team schedules for most recent game
    if not games and not show_all:
        seen_teams = set()
        for abbr in team_filter:
            if abbr in seen_teams:
                continue
            seen_teams.add(abbr)
            recent = _fetch_last_game(info, abbr, format_lines, get_cols, requests, game_filter)
            if recent:
                games.append(recent)

    return games


def _fetch_last_game(info, team_abbr, format_lines, get_cols, requests, game_filter):
    """Fetch the most recent game for a team via the teams endpoint.
    Always returns the last completed game regardless of filter."""
    import logging
    try:
        teams_url = f"https://site.api.espn.com/apis/site/v2/sports/{info['path']}/teams?limit=500"
        team_id = None
        for page in range(1, 4):
            url = f"{teams_url}&page={page}"
            data = requests.get(url, timeout=8).json()
            batch = data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', [])
            if not batch:
                break
            for entry in batch:
                t = entry.get('team', entry)
                if t.get('abbreviation', '').upper() == team_abbr:
                    team_id = t.get('id')
                    break
            if team_id:
                break
        if not team_id:
            return None

        sched_url = f"https://site.api.espn.com/apis/site/v2/sports/{info['path']}/teams/{team_id}/schedule"
        sched = requests.get(sched_url, timeout=8).json()
        events = sched.get('events', [])

        for event in reversed(events):
            comps = event.get('competitions', [])
            if not comps:
                continue
            comp = comps[0]
            state = comp.get('status', {}).get('type', {}).get('state', 'pre')
            if state != 'post':
                continue
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
            as_ = away.get('score', {})
            hs_ = home.get('score', {})
            a_score = as_.get('displayValue', str(as_)) if isinstance(as_, dict) else str(as_)
            h_score = hs_.get('displayValue', str(hs_)) if isinstance(hs_, dict) else str(hs_)
            score_line = f"{aa} {a_score}  {ha} {h_score}"
            page = format_lines(info['name'], score_line, "FINAL")
            return {'page': page, 'score_line': score_line, 'status': 'FINAL', 'state': 'post'}
        return None
    except Exception as e:
        logging.error(f"Schedule fetch error for {team_abbr}: {e}")
        return None


def _parse_events(events, info, team_filter, show_all, format_lines, get_cols, game_filter):
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

        # Apply game filter
        if game_filter == 'live' and state != 'in':
            continue
        elif game_filter == 'live+upcoming' and state == 'post':
            continue
        elif game_filter == 'live+final' and state == 'pre':
            continue

        if state == 'pre':
            score_line = f"{aa} VS {ha}"
        else:
            score_line = f"{aa} {away.get('score','0')}  {ha} {home.get('score','0')}"
        status = "FINAL" if state == 'post' else detail.upper()[:15]
        page = format_lines(info['name'], score_line, status)
        game = {'page': page, 'score_line': score_line, 'status': status, 'state': state}
        (live if state == 'in' else upcoming if state == 'pre' else final).append(game)
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
