"""Word of the Day plugin for Split-Flap Display."""

def fetch(settings, format_lines, get_rows, get_cols):
    import urllib.request
    import json
    try:
        url = "https://api.dictionaryapi.dev/api/v2/entries/en/random"
        req = urllib.request.Request(url, headers={"User-Agent": "SplitFlap/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        word = data[0]["word"].upper()
        meaning = data[0]["meanings"][0]["definitions"][0]["definition"].upper()
        return [
            format_lines("WORD OF THE DAY", word, ""),
            format_lines(meaning[:get_cols()], meaning[get_cols():get_cols()*2], ""),
        ]
    except Exception:
        import random
        words = [
            ("EPHEMERAL", "LASTING A", "VERY SHORT TIME"),
            ("UBIQUITOUS", "PRESENT OR", "FOUND EVERYWHERE"),
            ("SERENDIPITY", "HAPPY ACCIDENT", "OR DISCOVERY"),
            ("ELOQUENT", "FLUENT OR", "PERSUASIVE"),
            ("RESILIENT", "ABLE TO RECOVER", "QUICKLY"),
            ("PRAGMATIC", "DEALING WITH", "THINGS SENSIBLY"),
            ("CANDOR", "THE QUALITY OF", "BEING OPEN"),
            ("TENACIOUS", "HOLDING FIRMLY", "TO SOMETHING"),
        ]
        word, l2, l3 = random.choice(words)
        return [format_lines("WORD OF THE DAY", word, ""), format_lines(l2, l3, "")]
