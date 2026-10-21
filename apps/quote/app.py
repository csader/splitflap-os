"""An inspirational quote (keyless: DummyJSON quotes)."""


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
    """Lay the text out under a title. When it fits on one page the words are
    balanced evenly across the lines it needs; longer text word-wraps and
    paginates."""
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
                return [format_lines(title, *bal)] if title else [format_lines(*bal)]
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
        max_len = int(float(settings.get('max_length', '150') or 150))
    except (TypeError, ValueError):
        max_len = 150
    max_len = max(40, min(300, max_len))

    def one():
        d = requests.get('https://dummyjson.com/quotes/random', timeout=8).json()
        return str(d.get('quote', '') or '').strip(), str(d.get('author', '') or '').strip()

    try:
        # The API can't filter by length, so try a few times for a short quote,
        # keeping the shortest seen if none come in under the limit.
        best = None
        for _ in range(3):
            q, a = one()
            if not q:
                continue
            if len(q) <= max_len:
                best = (q, a)
                break
            if best is None or len(q) < len(best[0]):
                best = (q, a)
        if not best:
            return [format_lines('QUOTE', 'NO DATA', '')]
        q, a = best
        text = f'{q.upper()}  - {a.upper()}' if a else q.upper()
        return _pages(format_lines, '', f'QUOTE: {text}', rows, cols)
    except Exception:
        return [format_lines('QUOTE', 'OFFLINE', '')]
