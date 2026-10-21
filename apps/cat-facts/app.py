"""A random cat fact (keyless: catfact.ninja)."""


def _need_lines(lens, cols):
    need, cur = 1, 0
    for wl in lens:
        add = wl if cur == 0 else cur + 1 + wl
        if add <= cols:
            cur = add
        else:
            need += 1
            cur = wl
    return need


def _balance(words, lens, cols, k):
    """Split words into exactly k lines (each <= cols) minimizing raggedness, so
    lines fill evenly instead of orphaning the last word; prefers ending a line at
    sentence punctuation. A tiny DP."""
    n = len(words)
    pre = [0]
    for wl in lens:
        pre.append(pre[-1] + wl)

    def linelen(i, j):
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
                        cost -= cols
                    if cost < dp[kk][i]:
                        dp[kk][i] = cost
                        nxt[kk][i] = j + 1
                j += 1
    if dp[k][0] >= INF:
        return None
    out, i, kk = [], 0, k
    while kk > 0:
        j = nxt[kk][i]
        out.append(" ".join(words[i:j]))
        i, kk = j, kk - 1
    return out


def _greedy(words, cols):
    lines, cur = [], ''
    for w in words:
        w = w if len(w) <= cols else w[:cols]
        if len(cur) + len(w) + (1 if cur else 0) <= cols:
            cur = f'{cur} {w}'.strip()
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or ['']


def _pages(format_lines, title, text, rows, cols):
    """Lay the text out (optionally under a title). When it fits on one page the
    words are balanced evenly across the lines; longer text word-wraps and
    paginates. With no title the text uses every row and is vertically centered."""
    words = text.split() or ['']
    lens = [len(w) for w in words]
    if rows == 1:
        return [ln.center(cols)[:cols] for ln in _greedy(words, cols)]
    body = rows - 1 if title else rows
    if max(lens) <= cols:
        need = _need_lines(lens, cols)
        if need <= body:
            bal = _balance(words, lens, cols, need)
            if bal is not None:
                if title:
                    return [format_lines(title, *bal)]
                top = (rows - len(bal)) // 2
                return [format_lines(*([''] * top + bal))]
    lines = _greedy(words, cols)
    pages, i = ([format_lines(title, *lines[:body])], body) if title else ([], 0)
    while i < len(lines):
        pages.append(format_lines(*lines[i:i + rows]))
        i += rows
    return pages

def fetch(settings, format_lines, get_rows, get_cols):
    import requests
    rows, cols = get_rows(), get_cols()
    try:
        max_len = int(float(settings.get('max_length', '120') or 120))
    except (TypeError, ValueError):
        max_len = 120
    max_len = max(40, min(250, max_len))
    try:
        # catfact.ninja honors max_length, so we can ask for a display-friendly fact.
        d = requests.get('https://catfact.ninja/fact',
                         params={'max_length': max_len}, timeout=8).json()
        text = str(d.get('fact', '') or '').strip().upper()
        if not text:
            return [format_lines('CAT FACT', 'NO DATA', '')]
        return _pages(format_lines, '', text, rows, cols)   # no title — just the fact
    except Exception:
        return [format_lines('CAT FACT', 'OFFLINE', '')]
