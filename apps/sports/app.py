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

    rows = get_rows()
    cols = get_cols()

    if rows == 1:
        # Just score line
        return [g['score_line'][:cols].center(cols) for g in all_games]

    if not compact:
        if rows == 2:
            # score + status, no league name
            return [g['score_line'][:cols].center(cols) + g['status'][:cols].center(cols) for g in all_games]
        # 3+ rows: standard layout
        if show_league:
            return [g['page'] for g in all_games]
        else:
            return [g['score_line'][:cols].center(cols) + (' ' * cols) + g['status'][:cols].center(cols) for g in all_games]

    # Compact mode: games_per_page = rows - 1 (leave 1 row for statuses), min 1
    games_per_page = max(1, rows - 1)
    pages = []
    for i in range(0, len(all_games), games_per_page):
        chunk = all_games[i:i+games_per_page]
        score_rows = [g['score_line'][:cols].center(cols) for g in chunk]
        # pad to games_per_page
        while len(score_rows) < games_per_page:
            score_rows.append(' ' * cols)
        if rows > games_per_page:
            # status row
            statuses = [g['status'][:max(1, cols // games_per_page)] for g in chunk]
            status_row = ''.join(s.ljust(cols // games_per_page) for s in statuses)[:cols]
            pages.append(''.join(score_rows) + status_row)
        else:
            pages.append(''.join(score_rows))
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


def trigger(settings, conditions):
    """Fire when a followed team's game matches the configured event condition."""
    import requests
    from datetime import datetime, timedelta

    event_type = conditions.get('event', 'game_start')
    teams_str = conditions.get('teams', '').strip()
    trigger_teams = {t.strip().upper() for t in teams_str.split(',') if t.strip()} if teams_str else None

    # Build set of all followed teams if no specific teams configured
    if not trigger_teams:
        trigger_teams = set()
        for key in LEAGUES:
            val = settings.get(f'sports_{key}', '').strip()
            if val and val != '*':
                trigger_teams.update(t.strip().upper() for t in val.split(',') if t.strip())
            elif val == '*':
                trigger_teams.add('*')  # follow-all league

    if not trigger_teams:
        return False

    state_obj = getattr(trigger, '_state', None)
    if state_obj is None:
        state_obj = {'seen_game_ids': set(), 'last_scores': {}}
        setattr(trigger, '_state', state_obj)

    try:
        start = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        end = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d')
        for key, info in LEAGUES.items():
            if key in ('pga', 'ufc'):
                continue
            teams_setting = settings.get(f'sports_{key}', '').strip()
            if not teams_setting:
                continue
            url = f"https://site.api.espn.com/apis/site/v2/sports/{info['path']}/scoreboard?dates={start}-{end}&limit=50"
            data = requests.get(url, timeout=8).json()
            for event in data.get('events', []):
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
                aa = away['team'].get('abbreviation', '').upper()
                ha = home['team'].get('abbreviation', '').upper()
                if '*' not in trigger_teams and aa not in trigger_teams and ha not in trigger_teams:
                    continue
                game_id = event.get('id', '')
                state = event.get('status', {}).get('type', {}).get('state', 'pre')
                a_score = int(away.get('score', 0) or 0)
                h_score = int(home.get('score', 0) or 0)
                score_key = f"{game_id}"

                if event_type == 'game_start':
                    if state == 'in' and game_id not in state_obj['seen_game_ids']:
                        state_obj['seen_game_ids'].add(game_id)
                        return True

                elif event_type == 'score_change':
                    if state == 'in':
                        prev = state_obj['last_scores'].get(score_key)
                        curr = (a_score, h_score)
                        state_obj['last_scores'][score_key] = curr
                        if prev and prev != curr:
                            return True

                elif event_type == 'close_game':
                    if state == 'in' and abs(a_score - h_score) <= 5:
                        if score_key not in state_obj['seen_game_ids']:
                            state_obj['seen_game_ids'].add(score_key)
                            return True

                elif event_type == 'final':
                    if state == 'post' and game_id not in state_obj['seen_game_ids']:
                        state_obj['seen_game_ids'].add(game_id)
                        return True

                elif event_type == 'overtime':
                    detail = event.get('status', {}).get('type', {}).get('shortDetail', '').upper()
                    ot_keywords = ('OT', 'OVERTIME', 'EXTRA', 'SHOOTOUT', 'PENALTY')
                    if state == 'in' and any(k in detail for k in ot_keywords):
                        ot_key = f"ot_{game_id}"
                        if ot_key not in state_obj['seen_game_ids']:
                            state_obj['seen_game_ids'].add(ot_key)
                            return True

                elif event_type == 'playoff':
                    notes = comp.get('notes', [])
                    is_playoff = any('playoff' in str(n).lower() or 'postseason' in str(n).lower() for n in notes)
                    if not is_playoff:
                        season_type = event.get('season', {}).get('type', 2)
                        is_playoff = season_type in (3, 4)  # 3=postseason, 4=offseason
                    if is_playoff and state == 'in' and game_id not in state_obj['seen_game_ids']:
                        state_obj['seen_game_ids'].add(game_id)
                        return True

                elif event_type == 'comeback':
                    if state == 'in':
                        margin = int(conditions.get('comeback_margin', 10))
                        prev = state_obj['last_scores'].get(score_key)
                        curr = (a_score, h_score)
                        state_obj['last_scores'][score_key] = curr
                        if prev:
                            # Check if a team was down by margin and is now within 3
                            prev_diff = prev[0] - prev[1]
                            curr_diff = curr[0] - curr[1]
                            # Away was down big, now close
                            if prev_diff <= -margin and abs(curr_diff) <= 3:
                                comeback_key = f"comeback_a_{game_id}"
                                if comeback_key not in state_obj['seen_game_ids']:
                                    state_obj['seen_game_ids'].add(comeback_key)
                                    return True
                            # Home was down big, now close
                            if prev_diff >= margin and abs(curr_diff) <= 3:
                                comeback_key = f"comeback_h_{game_id}"
                                if comeback_key not in state_obj['seen_game_ids']:
                                    state_obj['seen_game_ids'].add(comeback_key)
                                    return True

    except Exception:
        pass
    return False
