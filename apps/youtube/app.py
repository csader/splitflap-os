def fetch(settings, format_lines, get_rows, get_cols):
    import requests
    import xml.etree.ElementTree as ET
    channel_id = settings.get('yt_channel_id', '')
    if not channel_id:
        return [format_lines('YOUTUBE', 'NO CHANNEL', 'SET ID')]
    try:
        url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
        r = requests.get(url, timeout=10)
        root = ET.fromstring(r.content)
        ns = {'a': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
        name = root.find('a:title', ns).text.upper()
        entries = root.findall('a:entry', ns)
        count = f'{len(entries)} VIDEOS'
        return [format_lines('YOUTUBE', name, count)]
    except Exception:
        return [format_lines('YOUTUBE', 'ERROR', 'CHECK ID')]


def trigger(settings, conditions):
    """Fire when a new video is posted or a video crosses a view milestone."""
    import requests
    import xml.etree.ElementTree as ET

    channel_id = settings.get('yt_channel_id', '')
    api_key = settings.get('yt_api_key', '')
    condition_type = conditions.get('condition_type', 'new_video')
    if not channel_id:
        return False

    state = getattr(trigger, '_state', None)
    if state is None:
        state = {'last_video_id': None, 'fired_milestones': set()}
        setattr(trigger, '_state', state)

    try:
        url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
        r = requests.get(url, timeout=10)
        root = ET.fromstring(r.content)
        ns = {'a': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
        entries = root.findall('a:entry', ns)
        if not entries:
            return False
        latest_id_el = entries[0].find('yt:videoId', ns)
        if latest_id_el is None:
            return False
        vid_id = latest_id_el.text

        if condition_type == 'new_video':
            if state['last_video_id'] is None:
                state['last_video_id'] = vid_id
                return False
            if vid_id != state['last_video_id']:
                state['last_video_id'] = vid_id
                return True

        elif condition_type == 'view_milestone' and api_key:
            milestone = int(conditions.get('view_milestone', 1000000))
            # Check view count via YouTube Data API
            vr = requests.get(
                'https://www.googleapis.com/youtube/v3/videos',
                params={'part': 'statistics', 'id': vid_id, 'key': api_key},
                timeout=8
            ).json()
            items = vr.get('items', [])
            if not items:
                return False
            views = int(items[0].get('statistics', {}).get('viewCount', 0))
            key = f"{vid_id}:{milestone}"
            if views >= milestone and key not in state['fired_milestones']:
                state['fired_milestones'].add(key)
                return True

    except Exception:
        pass
    return False
