def fetch(settings, format_lines, get_rows, get_cols):
    import requests
    from collections import Counter

    host = settings.get('birdnet_host', '192.168.86.139')
    port = settings.get('birdnet_port', '80')
    mode = settings.get('display_mode', 'latest')
    min_conf = int(settings.get('min_confidence', '70')) / 100
    leaderboard_count = int(settings.get('leaderboard_count', '3'))
    base_url = f"http://{host}:{port}"

    # Bird color mapping for split-flap color characters
    # Maps common bird color keywords to flap color codes
    BIRD_COLORS = {
        'red': 'r', 'cardinal': 'r', 'tanager': 'r',
        'orange': 'o', 'oriole': 'o',
        'yellow': 'y', 'goldfinch': 'y', 'warbler': 'y',
        'green': 'g', 'parakeet': 'g', 'hummingbird': 'g',
        'blue': 'b', 'bluebird': 'b', 'jay': 'b', 'bunting': 'b',
        'purple': 'p', 'martin': 'p', 'grackle': 'p',
        'white': 'w', 'dove': 'w', 'egret': 'w', 'gull': 'w',
    }

    def get_color_char(species_name):
        """Try to match a bird species to a flap color character."""
        name_lower = species_name.lower()
        for keyword, color in BIRD_COLORS.items():
            if keyword in name_lower:
                return color
        return ''

    try:
        # Fetch enough detections for all modes
        limit = 50 if mode == 'leaderboard' else 10
        r = requests.get(f"{base_url}/api/v1/detections/recent?limit={limit}", timeout=10)
        r.raise_for_status()
        detections = r.json()

        # Filter by confidence
        detections = [d for d in detections if d['confidence'] >= min_conf]

        if not detections:
            return [format_lines('BIRDNET', 'NO DETECTIONS', 'CHECK SETTINGS')]

        rows = get_rows()
        cols = get_cols()

        if mode == 'latest':
            bird = detections[0]
            name = bird['species'].upper()
            conf = f"{int(bird['confidence'] * 100)}%"
            time_str = bird['time'][:5]  # HH:MM
            color = get_color_char(bird['species'])
            indicator = color * 2 + ' ' if color else ''

            if rows == 1:
                return [format_lines(f"{name} {conf}")]
            elif rows == 2:
                return [format_lines(f"{indicator}{name}", f"{conf} {time_str}")]
            else:
                return [format_lines(f"{indicator}{name}", f"CONFIDENCE {conf}", f"DETECTED {time_str}")]

        elif mode == 'last_3':
            pages = []
            for bird in detections[:3]:
                name = bird['species'].upper()
                conf = f"{int(bird['confidence'] * 100)}%"
                time_str = bird['time'][:5]
                color = get_color_char(bird['species'])
                indicator = color * 2 + ' ' if color else ''

                if rows == 1:
                    pages.append(format_lines(f"{name} {conf}"))
                elif rows == 2:
                    pages.append(format_lines(f"{indicator}{name}", f"{conf} {time_str}"))
                else:
                    pages.append(format_lines(f"{indicator}{name}", f"CONFIDENCE {conf}", f"DETECTED {time_str}"))
            return pages

        elif mode == 'leaderboard':
            # Count species from today's detections
            species_count = Counter(d['species'] for d in detections)
            top = species_count.most_common(leaderboard_count)

            pages = []
            # Title page
            if rows >= 2:
                pages.append(format_lines('BIRDNET', f"TOP {len(top)} TODAY"))
            else:
                pages.append(format_lines(f"TOP {len(top)} BIRDS TODAY"))

            # One page per leader
            for rank, (species, count) in enumerate(top, 1):
                name = species.upper()
                color = get_color_char(species)
                indicator = color * 3 + ' ' if color else ''

                if rows == 1:
                    pages.append(format_lines(f"#{rank} {name} x{count}"))
                elif rows == 2:
                    pages.append(format_lines(f"#{rank} {indicator}{name}", f"{count} DETECTIONS"))
                else:
                    pages.append(format_lines(f"#{rank} {indicator}{name}", f"{count} DETECTIONS", f"TODAY"))
            return pages

    except Exception as e:
        return [format_lines('BIRDNET', 'ERROR', str(e)[:cols] if get_cols() > 10 else 'ERR')]
