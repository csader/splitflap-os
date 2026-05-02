"""News Headlines via RSS plugin for Split-Flap Display."""

def fetch(settings, format_lines, get_rows, get_cols):
    import urllib.request
    import xml.etree.ElementTree as ET

    cols = get_cols()
    rows = get_rows()
    feed_url = settings.get('feed_url', 'https://feeds.bbci.co.uk/news/rss.xml')

    def split_text(text, width):
        words = text.split()
        lines = []
        current = ''
        for word in words:
            if current and len(current) + 1 + len(word) > width:
                lines.append(current)
                current = word
            elif not current:
                current = word[:width]
            else:
                current += ' ' + word
        if current:
            lines.append(current)
        return lines

    try:
        req = urllib.request.Request(feed_url, headers={"User-Agent": "SplitFlap/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
        # Handle both RSS and Atom feeds
        items = root.findall('.//item')
        if not items:
            items = root.findall('.//{http://www.w3.org/2005/Atom}entry')
        titles = []
        for item in items[:10]:
            title_el = item.find('title')
            if title_el is None:
                title_el = item.find('{http://www.w3.org/2005/Atom}title')
            if title_el is not None and title_el.text:
                titles.append(title_el.text.strip().upper())
    except Exception:
        titles = ['NEWS UNAVAILABLE', 'CHECK FEED URL']

    allowed = set(" ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$&()-+=;:%'.,/?*")
    pages = []
    for title in titles:
        title = ''.join(c if c in allowed else ' ' for c in title)
        lines = split_text(title, cols)
        for i in range(0, len(lines), rows):
            chunk = lines[i:i + rows]
            pages.append(format_lines(*chunk))

    return pages or [format_lines('NEWS', 'NO HEADLINES', '')]
