from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.types import Message

import database as db
from core import stream as sm
from helpers.antiflood import is_flooded, remaining_cooldown
from helpers.downloader import fetch_playlist, fetch_track, format_duration
from helpers.pinmanager import pin_message
from helpers.thumbnails import generate_now_playing_card
from plugins.utils import maintenance_check


def register(app: Client) -> None:

    @app.on_message(filters.command("playlist") & filters.group)
    @maintenance_check
    async def playlist_cmd(client: Client, message: Message):
        user = message.from_user
        chat_id = message.chat.id

        if is_flooded(chat_id, user.id):
            secs = remaining_cooldown(chat_id, user.id)
            await message.reply(f"Slow down! Wait {secs:.1f}s.")
            return

        args = message.command[1:]
        if not args:
            await message.reply("Usage: /playlist <YouTube playlist URL>")
            return

        url = args[0].strip()
        if "list=" not in url and "playlist" not in url.lower():
            await message.reply("Please provide a valid YouTube playlist URL.")
            return

        await db.upsert_user(user.id, user.first_name)
        await db.upsert_chat(chat_id, message.chat.title or "")

        if await db.is_banned_in_chat(chat_id, user.id):
            await message.reply("You are banned from using the bot in this group.")
            return

        msg = await message.reply("Loading playlist, this may take a moment...")

        tracks = await fetch_playlist(url)
        if not tracks:
            await msg.edit("Could not load the playlist. Make sure it's public.")
            return

        added = 0
        current_queue = await db.get_queue(chat_id)
        existing_ids = {t.get("video_id") for t in current_queue if t.get("video_id")}

        for t in tracks:
            if t.get("video_id") in existing_ids:
                continue
            track = {
                "title": t["title"],
                "url": t.get("webpage_url", f"https://youtu.be/{t.get('video_id', '')}"),
                "webpage_url": t.get("webpage_url", ""),
                "duration": t.get("duration", 0),
                "thumbnail": t.get("thumbnail", ""),
                "uploader": t.get("uploader", "Unknown"),
                "video_id": t.get("video_id", ""),
                "requester": user.first_name,
                "requester_id": user.id,
                "video": False,
            }
            await db.add_to_queue(chat_id, track)
            existing_ids.add(t.get("video_id"))
            added += 1

        if added == 0:
            await msg.edit("All tracks from the playlist are already in the queue.")
            return

        if not sm.get_active(chat_id):
            queue = await db.get_queue(chat_id)
            if not queue:
                await msg.edit("Playlist added but queue is empty.")
                return
            first_track_data = queue[0]
            info = await fetch_track(
                first_track_data.get("webpage_url") or
                f"https://youtu.be/{first_track_data.get('video_id', '')}"
            )
            if info:
                first_track_data["url"] = info["url"]
                first_track_data["thumbnail"] = info.get("thumbnail", "")
                first_track_data["uploader"] = info.get("uploader", "Unknown")
                from database import get_db
                await get_db().queue.update_one(
                    {"chat_id": chat_id},
                    {"$set": {"tracks.0": first_track_data}},
                )

            await sm.play(chat_id, first_track_data, video=False)
            await msg.delete()

            buf = await generate_now_playing_card(
                title=first_track_data["title"],
                uploader=first_track_data.get("uploader", "Unknown"),
                thumbnail_url=first_track_data.get("thumbnail", ""),
                requester=first_track_data.get("requester", "Unknown"),
                elapsed=0,
                duration=first_track_data.get("duration", 0),
            )
            from plugins.utils import now_playing_keyboard
            kb = now_playing_keyboard(chat_id)
            np_msg = await client.send_photo(
                chat_id,
                photo=buf,
                caption=(
                    f"<b>Playlist loaded — {added} tracks added</b>\n\n"
                    f"<b>Now Playing</b>\n<b>{first_track_data['title']}</b>"
                ),
                reply_markup=kb,
            )
            await pin_message(client, chat_id, np_msg.id)

            async def _on_idle(cid: int):
                active = sm.get_active(cid)
                if not active:
                    return
                await sm.stop(cid, client)
                try:
                    await client.send_message(cid, "Left voice chat due to inactivity.")
                except Exception:
                    pass

            sm.start_idle_timer(chat_id, _on_idle)
        else:
            await msg.edit(
                f"<b>Playlist loaded</b>\n{added} tracks added to queue."
            )
