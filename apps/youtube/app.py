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
