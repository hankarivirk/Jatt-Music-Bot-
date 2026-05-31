import time
from collections import defaultdict

from config import ANTI_FLOOD_SECONDS

_last_used: dict[tuple[int, int], float] = defaultdict(float)


def is_flooded(chat_id: int, user_id: int) -> bool:
    key = (chat_id, user_id)
    now = time.monotonic()
    if now - _last_used[key] < ANTI_FLOOD_SECONDS:
        return True
    _last_used[key] = now
    return False


def remaining_cooldown(chat_id: int, user_id: int) -> float:
    key = (chat_id, user_id)
    remaining = ANTI_FLOOD_SECONDS - (time.monotonic() - _last_used[key])
    return max(0.0, remaining)
