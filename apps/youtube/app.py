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
    """Fire when a new video is posted to the followed channel."""
    import requests
    import xml.etree.ElementTree as ET

    channel_id = settings.get('yt_channel_id', '')
    if not channel_id:
        return False

    state = getattr(trigger, '_state', None)
    if state is None:
        state = {'last_video_id': None}
        setattr(trigger, '_state', state)

    try:
        url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
        r = requests.get(url, timeout=10)
        root = ET.fromstring(r.content)
        ns = {'a': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
        entries = root.findall('a:entry', ns)
        if not entries:
            return False
        latest_id = entries[0].find('yt:videoId', ns)
        if latest_id is None:
            return False
        vid_id = latest_id.text
        if state['last_video_id'] is None:
            # First run — seed without firing
            state['last_video_id'] = vid_id
            return False
        if vid_id != state['last_video_id']:
            state['last_video_id'] = vid_id
            return True
    except Exception:
        pass
    return False
