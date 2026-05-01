"""Demo mode — scripted showcase sequence as page list."""

def fetch(settings, format_lines, get_rows, get_cols):
    import random
    n = get_rows() * get_cols()
    cols = get_cols()
    colors = 'roygbpw'
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$&?%*-+'

    pages = []

    # Title
    pages.append(format_lines('', 'SPLIT  FLAP', ''))
    pages.append(format_lines('SPLIT  FLAP', 'DISPLAY', ''))

    # Rainbow wave
    for off in range(7):
        pages.append(''.join(colors[(c + off) % 7] for r in range(get_rows()) for c in range(cols)))

    # Feature text
    pages.append(format_lines('HANDMADE WITH', '45 MODULES', 'EACH ONE UNIQUE'))

    # Colour sweep
    for i in range(1, cols + 1):
        pages.append(''.join(colors[i % 7] if c < i else ' ' for r in range(get_rows()) for c in range(cols)))

    # Gradient
    gradient = 'rrrrroooooyyyyygggggbbbbbpppppwwwwwrrrrrooooo'[:n]
    pages.append(gradient.ljust(n))

    # Dimensions
    pages.append(format_lines('3 ROWS  OF 15', 'CHARACTERS', '= 45 TOTAL'))

    # Checker
    for a, b in [('r','b'),('o','p'),('y','g')]:
        pages.append(''.join(a if (r+c)%2==0 else b for r in range(get_rows()) for c in range(cols)))
        pages.append(''.join(b if (r+c)%2==0 else a for r in range(get_rows()) for c in range(cols)))

    # Data apps callout
    pages.append(format_lines('REAL  TIME', 'DATA  APPS', 'BUILT  IN'))

    # Matrix burst
    for _ in range(3):
        pages.append(''.join(random.choice(chars) for _ in range(n)))
    pages.append(format_lines('POWERED BY', 'ARDUINO  &', 'RASPBERRY PI'))

    # Twinkle
    twinkle = 'roygbpw   '
    for _ in range(8):
        pages.append(''.join(random.choice(twinkle) for _ in range(n)))

    # Charset
    pages.append(format_lines('ABCDEFGHIJKLMN', 'OPQRSTUVWXYZ', '0123456789!@#$&'))

    # Matrix burst 2
    for _ in range(3):
        pages.append(''.join(random.choice(chars) for _ in range(n)))
    pages.append(format_lines('', 'SUBSCRIBE!', ''))

    # Closing
    pages.append(format_lines('', 'THANKS  FOR', 'WATCHING!'))

    return pages
