"""Twinkle sparkle animation."""

def fetch(settings, format_lines, get_rows, get_cols):
    import random
    colors = 'roygbpw   '
    n = get_rows() * get_cols()
    return [''.join(random.choice(colors) for _ in range(n)) for _ in range(12)]
