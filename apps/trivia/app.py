"""Trivia plugin for Split-Flap Display."""

def fetch(settings, format_lines, get_rows, get_cols):
    import urllib.request
    import json
    import html
    import random

    cols = get_cols()
    rows = get_rows()

    fallback_qa = [
        ("WHAT IS THE LARGEST PLANET?", "JUPITER"),
        ("HOW MANY BONES IN A HUMAN BODY?", "206"),
        ("WHAT IS THE SPEED OF LIGHT?", "186000 MI/SEC"),
        ("WHAT YEAR DID WW2 END?", "1945"),
        ("WHAT IS THE SMALLEST COUNTRY?", "VATICAN CITY"),
        ("HOW MANY STRINGS ON A GUITAR?", "SIX"),
        ("WHAT IS THE HARDEST MINERAL?", "DIAMOND"),
        ("WHAT GAS DO PLANTS ABSORB?", "CO2"),
        ("HOW MANY LEGS DOES A SPIDER HAVE?", "EIGHT"),
        ("WHAT IS THE LARGEST OCEAN?", "PACIFIC"),
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
        url = "https://opentdb.com/api.php?amount=1&type=multiple"
        req = urllib.request.Request(url, headers={"User-Agent": "SplitFlap/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        result = data["results"][0]
        question = html.unescape(result["question"]).upper()
        answer = html.unescape(result["correct_answer"]).upper()
    except Exception:
        q, a = random.choice(fallback_qa)
        question, answer = q, a

    allowed = set(" ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$&()-+=;:%'.,/?*")
    question = ''.join(c if c in allowed else ' ' for c in question)
    answer = ''.join(c if c in allowed else ' ' for c in answer)

    q_lines = split_text(question, cols)
    pages = []
    for i in range(0, len(q_lines), rows):
        chunk = q_lines[i:i + rows]
        pages.append(format_lines(*chunk))

    a_lines = split_text(answer, cols)
    a_lines = ['ANSWER:'] + a_lines
    for i in range(0, len(a_lines), rows):
        chunk = a_lines[i:i + rows]
        pages.append(format_lines(*chunk))

    return pages or [format_lines('TRIVIA', 'NO DATA', '')]
