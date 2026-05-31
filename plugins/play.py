from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto, Message

import database as db
from core import stream as sm
from helpers.antiflood import is_flooded, remaining_cooldown
from helpers.downloader import fetch_track, format_duration
from helpers.memory import mem_add_track, mem_get_queue, set_active
from helpers.pinmanager import pin_message
from helpers.thumbnails import generate_now_playing_card
from plugins.utils import maintenance_check, now_playing_keyboard


def _make_track(info: dict, user, video: bool = False) -> dict:
    """Build a track dict from yt-dlp info and requesting user."""
    return {
        "title": info["title"],
        "url": info["url"],
        "webpage_url": info.get("webpage_url", ""),
        "duration": info.get("duration", 0),
        "thumbnail": info.get("thumbnail", ""),
        "uploader": info.get("uploader", "Unknown"),
        "video_id": info.get("video_id", ""),
        "requester": user.first_name,
        "requester_id": user.id,
        "video": video,
    }


async def _send_np_card(client: Client, chat_id: int, track: dict) -> None:
    """Send the Now Playing card, pin it, and start the NP updater."""
    stream = sm.get_active(chat_id)
    elapsed = stream.elapsed if stream else 0

    buf = await generate_now_playing_card(
        title=track["title"],
        uploader=track.get("uploader", "Unknown"),
        thumbnail_url=track.get("thumbnail", ""),
        requester=track.get("requester", "Unknown"),
        elapsed=elapsed,
        duration=track.get("duration", 0),
    )
    kb = now_playing_keyboard(chat_id, paused=False)
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

    if stream:
        stream.message_id = np_msg.id

    await pin_message(client, chat_id, np_msg.id)

    # Start NP card updater
    async def _np_update(cid: int) -> None:
        s = sm.get_active(cid)
        if not s:
            return
        try:
            buf2 = await generate_now_playing_card(
                title=s.track["title"],
                uploader=s.track.get("uploader", "Unknown"),
                thumbnail_url=s.track.get("thumbnail", ""),
                requester=s.track.get("requester", "Unknown"),
                elapsed=s.elapsed,
                duration=s.track.get("duration", 0),
            )
            await np_msg.edit_media(
                media=InputMediaPhoto(media=buf2),
                reply_markup=now_playing_keyboard(cid, paused=s.is_paused),
            )
        except Exception:
            sm.stop_np_updater(cid)

    sm.start_np_updater(chat_id, _np_update)


def _is_duplicate(queue: list[dict], video_id: str) -> bool:
    if not video_id:
        return False
    return any(t.get("video_id") == video_id for t in queue)


async def _play_track(
    client: Client,
    message: Message,
    query: str,
    video: bool = False,
    force: bool = False,
) -> None:
    chat_id = message.chat.id
    user = message.from_user

    if is_flooded(chat_id, user.id):
        secs = remaining_cooldown(chat_id, user.id)
        await message.reply(f"Slow down! Wait {secs:.1f}s before using play again.")
        return

    await db.upsert_user(user.id, user.first_name)
    await db.upsert_chat(chat_id, message.chat.title or "")

    if await db.is_banned_in_chat(chat_id, user.id):
        await message.reply("You are banned from using the bot in this group.")
        return

    searching_msg = await message.reply("Searching...")

    info = await fetch_track(query)
    if not info:
        await searching_msg.edit("Could not find that track. Try a different query.")
        return

    track = _make_track(info, user, video)

    # Use memory queue for fast duplicate check
    current_queue = mem_get_queue(chat_id)
    if not current_queue:
        # Fall back to DB if memory is cold
        current_queue = await db.get_queue(chat_id)

    # Force play: insert at front, skip current
    if force and sm.get_active(chat_id):
        from database import get_db
        if current_queue:
            first = current_queue[0]
            await db.add_to_history(chat_id, first)
            await db.remove_from_queue(chat_id, 1)

        # Insert new track at position 1
        fresh_queue = await db.get_queue(chat_id)
        fresh_queue.insert(0, track)
        for i, t in enumerate(fresh_queue):
            t["position"] = i + 1
        await get_db().queue.update_one(
            {"chat_id": chat_id}, {"$set": {"tracks": fresh_queue}}, upsert=True
        )
        from helpers.memory import mem_set_queue
        mem_set_queue(chat_id, fresh_queue)

        try:
            await sm.play(chat_id, track, video=video)
        except RuntimeError as e:
            await searching_msg.edit(f"Error: {e}")
            return
        await searching_msg.delete()
        await _send_np_card(client, chat_id, track)
        return

    # Normal play: check duplicate then add to queue
    if _is_duplicate(current_queue, track.get("video_id", "")):
        await searching_msg.edit("This song is already in the queue.")
        return

    pos = await db.add_to_queue(chat_id, track)
    mem_add_track(chat_id, track)

    is_playing = sm.get_active(chat_id) is not None

    if not is_playing:
        try:
            await sm.play(chat_id, track, video=video)
        except RuntimeError as e:
            await searching_msg.edit(f"Error: {e}")
            return

        set_active(chat_id)
        await searching_msg.delete()
        await _send_np_card(client, chat_id, track)

        # Set idle timer (respects 247 mode)
        async def _on_idle(cid: int) -> None:
            vc247 = await db.get_setting(cid, "vc247")
            if vc247:
                return
            if not sm.get_active(cid):
                return
            await sm.stop(cid, client)
            try:
                await client.send_message(cid, "Left voice chat due to inactivity.")
            except Exception:
                pass

        sm.start_idle_timer(chat_id, _on_idle)
    else:
        await searching_msg.edit(
            f"Added to queue at position <b>{pos}</b>\n"
            f"<b>{track['title']}</b> [{format_duration(track.get('duration', 0))}]"
        )


def register(app: Client) -> None:

    @app.on_message(filters.command(["play", "song"]) & filters.group)
    @maintenance_check
    async def play_cmd(client: Client, message: Message):
        query = " ".join(message.command[1:]).strip()
        if not query and message.reply_to_message and message.reply_to_message.text:
            query = message.reply_to_message.text.strip()
        if not query:
            await message.reply("Usage: /play <song name or YouTube URL>")
            return
        await _play_track(client, message, query, video=False, force=False)

    @app.on_message(filters.command("playforce") & filters.group)
    @maintenance_check
    async def playforce_cmd(client: Client, message: Message):
        from plugins.utils import is_dj_or_admin
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("This command is for DJs and admins only.")
            return
        query = " ".join(message.command[1:]).strip()
        if not query:
            await message.reply("Usage: /playforce <song name or YouTube URL>")
            return
        await _play_track(client, message, query, video=False, force=True)

    @app.on_message(filters.command("vplay") & filters.group)
    @maintenance_check
    async def vplay_cmd(client: Client, message: Message):
        query = " ".join(message.command[1:]).strip()
        if not query:
            await message.reply("Usage: /vplay <song name or YouTube URL>")
            return
        await _play_track(client, message, query, video=True, force=False)
