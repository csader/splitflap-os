def fetch(settings, format_lines, get_rows, get_cols):
    import requests
    from collections import Counter

    host = settings.get('birdnet_host', '192.168.86.139')
    port = settings.get('birdnet_port', '80')
    mode = settings.get('display_mode', 'latest')
    min_conf = int(settings.get('min_confidence', '70')) / 100
    leaderboard_count = int(settings.get('leaderboard_count', '3'))
    base_url = f"http://{host}:{port}"

    # Cache invalidation: re-fetch when settings change
    state = getattr(fetch, '_state', None)
    if state is None:
        state = {'last_sig': None, 'last_pages': None}
        setattr(fetch, '_state', state)
    sig = (host, port, mode, min_conf, leaderboard_count)
    if sig != state['last_sig']:
        state['last_pages'] = None
        state['last_sig'] = sig

    ABBREV_WORDS = {
        'northern', 'southern', 'eastern', 'western', 'american', 'common',
        'carolina', 'great', 'lesser', 'greater', 'little', 'dark',
        'rufous', 'spotted', 'striped',
    }

    def shorten_name(species, max_len):
        words = species.split()
        parts = []
        for word in words:
            if '-' in word:
                parts.append(''.join(p[0].upper() for p in word.split('-') if p))
            elif word.lower() in ABBREV_WORDS:
                parts.append(word[0].upper() + '.')
            else:
                parts.append(word)
        name = ' '.join(parts)
        if len(name) <= max_len:
            return name
        core = [p for p in parts if not (len(p) == 2 and p.endswith('.'))]
        name = ' '.join(core)
        if len(name) <= max_len:
            return name
        return name[:max_len]

    def vcenter(text, rows):
        """Vertically center a single line of text in a rows-tall display."""
        mid = rows // 2
        lines = [''] * rows
        lines[mid] = text
        return format_lines(*lines)

    try:
        limit = 50 if mode == 'leaderboard' else 10
        r = requests.get(f"{base_url}/api/v1/detections/recent?limit={limit}", timeout=10)
        r.raise_for_status()
        detections = r.json()
        detections = [d for d in detections if d['confidence'] >= min_conf]

        if not detections:
            pages = [format_lines('BIRDNET', 'NO DETECTIONS', 'CHECK SETTINGS')]
            state['last_pages'] = pages
            return pages

        rows = get_rows()
        cols = get_cols()

        if mode == 'latest':
            bird = detections[0]
            conf = f"{int(bird['confidence'] * 100)}%"
            short = shorten_name(bird['species'], cols - len(conf) - 1)
            pages = [vcenter(f"{short} {conf}", rows)]

        elif mode == 'last_3':
            pages = []
            seen = set()
            for bird in detections:
                if bird['species'] not in seen:
                    seen.add(bird['species'])
                    conf = f"{int(bird['confidence'] * 100)}%"
                    short = shorten_name(bird['species'], cols - len(conf) - 1)
                    pages.append(vcenter(f"{short} {conf}", rows))
                    if len(pages) == 3:
                        break

        elif mode == 'leaderboard':
            species_count = Counter(d['species'] for d in detections)
            top = species_count.most_common(min(leaderboard_count, rows))
            lines = []
            for species, count in top:
                count_str = str(count)
                short = shorten_name(species, cols - len(count_str) - 1)
                lines.append(f"{count_str} {short}")
            while len(lines) < rows:
                lines.append('')
            pages = [format_lines(*lines[:rows])]

        else:
            pages = [format_lines('BIRDNET', 'UNKNOWN MODE', '')]

        state['last_pages'] = pages
        return pages

    except Exception as e:
        if state['last_pages']:
            return state['last_pages']
        return [format_lines('BIRDNET', 'ERROR', str(e)[:cols] if cols > 10 else 'ERR')]


def trigger(settings, conditions):
    """Fire when a new bird detection matches the configured filter."""
    import requests

    host = settings.get('birdnet_host', '192.168.86.139')
    port = settings.get('birdnet_port', '80')
    min_conf = int(settings.get('min_confidence', '70')) / 100
    filt = conditions.get('filter', 'any')
    species_query = conditions.get('species', '').lower().strip()
    watchlist_str = conditions.get('watchlist', '').lower()
    watchlist = [s.strip() for s in watchlist_str.split(',') if s.strip()]
    high_conf_threshold = float(conditions.get('high_confidence', 95)) / 100

    state = getattr(trigger, '_state', None)
    if state is None:
        state = {'last_id': None, 'seen_today': set()}
        setattr(trigger, '_state', state)

    try:
        r = requests.get(f"http://{host}:{port}/api/v1/detections/recent?limit=5", timeout=5)
        detections = [d for d in r.json() if d.get('confidence', 0) >= min_conf]
        if not detections:
            return False
        latest = detections[0]
        det_id = latest.get('id') or latest.get('timestamp') or latest.get('time')
        if det_id == state['last_id']:
            return False  # nothing new
        state['last_id'] = det_id
        species = latest.get('species', '')
        confidence = latest.get('confidence', 0)

        if filt == 'any':
            return True
        if filt == 'specific':
            return bool(species_query) and species_query in species.lower()
        if filt == 'new_today':
            if species not in state['seen_today']:
                state['seen_today'].add(species)
                return True
        if filt == 'watchlist':
            return bool(watchlist) and any(w in species.lower() for w in watchlist)
        if filt == 'high_confidence':
            return confidence >= high_conf_threshold
        if filt == 'busy_feeder':
            count = int(conditions.get('busy_count', 5))
            window_mins = int(conditions.get('busy_window', 10))
            import time as _time
            now_ts = _time.time()
            # Store recent detection timestamps
            if 'recent_times' not in state:
                state['recent_times'] = []
            state['recent_times'].append(now_ts)
            # Prune to window
            cutoff = now_ts - (window_mins * 60)
            state['recent_times'] = [t for t in state['recent_times'] if t >= cutoff]
            return len(state['recent_times']) >= count
        return False
    except Exception:
        return False
