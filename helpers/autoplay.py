from __future__ import annotations

from typing import Optional

from helpers.downloader import fetch_similar


async def get_next_similar(title: str, video_id: str = "") -> Optional[dict]:
    """
    Fetch a track similar to the given song for on-demand autoplay.
    Called explicitly via /autoplay command, NOT automatically.
    """
    return await fetch_similar(title, video_id)
