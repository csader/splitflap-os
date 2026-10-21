def fetch(settings, format_lines, get_rows, get_cols, i18n=None):
    from datetime import datetime
    import pytz

    def t(s):
        return i18n.t(s, "time") if i18n is not None else s

    def u(k):                       # localized D/H/M/S suffix (French J for jour, etc.)
        return i18n.unit(k) if i18n is not None else k

    def get_allowed_chars():
        default_chars = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$&()-+=;:%'.,/?*"

        try:
            import __main__

            source_chars = getattr(__main__, 'FLAP_CHARS', '') or default_chars
        except Exception:
            source_chars = default_chars

        # The server stores some flap-only control/color characters in lowercase.
        return {ch.upper() for ch in str(source_chars)}

    allowed_chars = get_allowed_chars()

    def is_enabled(value, default=False):
        if value is None:
            return default
        return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}

    def clean_event(value, fallback='COUNTDOWN'):
        text = str(value or '').strip().upper()
        sanitized = ''.join(ch if ch in allowed_chars else ' ' for ch in text)
        return sanitized.strip() or fallback

    def clean_target(value):
        return str(value or '').strip()

    def build_compact_countdown(total_seconds, cols):
        days, rem = divmod(total_seconds, 86400)
        hrs, rem = divmod(rem, 3600)
        mins, secs = divmod(rem, 60)

        # Keep the most useful leading units that still fit on the sign.
        day_u = u('D')
        sections = [
            f'{days}{day_u}',
            f'{hrs}{u("H")}',
            f'{mins}{u("M")}',
            f'{secs}{u("S")}',
        ]

        text = ''
        for section in sections:
            candidate = section if not text else f'{text} {section}'
            if len(candidate) <= cols:
                text = candidate
            else:
                break

        if text:
            return text
        # At the narrowest widths, preserve the day suffix so the value still has context.
        if cols <= 1:
            return day_u[:cols]
        return f"{str(days)[:cols - len(day_u)]}{day_u}"

    def _pick(cols, *words):
        for w in words:
            if w and cols >= len(w):
                return w
        return (words[-1] or '')[:cols]

    def build_arrived_text(cols):
        return _pick(cols, t('ARRIVED') + '!', t('HERE') + '!', t('NOW') + '!', 'GO')

    def build_celebration_text(cols):
        return _pick(cols, t('CELEBRATE') + '!', t('PARTY') + '!', '')

    def build_remaining_text(cols):
        return _pick(cols, t('REMAINING'), t('LEFT'), '')

    def build_slot_pages(event, target, now, rows, cols):
        diff = target - now
        if diff.total_seconds() <= 0:
            arrived_text = build_arrived_text(cols)
            if rows == 1:
                return [format_lines(event[:cols]), format_lines(arrived_text)]
            if rows == 2:
                return [format_lines(event, arrived_text)]

            celebration_text = build_celebration_text(cols)
            return [format_lines(event, arrived_text, celebration_text)]

        total_seconds = max(0, int(diff.total_seconds()))
        countdown_text = build_compact_countdown(total_seconds, cols)

        if rows == 1:
            return [format_lines(event[:cols]), format_lines(countdown_text[:cols])]
        if rows == 2:
            return [format_lines(event, countdown_text)]
        return [format_lines(event, countdown_text, build_remaining_text(cols))]

    def parse_target(target_str, tz, now, *, allow_default=False):
        if not target_str:
            if not allow_default:
                return None
            # Slot 1 keeps legacy behavior by defaulting to the next New Year.
            return now.replace(
                year=now.year + 1,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

        try:
            target = datetime.fromisoformat(target_str)
        except (TypeError, ValueError):
            return None

        if target.tzinfo is None:
            target = tz.localize(target)
        return target

    try:
        tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    except Exception:
        tz = pytz.timezone('US/Eastern')

    now = datetime.now(tz)
    rows = get_rows()
    cols = get_cols()

    slots = [
        {
            'enabled': is_enabled(settings.get('countdown_enabled', 'on'), default=True),
            'event': clean_event(
                settings.get('countdown_event', 'NEW YEAR'),
                fallback='NEW YEAR',
            ),
            'target': clean_target(settings.get('countdown_target', '')),
            'allow_default_target': True,
        }
    ]

    for index in range(2, 6):
        slots.append(
            {
                'enabled': is_enabled(settings.get(f'countdown_{index}_enabled', 'off')),
                'event': clean_event(settings.get(f'countdown_{index}_event', '')),
                'target': clean_target(settings.get(f'countdown_{index}_target', '')),
                'allow_default_target': False,
            }
        )

    # If every slot is toggled off, still show slot 1 rather than a blank app.
    if not any(slot['enabled'] for slot in slots):
        slots[0]['enabled'] = True

    pages = []
    for slot in slots:
        if not slot['enabled']:
            continue

        if not slot['event'] and not slot['target']:
            continue

        target = parse_target(
            slot['target'],
            tz,
            now,
            allow_default=slot['allow_default_target'],
        )
        if target is None:
            continue

        event = slot['event'] or 'COUNTDOWN'
        pages.extend(build_slot_pages(event, target, now, rows, cols))

    if pages:
        return pages

    if rows == 2:
        return [format_lines('COUNTDOWN', 'CHECK CONFIG')]
    return [format_lines('COUNTDOWN', 'CHECK CONFIG', '')]


def trigger(settings, conditions):
    """Fire when the countdown reaches a configured milestone."""
    from datetime import datetime
    import pytz

    milestone = conditions.get('milestone', '1d')
    target_str = settings.get('countdown_target', '')
    tz = pytz.timezone(settings.get('timezone', 'US/Eastern'))
    now = datetime.now(tz)

    if not target_str:
        return False

    try:
        target = datetime.fromisoformat(target_str)
        if target.tzinfo is None:
            target = tz.localize(target)
        diff = target - now
        total_secs = diff.total_seconds()
        if total_secs <= 0:
            return False

        windows = {
            '30d': (30 * 86400, 29 * 86400),
            '7d':  (7 * 86400,  6 * 86400),
            '1d':  (86400,      82800),
            '1h':  (3600,       3540),
            '0':   (60,         0),
        }
        lo, hi = windows.get(milestone, (86400, 82800))
        in_window = hi <= total_secs <= lo

        state = getattr(trigger, '_state', None)
        if state is None:
            state = {'fired_milestone': None}
            setattr(trigger, '_state', state)

        key = f"{milestone}:{target_str}"
        if in_window and state['fired_milestone'] != key:
            state['fired_milestone'] = key
            return True
    except Exception:
        raise
    return False
