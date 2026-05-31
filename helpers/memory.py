"""
In-memory state layer. Hot-path queue and chat state live here for speed.
MongoDB is written to asynchronously for persistence; reads fall back to DB.
"""
from __future__ import annotations

from typing import Optional

# Active queue per chat_id: list of track dicts, index 0 = now playing
_queue: dict[int, list[dict]] = {}

# Per-chat mute state (VC audio muted)
_muted: dict[int, bool] = {}

# Active chat IDs currently streaming
_active_chats: set[int] = set()


# ─── Queue ────────────────────────────────────────────────────────────────────

def mem_get_queue(chat_id: int) -> list[dict]:
    return _queue.get(chat_id, [])


def mem_set_queue(chat_id: int, tracks: list[dict]) -> None:
    if tracks:
        _queue[chat_id] = tracks
    else:
        _queue.pop(chat_id, None)


def mem_add_track(chat_id: int, track: dict) -> int:
    if chat_id not in _queue:
        _queue[chat_id] = []
    track["position"] = len(_queue[chat_id]) + 1
    _queue[chat_id].append(track)
    return track["position"]


def mem_pop_first(chat_id: int) -> Optional[dict]:
    if chat_id not in _queue or not _queue[chat_id]:
        return None
    track = _queue[chat_id].pop(0)
    _reindex(chat_id)
    return track


def mem_remove(chat_id: int, position: int) -> bool:
    q = _queue.get(chat_id, [])
    if not q or position < 1 or position > len(q):
        return False
    q.pop(position - 1)
    _reindex(chat_id)
    if not q:
        _queue.pop(chat_id, None)
    return True


def mem_move(chat_id: int, from_pos: int, to_pos: int) -> bool:
    q = _queue.get(chat_id, [])
    n = len(q)
    if not (1 <= from_pos <= n and 1 <= to_pos <= n):
        return False
    track = q.pop(from_pos - 1)
    q.insert(to_pos - 1, track)
    _reindex(chat_id)
    return True


def mem_clear(chat_id: int) -> None:
    _queue.pop(chat_id, None)


def mem_shuffle(chat_id: int) -> None:
    import random
    q = _queue.get(chat_id, [])
    if len(q) < 2:
        return
    first = q[0]
    rest = q[1:]
    random.shuffle(rest)
    _queue[chat_id] = [first] + rest
    _reindex(chat_id)


def _reindex(chat_id: int) -> None:
    for i, t in enumerate(_queue.get(chat_id, [])):
        t["position"] = i + 1


# ─── Chat state ───────────────────────────────────────────────────────────────

def set_active(chat_id: int) -> None:
    _active_chats.add(chat_id)


def set_inactive(chat_id: int) -> None:
    _active_chats.discard(chat_id)
    _queue.pop(chat_id, None)
    _muted.pop(chat_id, None)


def is_active(chat_id: int) -> bool:
    return chat_id in _active_chats


def set_muted(chat_id: int, muted: bool) -> None:
    _muted[chat_id] = muted


def is_muted(chat_id: int) -> bool:
    return _muted.get(chat_id, False)
