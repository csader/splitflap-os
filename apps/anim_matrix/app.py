"""Matrix cascade reveal animation."""

def fetch(settings, format_lines, get_rows, get_cols):
    import random
    n = get_rows() * get_cols()
    target = settings.get('anim_text', 'SPLIT  FLAP  DISPLAY').upper().ljust(n)[:n]
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$&?%*-+'
    pages = [''.join(random.choice(chars) for _ in range(n)) for _ in range(3)]
    pages.append(target)
    return pages
