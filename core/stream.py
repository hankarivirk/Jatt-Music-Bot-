"""
Core stream manager — pytgcalls (latest) + pyrogram 2.x
"""
from __future__ import annotations

import asyncio
import time
from typing import Optional, TYPE_CHECKING

from pytgcalls import PyTgCalls
from pytgcalls.exceptions import (
    NotInCallError,
    GroupCallNotFound,
    NoActiveGroupCall,
)
from pytgcalls.types import (
    AudioQuality,
    MediaStream,
    VideoParameters,
)

import database as db
from helpers.logger import log
from helpers.memory import (
    is_muted,
    mem_add_track,
    mem_clear,
    mem_get_queue,
    mem_pop_first,
    mem_set_queue,
    set_active,
    set_inactive,
)
from helpers.pinmanager import unpin_message

if TYPE_CHECKING:
    from pyrogram import Client

# ─── Globals ──────────────────────────────────────────────────────────────────

_call: Optional[PyTgCalls] = None
_bot_client: Optional["Client"] = None

_active_streams: dict[int, "ActiveStream"] = {}
_idle_tasks: dict[int, asyncio.Task] = {}
_np_tasks: dict[int, asyncio.Task] = {}


# ─── ActiveStream ─────────────────────────────────────────────────────────────

class ActiveStream:
    __slots__ = (
        "chat_id", "track", "message_id",
        "started_at", "paused_at", "paused_duration",
        "speed", "volume", "bass", "pitch",
        "reverb", "nightcore",
    )

    def __init__(self, chat_id: int, track: dict, message_id: Optional[int] = None):
        self.chat_id = chat_id
        self.track = track
        self.message_id = message_id
        self.started_at: float = time.monotonic()
        self.paused_at: Optional[float] = None
        self.paused_duration: float = 0.0
        self.speed: float = 1.0
        self.volume: int = 100
        self.bass: int = 0
        self.pitch: float = 1.0
        self.reverb: bool = False
        self.nightcore: bool = False

    @property
    def elapsed(self) -> int:
        base = (self.paused_at or time.monotonic()) - self.started_at
        return max(0, int(base - self.paused_duration))

    @property
    def is_paused(self) -> bool:
        return self.paused_at is not None

    def pause(self) -> None:
        if self.paused_at is None:
            self.paused_at = time.monotonic()

    def resume(self) -> None:
        if self.paused_at is not None:
            self.paused_duration += time.monotonic() - self.paused_at
            self.paused_at = None

    def seek_to(self, seconds: int) -> None:
        self.started_at = time.monotonic() - seconds
        self.paused_duration = 0.0
        if self.paused_at is not None:
            self.paused_at = time.monotonic()


# ─── Initialisation ───────────────────────────────────────────────────────────

def get_pytgcalls() -> PyTgCalls:
    if _call is None:
        raise RuntimeError("PyTgCalls not initialised — call init_stream() first")
    return _call


def init_stream(call: PyTgCalls, bot_client: "Client") -> None:
    global _call, _bot_client
    _call = call
    _bot_client = bot_client
    _register_callbacks(call)


def _register_callbacks(call: PyTgCalls) -> None:

    @call.on_stream_end()
    async def on_stream_end(_, update) -> None:
        chat_id: int = update.chat_id
        log.info(f"Stream ended in chat {chat_id}")
        await _handle_stream_end(chat_id)

    @call.on_left_group_call()
    async def on_left_call(_, update) -> None:
        chat_id: int = update.chat_id
        log.warning(f"Left group call in {chat_id}")
        active = _active_streams.get(chat_id)
        if not active:
            return
        await asyncio.sleep(3)
        try:
            media = _build_media_stream(active.track, active.elapsed, active)
            await call.join_group_call(chat_id, media)
            log.info(f"Auto-reconnected in {chat_id}")
        except Exception as e:
            log.warning(f"Auto-reconnect failed in {chat_id}: {e}")
            _cleanup_chat(chat_id)


# ─── FFmpeg helpers ───────────────────────────────────────────────────────────

