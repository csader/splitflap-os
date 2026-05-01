"""Livestream mode — rotates subs, viewers, and comment slides."""

def fetch(settings, format_lines, get_rows, get_cols):
    from datetime import datetime
    import pytz, requests, logging
    pages = []
    tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    time_str = datetime.now(tz).strftime("%I:%M %p").lstrip("0")

    # YouTube subs
    cid = settings.get('yt_channel_id', '').strip()
    if cid:
        try:
            import urllib.request, json
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
            req = urllib.request.Request(url, headers={"User-Agent": "SplitFlap/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = resp.read().decode()
            import re
            name = re.search(r'<name>(.+?)</name>', body)
            name = name.group(1).upper() if name else cid[:15]
            pages.append({'text': format_lines(time_str, name[:15], "YOUTUBE"), 'style': 'ltr'})
        except Exception:
            pass

    # Concurrent viewers
    api_key = settings.get('yt_api_key', '').strip()
    video_id = settings.get('yt_video_id', '').strip()
    if api_key and video_id:
        try:
            url = f"https://www.googleapis.com/youtube/v3/videos?part=liveStreamingDetails&id={video_id}&key={api_key}"
            data = requests.get(url, timeout=5).json()
            items = data.get('items', [])
            if items:
                v = items[0].get('liveStreamingDetails', {}).get('concurrentViewers')
                if v is not None:
                    pages.append({'text': format_lines("WATCHING NOW", f"{int(v):,}", "LIVE VIEWERS"), 'style': 'diagonal'})
        except Exception:
            pass

    # Comment slides
    raw = settings.get('livestream_comments', '').strip()
    if raw:
        raw = raw.replace('\r\n', '\n').replace('\r', '\n')
        styles = ['outside_in', 'spiral', 'anti_diagonal', 'rtl', 'rain', 'center_out']
        for i, block in enumerate(b for b in raw.split('\n\n') if b.strip()):
            lines = [l.strip() for l in block.split('\n') if l.strip()][:3]
            while len(lines) < 3: lines.append('')
            cols = get_cols()
            page = ''.join(l[:cols].center(cols) for l in lines)
            pages.append({'text': page, 'style': styles[i % len(styles)]})

    return pages or [format_lines("LIVESTREAM", time_str, "NO DATA")]
