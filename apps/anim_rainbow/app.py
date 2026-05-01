"""Rainbow colour wave animation."""

def fetch(settings, format_lines, get_rows, get_cols):
    colors = 'roygbpw'
    rows, cols = get_rows(), get_cols()
    return [''.join(colors[(c + off) % 7] for r in range(rows) for c in range(cols))
            for off in range(7)]