def _build_ffmpeg_filter(stream: "ActiveStream") -> str:
    parts: list[str] = []

    if stream.bass > 0:
        parts.append(f"bass=g={stream.bass * 5}")

    speed = stream.speed
    pitch = stream.pitch
    if stream.nightcore:
        speed = 1.25
        pitch = 1.25

    if speed != 1.0:
        if speed < 0.5:
            speed = 0.5
        elif speed > 2.0:
            speed = 2.0
        parts.append(f"atempo={speed:.2f}")

    if pitch != 1.0:
        pitch = max(0.5, min(2.0, pitch))
        parts.append(f"asetrate=44100*{pitch:.3f},aresample=44100")

    if stream.reverb:
        parts.append("aecho=0.8:0.88:60:0.4")

    if stream.volume != 100:
        vol = max(0.0, min(4.0, stream.volume / 100.0))
        parts.append(f"volume={vol:.3f}")

    return ",".join(parts)


def _build_media_stream(
    track: dict,
    seek: int = 0,
    stream: Optional["ActiveStream"] = None,
    video: bool = False,
) -> MediaStream:
    seek_part = f"-ss {seek}" if seek > 0 else ""
    filter_str = _build_ffmpeg_filter(stream) if stream else ""
    filter_part = f"-af \"{filter_str}\"" if filter_str else ""
    parts = [p for p in [seek_part, filter_part] if p]
    ffmpeg_extra = " ".join(parts)

    if video:
        return MediaStream(
            track["url"],
            audio_quality=AudioQuality.STUDIO,
            video_parameters=VideoParameters(1280, 720, 30),
            ffmpeg_parameters=ffmpeg_extra or None,
        )

    return MediaStream(
        track["url"],
        audio_quality=AudioQuality.STUDIO,
        video_only=False,
        ffmpeg_parameters=ffmpeg_extra or None,
    )


# ─── Playback control ─────────────────────────────────────────────────────────

async def play(
    chat_id: int,
    track: dict,
    message_id: Optional[int] = None,
    video: bool = False,
    seek: int = 0,
) -> None:
    call = get_pytgcalls()
    stream = ActiveStream(chat_id, track, message_id)
    _active_streams[chat_id] = stream
    set_active(chat_id)

    media = _build_media_stream(track, seek, stream, video)

    try:
        await call.join_group_call(chat_id, media)
    except GroupCallNotFound:
        await call.change_stream(chat_id, media)
    except NoActiveGroupCall:
        raise RuntimeError("No active voice chat in this group. Start one first.")
    except Exception:
        raise

    if seek > 0:
        stream.seek_to(seek)

    _cancel_idle(chat_id)
    await db.record_play(chat_id, track.get("requester_id", 0), track["title"])


async def pause(chat_id: int) -> bool:
    stream = _active_streams.get(chat_id)
    if not stream or stream.is_paused:
        return False
    call = get_pytgcalls()
    await call.pause_stream(chat_id)
    stream.pause()
    return True


async def resume(chat_id: int) -> bool:
    stream = _active_streams.get(chat_id)
    if not stream or not stream.is_paused:
        return False
    call = get_pytgcalls()
    await call.resume_stream(chat_id)
    stream.resume()
    return True


async def mute(chat_id: int) -> bool:
    if not _active_streams.get(chat_id):
        return False
    call = get_pytgcalls()
    await call.mute_stream(chat_id)
    from helpers.memory import set_muted
    set_muted(chat_id, True)
    return True


async def unmute(chat_id: int) -> bool:
    if not _active_streams.get(chat_id):
        return False
    call = get_pytgcalls()
    await call.unmute_stream(chat_id)
    from helpers.memory import set_muted
    set_muted(chat_id, False)
    return True


async def stop(chat_id: int, client: Optional["Client"] = None) -> None:
    call = get_pytgcalls()
    _cleanup_chat(chat_id)
    try:
        await call.leave_group_call(chat_id)
    except (GroupCallNotFound, NotInCallError, NoActiveGroupCall):
        pass
    except Exception as e:
        log.warning(f"stop(): leave_group_call error in {chat_id}: {e}")
    await db.clear_queue(chat_id)
    c = client or _bot_client
    if c:
        await unpin_message(c, chat_id)


async def seek(chat_id: int, seconds: int) -> bool:
    stream = _active_streams.get(chat_id)
    if not stream:
        return False
    call = get_pytgcalls()
    media = _build_media_stream(stream.track, seconds, stream, stream.track.get("video", False))
    await call.change_stream(chat_id, media)
    stream.seek_to(seconds)
    return True


