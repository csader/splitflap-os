"""Chuck Norris facts plugin for Split-Flap Display."""

def fetch(settings, format_lines, get_rows, get_cols):
    import urllib.request
    import json
    import random

    cols = get_cols()

    fallback = [
        "CHUCK NORRIS COUNTED TO INFINITY TWICE",
        "CHUCK NORRIS CAN SLAM A REVOLVING DOOR",
        "CHUCK NORRIS MAKES ONIONS CRY",
        "WHEN CHUCK NORRIS DOES PUSHUPS HE PUSHES THE EARTH DOWN",
        "CHUCK NORRIS CAN HEAR SIGN LANGUAGE",
        "CHUCK NORRIS WON A STARING CONTEST WITH THE SUN",
        "TIME WAITS FOR NO ONE EXCEPT CHUCK NORRIS",
        "CHUCK NORRIS CAN CUT A KNIFE WITH BUTTER",
        "CHUCK NORRIS CAN SPEAK BRAILLE",
        "CHUCK NORRIS BEAT THE SUN IN A STARING CONTEST",
    ]

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
        url = "https://api.chucknorris.io/jokes/random"
        req = urllib.request.Request(url, headers={"User-Agent": "SplitFlap/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        text = data["value"].upper()
    except Exception:
        text = random.choice(fallback)

    # Remove characters not in the flap set
    allowed = set(" ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$&()-+=;:%'.,/?*")
    text = ''.join(c if c in allowed else ' ' for c in text)

    lines = split_text(text, cols)
    rows = get_rows()
    pages = []
    for i in range(0, len(lines), rows):
        chunk = lines[i:i + rows]
        pages.append(format_lines(*chunk))
    return pages or [format_lines('CHUCK NORRIS', 'FACTS', '')]
