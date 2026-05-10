"""
Inbox app for splitflap-os.

Unlike functional apps that poll external APIs, the inbox app receives
pushed messages via POST /inbox endpoint. This module manages the message
queue and provides pages for display rotation.

The queue is stored in memory and persisted to a JSON file so messages
survive server restarts.
"""
import json
import os
import time
import threading

# Message queue and lock
_messages = []
_lock = threading.Lock()
_persistence_path = os.path.join(os.path.dirname(__file__), 'queue.json')


def _load_queue():
    """Load persisted queue from disk."""
    global _messages
    try:
        if os.path.exists(_persistence_path):
            with open(_persistence_path, 'r') as f:
                _messages = json.load(f)
    except Exception:
        _messages = []


def _save_queue():
    """Persist queue to disk."""
    try:
        with open(_persistence_path, 'w') as f:
            json.dump(_messages, f)
    except Exception:
        pass


def push_message(text, source='unknown', priority='normal', ttl_minutes=None,
                 animation=None, style=None):
    """
    Add a message to the inbox queue.
    Called by the server route handler.

    Args:
        text: Display text (will be uppercased for the flaps)
        source: Identifier for the sender (e.g. 'hermes', 'frigate', 'drift')
        priority: 'low', 'normal', or 'high'
        ttl_minutes: Minutes before message expires (None = use app default)
        animation: Optional animation order override
        style: Optional dict with extra display hints
    
    Returns:
        dict with message id and queue position
    """
    with _lock:
        msg = {
            'id': f"msg_{int(time.time() * 1000)}",
            'text': text,
            'source': source,
            'priority': priority,
            'ttl_minutes': ttl_minutes,
            'animation': animation,
            'style': style or {},
            'created_at': time.time(),
            'read': False,
        }
        _messages.append(msg)
        _save_queue()
        return {'id': msg['id'], 'position': len(_messages)}


def get_messages(max_messages=20, default_ttl=60, priority_filter='all'):
    """
    Get active messages, pruning expired ones.

    Args:
        max_messages: Max queue size
        default_ttl: Default TTL in minutes for messages without explicit TTL
        priority_filter: 'all', 'normal' (normal+high), or 'high' (high only)
    
    Returns:
        List of active message dicts
    """
    now = time.time()
    priority_levels = {'low': 0, 'normal': 1, 'high': 2}
    min_priority = {'all': 0, 'normal': 1, 'high': 2}.get(priority_filter, 0)

    with _lock:
        # Prune expired messages
        active = []
        for msg in _messages:
            ttl = msg.get('ttl_minutes') or default_ttl
            age_minutes = (now - msg['created_at']) / 60
            if age_minutes <= ttl:
                msg_priority = priority_levels.get(msg.get('priority', 'normal'), 1)
                if msg_priority >= min_priority:
                    active.append(msg)

        # Keep only the most recent max_messages
        active = active[-max_messages:]
        _messages.clear()
        _messages.extend(active)
        _save_queue()
        return list(active)


def clear_messages(source=None):
    """Clear all messages, or only from a specific source."""
    with _lock:
        if source:
            _messages[:] = [m for m in _messages if m.get('source') != source]
        else:
            _messages.clear()
        _save_queue()


# Load persisted queue on import
_load_queue()


def fetch(settings, format_lines, get_rows, get_cols):
    """
    Standard splitflap-os app fetch function.
    Returns pages from the message queue.
    """
    max_msgs = int(settings.get('max_messages', '20'))
    default_ttl = int(settings.get('default_ttl', '60'))
    show_time = settings.get('show_timestamp', 'on') == 'on'
    priority_filter = settings.get('priority_filter', 'all')

    messages = get_messages(max_msgs, default_ttl, priority_filter)

    if not messages:
        return [format_lines('INBOX', 'NO MESSAGES')]

    rows = get_rows()
    cols = get_cols()
    pages = []

    # Sort: high priority first, then by time (newest first for display)
    priority_order = {'high': 0, 'normal': 1, 'low': 2}
    messages.sort(key=lambda m: (priority_order.get(m['priority'], 1), -m['created_at']))

    for msg in messages:
        text = msg['text'].upper()
        source = msg.get('source', '').upper()
        priority = msg.get('priority', 'normal')

        # Time formatting
        created = time.localtime(msg['created_at'])
        time_str = time.strftime('%H:%M', created)

        # Priority indicator
        indicator = '!' if priority == 'high' else ''

        if rows == 1:
            line = f"{indicator}{text}"
            if show_time:
                line = f"{time_str} {line}"
            pages.append(format_lines(line))
        elif rows == 2:
            header = f"{indicator}{source}" if source else ''
            if show_time:
                header = f"{time_str} {header}".strip()
            pages.append(format_lines(header, text))
        else:
            header = f"{indicator}{source}" if source else ''
            # Split long text across lines
            if len(text) > cols:
                line1 = text[:cols]
                line2 = text[cols:cols*2]
                pages.append(format_lines(header, line1, line2))
            else:
                footer = time_str if show_time else ''
                pages.append(format_lines(header, text, footer))

    return pages