async def _apply_effects(chat_id: int) -> None:
    stream = _active_streams.get(chat_id)
    if not stream:
        return
    call = get_pytgcalls()
    elapsed = stream.elapsed
    media = _build_media_stream(stream.track, elapsed, stream, stream.track.get("video", False))
    await call.change_stream(chat_id, media)
    stream.seek_to(elapsed)


async def set_volume(chat_id: int, volume: int) -> bool:
    stream = _active_streams.get(chat_id)
    if not stream:
        return False
    stream.volume = max(0, min(200, volume))
    await _apply_effects(chat_id)
    return True


async def set_speed(chat_id: int, speed: float) -> bool:
    stream = _active_streams.get(chat_id)
    if not stream:
        return False
    stream.speed = max(0.5, min(2.0, speed))
    stream.nightcore = False
    await _apply_effects(chat_id)
    return True


async def set_bass(chat_id: int, level: int) -> bool:
    stream = _active_streams.get(chat_id)
    if not stream:
        return False
    stream.bass = max(0, min(10, level))
    await _apply_effects(chat_id)
    return True


async def set_pitch(chat_id: int, pitch: float) -> bool:
    stream = _active_streams.get(chat_id)
    if not stream:
        return False
    stream.pitch = max(0.5, min(2.0, pitch))
    stream.nightcore = False
    await _apply_effects(chat_id)
    return True


async def toggle_reverb(chat_id: int) -> bool:
    stream = _active_streams.get(chat_id)
    if not stream:
        return False
    stream.reverb = not stream.reverb
    await _apply_effects(chat_id)
    return stream.reverb


async def toggle_nightcore(chat_id: int) -> bool:
    stream = _active_streams.get(chat_id)
    if not stream:
        return False
    stream.nightcore = not stream.nightcore
    if stream.nightcore:
        stream.speed = 1.25
        stream.pitch = 1.25
    else:
        stream.speed = 1.0
        stream.pitch = 1.0
    await _apply_effects(chat_id)
    return stream.nightcore


async def normalise(chat_id: int) -> bool:
    stream = _active_streams.get(chat_id)
    if not stream:
        return False
    stream.speed = 1.0
    stream.pitch = 1.0
    stream.bass = 0
    stream.reverb = False
    stream.nightcore = False
    stream.volume = 100
    await _apply_effects(chat_id)
    return True


# ─── Stream-end handler ───────────────────────────────────────────────────────

async def _handle_stream_end(chat_id: int) -> None:
    stream = _active_streams.get(chat_id)
    if not stream:
        return

    loop_mode = await db.get_setting(chat_id, "loop_mode")

    if loop_mode == "track":
        try:
            await play(chat_id, stream.track, message_id=stream.message_id,
                       video=stream.track.get("video", False))
        except Exception as e:
            log.warning(f"Loop-track replay failed in {chat_id}: {e}")
        return

    if loop_mode == "queue":
        queue = await db.get_queue(chat_id)
        if len(queue) > 1:
            current = queue[0]
            await db.remove_from_queue(chat_id, 1)
            await db.add_to_queue(chat_id, current)
            queue = await db.get_queue(chat_id)
            mem_set_queue(chat_id, queue)

    await db.add_to_history(chat_id, stream.track)
    await db.remove_from_queue(chat_id, 1)
    mem_pop_first(chat_id)

    next_queue = await db.get_queue(chat_id)
    if not next_queue:
        _active_streams.pop(chat_id, None)
        set_inactive(chat_id)
        stop_np_updater(chat_id)
        vc247 = await db.get_setting(chat_id, "vc247")
        if vc247:
            return

        async def _idle_leave(cid: int) -> None:
            if not _active_streams.get(cid):
                try:
                    call = get_pytgcalls()
                    await call.leave_group_call(cid)
                except Exception:
                    pass
                if _bot_client:
                    try:
                        await _bot_client.send_message(
                            cid,
                            "⏹ <b>Queue Ended</b>\nAll songs played. Left the voice chat."
                        )
                    except Exception:
                        pass

        start_idle_timer(chat_id, _idle_leave)
        return

    next_track = next_queue[0]

    if next_track.get("webpage_url"):
        try:
            from helpers.downloader import fetch_track
            fresh = await fetch_track(next_track["webpage_url"])
            if fresh and fresh.get("url"):
                next_track["url"] = fresh["url"]
                next_track["thumbnail"] = fresh.get("thumbnail", next_track.get("thumbnail", ""))
        except Exception as e:
            log.warning(f"URL refresh failed for {next_track['title']}: {e}")

    try:
        await play(chat_id, next_track, video=next_track.get("video", False))
    except Exception as e:
        log.error(f"Failed to play next track in {chat_id}: {e}")
        return

    if _bot_client:
        try:
            await _send_np_card_internal(chat_id, next_track)
        except Exception as e:
            log.warning(f"NP card send failed: {e}")


