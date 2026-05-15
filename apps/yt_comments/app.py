def fetch(settings, format_lines, get_rows, get_cols):
    import requests
    video_id = settings.get('yt_video_id', '')
    api_key = settings.get('yt_api_key', '')
    if not video_id or not api_key:
        return [format_lines('COMMENTS', 'MISSING', 'CONFIG')]
    try:
        r = requests.get(
            'https://www.googleapis.com/youtube/v3/commentThreads',
            params={'part': 'snippet', 'videoId': video_id, 'key': api_key, 'maxResults': 10, 'order': 'time'},
            timeout=10
        ).json()
        pages = []
        cols = get_cols()
        rows = get_rows()
        for item in r.get('items', []):
            s = item['snippet']['topLevelComment']['snippet']
            author = s['authorDisplayName'].upper()[:cols]
            text = s['textDisplay'].upper()
            # split text into lines that fit the display
            text_lines = [text[j:j+cols] for j in range(0, len(text), cols)]
            text_lines = text_lines[:rows - 1]  # leave room for author
            lines = [author] + text_lines
            lines += [''] * (rows - len(lines))
            pages.append(format_lines(*lines[:rows]))
        return pages or [format_lines('COMMENTS', 'NONE FOUND', '')]
    except Exception:
        return [format_lines('COMMENTS', 'ERROR', 'CHECK CONFIG')]


def trigger(settings, conditions):
    """Fire when a new comment appears on the followed video."""
    import requests

    video_id = settings.get('yt_video_id', '')
    api_key = settings.get('yt_api_key', '')
    keyword = conditions.get('keyword', '').upper().strip()
    if not video_id or not api_key:
        return False

    state = getattr(trigger, '_state', None)
    if state is None:
        state = {'seen_ids': set()}
        setattr(trigger, '_state', state)

    try:
        r = requests.get(
            'https://www.googleapis.com/youtube/v3/commentThreads',
            params={'part': 'snippet', 'videoId': video_id, 'key': api_key,
                    'maxResults': 5, 'order': 'time'},
            timeout=10
        ).json()
        for item in r.get('items', []):
            cid = item.get('id', '')
            if cid in state['seen_ids']:
                continue
            state['seen_ids'].add(cid)
            if not keyword:
                return True
            text = item['snippet']['topLevelComment']['snippet'].get('textDisplay', '').upper()
            if keyword in text:
                return True
        if len(state['seen_ids']) > 500:
            state['seen_ids'] = set(list(state['seen_ids'])[-200:])
    except Exception:
        pass
    return False
