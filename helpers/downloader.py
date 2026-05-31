from __future__ import annotations

import asyncio
import re
from typing import Optional

import yt_dlp

YDL_OPTS_AUDIO = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "extract_flat": False,
    "noplaylist": True,
    "socket_timeout": 15,
}

YDL_OPTS_SEARCH = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "extract_flat": True,
    "noplaylist": True,
    "socket_timeout": 15,
}

YDL_OPTS_PLAYLIST = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": True,
    "socket_timeout": 15,
}


def _is_url(query: str) -> bool:
    return bool(re.match(r"https?://", query.strip()))


async def _run_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)


def _extract_info(url: str, opts: dict) -> Optional[dict]:
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


async def fetch_track(query: str) -> Optional[dict]:
    """Fetch a single track's stream URL and metadata."""
    opts = dict(YDL_OPTS_AUDIO)
    if not _is_url(query):
        query = f"ytsearch1:{query}"
        opts["noplaylist"] = True

    try:
        info = await _run_in_executor(lambda: _extract_info(query, opts))
    except yt_dlp.utils.DownloadError:
        return None

    if not info:
        return None

    if "entries" in info:
        entries = [e for e in info["entries"] if e]
        if not entries:
            return None
        info = entries[0]
        try:
            info = await _run_in_executor(
                lambda: _extract_info(info["url"] if "url" in info else info["webpage_url"], opts)
            )
        except Exception:
            return None

    formats = info.get("formats", [])
    audio_url = None
    for f in reversed(formats):
        if f.get("acodec") != "none" and f.get("vcodec") == "none":
            audio_url = f.get("url")
            break
    if not audio_url:
        audio_url = info.get("url")

    return {
        "title": info.get("title", "Unknown"),
        "url": audio_url,
        "webpage_url": info.get("webpage_url", ""),
        "duration": info.get("duration", 0),
        "thumbnail": info.get("thumbnail", ""),
        "uploader": info.get("uploader", "Unknown"),
        "view_count": info.get("view_count", 0),
        "upload_date": info.get("upload_date", ""),
        "video_id": info.get("id", ""),
    }


async def search_tracks(query: str, limit: int = 5) -> list[dict]:
    """Search YouTube and return up to `limit` results."""
    opts = dict(YDL_OPTS_SEARCH)
    opts["playlistend"] = limit

    try:
        info = await _run_in_executor(
            lambda: _extract_info(f"ytsearch{limit}:{query}", opts)
        )
    except Exception:
        return []

    if not info or "entries" not in info:
        return []

    results = []
    for entry in info["entries"]:
        if not entry:
            continue
        dur = entry.get("duration", 0) or 0
        results.append({
            "title": entry.get("title", "Unknown"),
            "video_id": entry.get("id", ""),
            "webpage_url": entry.get("url") or f"https://youtu.be/{entry.get('id', '')}",
            "duration": dur,
            "uploader": entry.get("uploader", "Unknown"),
            "thumbnail": entry.get("thumbnail", ""),
        })

    return results


async def fetch_playlist(url: str) -> list[dict]:
    """Fetch all tracks from a YouTube playlist."""
    opts = dict(YDL_OPTS_PLAYLIST)

    try:
        info = await _run_in_executor(lambda: _extract_info(url, opts))
    except Exception:
        return []

    if not info or "entries" not in info:
        return []

    tracks = []
    for entry in info["entries"]:
        if not entry:
            continue
        tracks.append({
            "title": entry.get("title", "Unknown"),
            "video_id": entry.get("id", ""),
            "webpage_url": entry.get("url") or f"https://youtu.be/{entry.get('id', '')}",
            "duration": entry.get("duration", 0) or 0,
            "uploader": entry.get("uploader", "Unknown"),
            "thumbnail": entry.get("thumbnail", ""),
        })

    return tracks


async def fetch_similar(title: str, video_id: str = "") -> Optional[dict]:
    """Find a similar song for autoplay."""
    query = f"{title} official audio"
    if video_id:
        query = f"ytsearch2:{query}"
        try:
            opts = dict(YDL_OPTS_SEARCH)
            opts["playlistend"] = 5
            info = await _run_in_executor(lambda: _extract_info(f"ytsearch5:{title}", opts))
            if info and "entries" in info:
                for entry in info["entries"]:
                    if entry and entry.get("id") != video_id:
                        return await fetch_track(
                            entry.get("url") or f"https://youtu.be/{entry['id']}"
                        )
        except Exception:
            pass
    return await fetch_track(query)


def format_duration(seconds: int) -> str:
    if not seconds:
        return "Live"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
