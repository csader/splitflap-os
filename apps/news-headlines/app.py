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


def trigger(settings, conditions):
    """Fire when a headline containing the configured keyword appears."""
    import urllib.request
    import xml.etree.ElementTree as ET

    keywords_str = conditions.get('keywords', '').upper().strip()
    keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
    feed_url = settings.get('feed_url', 'https://feeds.bbci.co.uk/news/rss.xml')

    state = getattr(trigger, '_state', None)
    if state is None:
        state = {'seen_titles': set()}
        setattr(trigger, '_state', state)

    try:
        req = urllib.request.Request(feed_url, headers={"User-Agent": "SplitFlap/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
        items = root.findall('.//item')
        if not items:
            items = root.findall('.//{http://www.w3.org/2005/Atom}entry')

        for item in items[:10]:
            title_el = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
            if title_el is None or not title_el.text:
                continue
            title = title_el.text.strip().upper()
            if title in state['seen_titles']:
                continue
            state['seen_titles'].add(title)
            # If no keywords configured, fire on any new headline
            if not keywords:
                return True
            if any(kw in title for kw in keywords):
                return True

        # Prune seen set
        if len(state['seen_titles']) > 200:
            state['seen_titles'] = set(list(state['seen_titles'])[-100:])
    except Exception:
        pass
    return False
