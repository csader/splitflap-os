def fetch(settings, format_lines, get_rows, get_cols):
    import requests
    from collections import Counter

    host = settings.get('birdnet_host', '192.168.86.139')
    port = settings.get('birdnet_port', '80')
    mode = settings.get('display_mode', 'latest')
    min_conf = int(settings.get('min_confidence', '70')) / 100
    leaderboard_count = int(settings.get('leaderboard_count', '3'))
    base_url = f"http://{host}:{port}"

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

    try:
        limit = 50 if mode == 'leaderboard' else 10
        r = requests.get(f"{base_url}/api/v1/detections/recent?limit={limit}", timeout=10)
        r.raise_for_status()
        detections = r.json()
        detections = [d for d in detections if d['confidence'] >= min_conf]

        if not detections:
            return [format_lines('BIRDNET', 'NO DETECTIONS', 'CHECK SETTINGS')]

        rows = get_rows()
        cols = get_cols()

        if mode == 'latest':
            bird = detections[0]
            conf = f"{int(bird['confidence'] * 100)}%"
            short = shorten_name(bird['species'], cols - len(conf) - 1)
            return [format_lines(f"{short} {conf}")]

        elif mode == 'last_3':
            pages = []
            for bird in detections[:3]:
                conf = f"{int(bird['confidence'] * 100)}%"
                short = shorten_name(bird['species'], cols - len(conf) - 1)
                pages.append(format_lines(f"{short} {conf}"))
            return pages

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
            return [format_lines(*lines[:rows])]

    except Exception as e:
        return [format_lines('BIRDNET', 'ERROR', str(e)[:cols] if cols > 10 else 'ERR')]