async def _send_np_card_internal(chat_id: int, track: dict) -> None:
    from helpers.thumbnails import generate_now_playing_card
    from helpers.pinmanager import pin_message
    from plugins.utils import now_playing_keyboard
    from helpers.downloader import format_duration

    client = _bot_client
    if not client:
        return

    buf = await generate_now_playing_card(
        title=track["title"],
        uploader=track.get("uploader", "Unknown"),
        thumbnail_url=track.get("thumbnail", ""),
        requester=track.get("requester", "Unknown"),
        elapsed=0,
        duration=track.get("duration", 0),
    )
    kb = now_playing_keyboard(chat_id)
    np_msg = await client.send_photo(
        chat_id,
        photo=buf,
        caption=(
            f"<b>Now Playing</b>\n"
            f"<b>{track['title']}</b>\n"
            f"{format_duration(track.get('duration', 0))}"
        ),
        reply_markup=kb,
    )
    stream = _active_streams.get(chat_id)
    if stream:
        stream.message_id = np_msg.id
    await pin_message(client, chat_id, np_msg.id)


# ─── Queue helpers ────────────────────────────────────────────────────────────

def get_active(chat_id: int) -> Optional[ActiveStream]:
    return _active_streams.get(chat_id)


async def skip_to_next(chat_id: int, client: Optional["Client"] = None) -> Optional[dict]:
    queue = await db.get_queue(chat_id)
    if not queue or len(queue) < 2:
        return None

    current = queue[0]
    await db.add_to_history(chat_id, current)
    await db.remove_from_queue(chat_id, 1)
    mem_pop_first(chat_id)

    queue = await db.get_queue(chat_id)
    if not queue:
        return None

    next_track = queue[0]

    if next_track.get("webpage_url"):
        try:
            from helpers.downloader import fetch_track
            fresh = await fetch_track(next_track["webpage_url"])
            if fresh and fresh.get("url"):
                next_track["url"] = fresh["url"]
        except Exception:
            pass

    await play(chat_id, next_track, video=next_track.get("video", False))
    return next_track


# ─── Timers ───────────────────────────────────────────────────────────────────

def _cancel_idle(chat_id: int) -> None:
    task = _idle_tasks.pop(chat_id, None)
    if task and not task.done():
        task.cancel()


def _cancel_np_task(chat_id: int) -> None:
    task = _np_tasks.pop(chat_id, None)
    if task and not task.done():
        task.cancel()


def start_idle_timer(chat_id: int, callback) -> None:
    _cancel_idle(chat_id)

    async def _timer():
        from config import IDLE_TIMEOUT
        await asyncio.sleep(IDLE_TIMEOUT)
        try:
            await callback(chat_id)
        except Exception as e:
            log.warning(f"Idle timer callback error in {chat_id}: {e}")

    _idle_tasks[chat_id] = asyncio.create_task(_timer())


def start_np_updater(chat_id: int, callback) -> None:
    _cancel_np_task(chat_id)

    async def _updater():
        from config import NP_UPDATE_INTERVAL
        while True:
            await asyncio.sleep(NP_UPDATE_INTERVAL)
            try:
                stream = _active_streams.get(chat_id)
                if not stream:
                    break
                await callback(chat_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.warning(f"NP updater error in {chat_id}: {e}")
                break

    _np_tasks[chat_id] = asyncio.create_task(_updater())


def stop_np_updater(chat_id: int) -> None:
    _cancel_np_task(chat_id)


def _cleanup_chat(chat_id: int) -> None:
    _active_streams.pop(chat_id, None)
    _cancel_idle(chat_id)
    _cancel_np_task(chat_id)
    set_inactive(chat_id)
