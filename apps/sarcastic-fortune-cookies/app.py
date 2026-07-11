"""
Sarcastic Fortune Cookies — a functional Split-Flap plugin.

Shows a random tongue-in-cheek "fortune cookie" one-liner and swaps it for a new
random one on a chosen interval. Fortunes ship in several languages, one bundled
``fortunes_<lang>.json`` file each; the language follows the global Language
setting, falling back to English when there's no file for it. Accented fortunes
keep their Windows-1252 accents (É, Ü, ß, Œ, …) — the gateway and modules render
the cp1252 code page directly, so nothing is stripped.

Drop-in compatible with the splitflap-os plugin ABI:
    fetch(settings, format_lines, get_rows, get_cols) -> list[str]
"""

import json
import os
import random
import time

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(lang):
    """Load + cache the fortune list for a language (read once per process)."""
    cache = getattr(fetch, "_data", None)
    if cache is None:
        cache = {}
        fetch._data = cache
    if lang not in cache:
        path = os.path.join(_HERE, "fortunes_%s.json" % lang)
        entries = []
        # Bundled files are UTF-8; fall back to cp1252 in case a file is replaced
        # with a Windows-1252 one.
        for enc in ("utf-8", "cp1252"):
            try:
                with open(path, encoding=enc) as fh:
                    entries = json.load(fh)
                break
            except (UnicodeDecodeError, FileNotFoundError, ValueError, OSError):
                continue
        cache[lang] = [e["fortune"] for e in entries
                       if isinstance(e, dict) and e.get("fortune")]
    return cache[lang]


def _hard_wrap(words, rows, cols):
    flat = " ".join(words)
    return [flat[i:i + cols] for i in range(0, len(flat), cols)][:rows]


def _balance(words, lens, cols, k):
    """Split ``words`` into exactly ``k`` lines (each <= cols), minimizing
    raggedness (sum of squared trailing slack) so the lines are evenly filled
    instead of packing the top and orphaning the last word — nudged toward
    ending a line at sentence punctuation. A short DP; fortunes are tiny."""
    n = len(words)
    pre = [0]
    for wl in lens:
        pre.append(pre[-1] + wl)

    def linelen(i, j):                      # words[i..j] inclusive, with spaces
        return pre[j + 1] - pre[i] + (j - i)

    INF = float("inf")
    dp = [[INF] * (n + 1) for _ in range(k + 1)]
    nxt = [[0] * (n + 1) for _ in range(k + 1)]
    dp[0][n] = 0.0
    for kk in range(1, k + 1):
        for i in range(n - 1, -1, -1):
            j = i
            while j < n:
                ll = linelen(i, j)
                if ll > cols and j > i:
                    break
                rest = dp[kk - 1][j + 1]
                if rest < INF:
                    slack = cols - ll
                    cost = slack * slack + rest
                    if words[j][-1:] in ".!?":
                        cost -= cols        # prefer breaking after a sentence
                    if cost < dp[kk][i]:
                        dp[kk][i] = cost
                        nxt[kk][i] = j + 1
                j += 1
    if dp[k][0] >= INF:
        return _hard_wrap(words, k, cols)
    out, i, kk = [], 0, k
    while kk > 0:
        j = nxt[kk][i]
        out.append(" ".join(words[i:j]))
        i, kk = j, kk - 1
    return out


def _wrap(text, rows, cols):
    """Fit ``text`` into at most ``rows`` lines of ``cols`` characters, balanced.

    When the text fits on the page, its words are spread evenly across the lines
    it needs (not greedily packed, which leaves a lonely last word); only if even
    the tightest word-wrap needs more rows than the board has do we fall back to a
    hard character wrap. An accented letter counts as one character (one module).
    """
    words = text.split()
    if not words:
        return []
    lens = [len(w) for w in words]
    if max(lens) > cols:
        return _hard_wrap(words, rows, cols)
    # Fewest lines a word-wrap needs.
    need, cur = 1, 0
    for wl in lens:
        add = wl if cur == 0 else cur + 1 + wl
        if add <= cols:
            cur = add
        else:
            need += 1
            cur = wl
    if need > rows:
        return _hard_wrap(words, rows, cols)
    return _balance(words, lens, cols, need)


def fetch(settings, format_lines, get_rows, get_cols, i18n=None):
    rows, cols = get_rows(), get_cols()

    # Language follows the global Language (or a per-app override, via i18n); use
    # it when we bundle fortunes for it, otherwise fall back to English. Off a
    # companion host (i18n is None) we read the raw setting.
    lang = str((i18n.lang if i18n is not None else settings.get("language")) or "en").lower()
    if not _load(lang):
        lang = "en"
    try:
        every = int(settings.get("frequency") or 300)
    except (ValueError, TypeError):
        every = 300

    now = time.time()
    state = getattr(fetch, "_state", None)
    # Pick a new fortune on first run, when the chosen interval elapses, or when
    # the language changes (so a language switch shows on the next tick).
    if (state is None
            or state.get("lang") != lang
            or not state.get("pages")
            or (now - state.get("at", 0)) >= every):
        fortunes = _load(lang)
        text = random.choice(fortunes) if fortunes else "NO FORTUNES FOUND"
        lines = _wrap(text, rows, cols)
        # Vertically centre when the board has spare rows (format_lines centres
        # each line horizontally and pads the remaining rows at the bottom).
        top = (rows - len(lines)) // 2
        page = format_lines(*([""] * top + lines))
        fetch._state = {"at": now, "lang": lang, "pages": [page]}
    return fetch._state["pages"]
