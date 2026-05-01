"""Colour band sweep animation."""

def fetch(settings, format_lines, get_rows, get_cols):
    colors = 'roygbpw'
    rows, cols = get_rows(), get_cols()
    pages = []
    for i in range(1, cols + 1):
        col = colors[i % 7]
        pages.append(''.join(col if c < i else ' ' for r in range(rows) for c in range(cols)))
    for i in range(cols - 1, 0, -1):
        col = colors[(i + 3) % 7]
        pages.append(''.join(col if c < i else ' ' for r in range(rows) for c in range(cols)))
    return pages
