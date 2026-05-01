"""Checkerboard animation."""

def fetch(settings, format_lines, get_rows, get_cols):
    rows, cols = get_rows(), get_cols()
    pages = []
    for a, b in [('r','b'),('o','p'),('y','g'),('r','w'),('g','b')]:
        p1 = ''.join(a if (r+c)%2==0 else b for r in range(rows) for c in range(cols))
        p2 = ''.join(b if (r+c)%2==0 else a for r in range(rows) for c in range(cols))
        pages += [p1, p2]
    return pages
