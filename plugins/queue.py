from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

import database as db
from core import stream as sm
from helpers.downloader import fetch_track, format_duration
from helpers.memory import mem_clear, mem_pop_first, mem_set_queue
from helpers.pinmanager import pin_message
from helpers.thumbnails import generate_now_playing_card
from plugins.utils import (
    format_track,
    is_dj_or_admin,
    maintenance_check,
    now_playing_keyboard,
    queue_keyboard,
)

_PER_PAGE = 10


def register(app: Client) -> None:

    @app.on_message(filters.command("np") & filters.group)
    @maintenance_check
    async def np_cmd(client: Client, message: Message):
        chat_id = message.chat.id
        active = sm.get_active(chat_id)
        if not active:
            await message.reply("Nothing is playing right now.")
            return
        track = active.track
        buf = await generate_now_playing_card(
            title=track["title"],
            uploader=track.get("uploader", "Unknown"),
            thumbnail_url=track.get("thumbnail", ""),
            requester=track.get("requester", "Unknown"),
            elapsed=active.elapsed,
            duration=track.get("duration", 0),
        )
        kb = now_playing_keyboard(chat_id, paused=active.is_paused)
        await client.send_photo(
            chat_id,
            photo=buf,
            caption=(
                f"<b>Now Playing</b>\n"
                f"<b>{track['title']}</b>\n"
                f"{format_duration(active.elapsed)} / {format_duration(track.get('duration', 0))}"
            ),
            reply_markup=kb,
        )

    @app.on_message(filters.command("queue") & filters.group)
    @maintenance_check
    async def queue_cmd(client: Client, message: Message):
        chat_id = message.chat.id
        queue = await db.get_queue(chat_id)
        if not queue:
            await message.reply("The queue is empty.")
            return
        page = 1
        total_pages = max(1, (len(queue) + _PER_PAGE - 1) // _PER_PAGE)
        start = 0
        lines = [format_track(t, i + 1) for i, t in enumerate(queue[start:start + _PER_PAGE])]
        text = f"<b>Queue — {len(queue)} track(s)</b>\n\n" + "\n".join(lines)
        await message.reply(text, reply_markup=queue_keyboard(chat_id, page, total_pages))

    @app.on_callback_query(filters.regex(r"^queue_(prev|next)_"))
    async def queue_page_cb(client: Client, cb: CallbackQuery):
        parts = cb.data.split("_")
        direction = parts[1]
        chat_id = int(parts[2])
        current_page = int(parts[3])
        new_page = current_page - 1 if direction == "prev" else current_page + 1

        queue = await db.get_queue(chat_id)
        if not queue:
            await cb.answer("Queue is empty.", show_alert=True)
            return

        total_pages = max(1, (len(queue) + _PER_PAGE - 1) // _PER_PAGE)
        new_page = max(1, min(new_page, total_pages))
        start = (new_page - 1) * _PER_PAGE
        lines = [format_track(t, i + start + 1) for i, t in enumerate(queue[start:start + _PER_PAGE])]
        text = f"<b>Queue — {len(queue)} track(s)</b>\n\n" + "\n".join(lines)
        try:
            await cb.message.edit(text, reply_markup=queue_keyboard(chat_id, new_page, total_pages))
        except Exception:
            pass
        await cb.answer()

    @app.on_message(filters.command("history") & filters.group)
    @maintenance_check
    async def history_cmd(client: Client, message: Message):
        history = await db.get_history(message.chat.id)
        if not history:
            await message.reply("No play history yet.")
            return
        lines = [
            f"{i + 1}. <b>{t['title']}</b> [{format_duration(t.get('duration', 0))}]"
            for i, t in enumerate(history)
        ]
        await message.reply("<b>Last 10 Played</b>\n\n" + "\n".join(lines))

    @app.on_message(filters.command("replay") & filters.group)
    @maintenance_check
    async def replay_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can replay.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("Nothing is playing.")
            return
        await sm.seek(message.chat.id, 0)
        await message.reply("Replaying from the beginning.")

    @app.on_message(filters.command("skipto") & filters.group)
    @maintenance_check
    async def skipto_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can use skipto.")
            return
        args = message.command[1:]
        if not args:
            await message.reply("Usage: /skipto <track number>")
            return
        try:
            pos = int(args[0])
        except ValueError:
            await message.reply("Invalid track number.")
            return
        chat_id = message.chat.id
        queue = await db.get_queue(chat_id)
        if not queue or pos < 1 or pos > len(queue):
            await message.reply(f"Invalid position. Queue has {len(queue)} track(s).")
            return
        if pos == 1:
            await message.reply("Track 1 is already playing.")
            return

        # Archive skipped tracks and remove them
        skipped = queue[:pos - 1]
        for t in skipped:
            await db.add_to_history(chat_id, t)
        for _ in range(pos - 1):
            await db.remove_from_queue(chat_id, 1)
            mem_pop_first(chat_id)

        queue = await db.get_queue(chat_id)
        if not queue:
            await sm.stop(chat_id, client)
            await message.reply("Queue ended.")
            return

        next_track = queue[0]

        # Refresh URL
        if next_track.get("webpage_url"):
            try:
                fresh = await fetch_track(next_track["webpage_url"])
                if fresh and fresh.get("url"):
                    next_track["url"] = fresh["url"]
                    next_track["thumbnail"] = fresh.get("thumbnail", next_track.get("thumbnail", ""))
            except Exception:
                pass

        try:
            await sm.play(chat_id, next_track, video=next_track.get("video", False))
        except Exception as e:
            await message.reply(f"Error starting track: {e}")
            return

        buf = await generate_now_playing_card(
            title=next_track["title"],
            uploader=next_track.get("uploader", "Unknown"),
            thumbnail_url=next_track.get("thumbnail", ""),
            requester=next_track.get("requester", "Unknown"),
            elapsed=0,
            duration=next_track.get("duration", 0),
        )
        kb = now_playing_keyboard(chat_id)
        np_msg = await client.send_photo(
            chat_id,
            photo=buf,
            caption=f"<b>Skipped to track {pos}</b>\n<b>{next_track['title']}</b>",
            reply_markup=kb,
        )
        await pin_message(client, chat_id, np_msg.id)
        stream = sm.get_active(chat_id)
        if stream:
            stream.message_id = np_msg.id

    @app.on_message(filters.command("songinfo") & filters.group)
    @maintenance_check
    async def songinfo_cmd(client: Client, message: Message):
        active = sm.get_active(message.chat.id)
        if not active:
            await message.reply("Nothing is playing.")
            return
        track = active.track
        from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        views = track.get("view_count", 0)
        views_str = f"{views:,}" if views else "N/A"
        upload_date = track.get("upload_date", "")
        if len(upload_date) == 8:
            upload_date = f"{upload_date[6:]}/{upload_date[4:6]}/{upload_date[:4]}"
        text = (
            f"<b>Song Information</b>\n\n"
            f"<b>Title:</b> {track['title']}\n"
            f"<b>Artist:</b> {track.get('uploader', 'Unknown')}\n"
            f"<b>Duration:</b> {format_duration(track.get('duration', 0))}\n"
            f"<b>Views:</b> {views_str}\n"
            f"<b>Published:</b> {upload_date or 'N/A'}\n"
            f"<b>Requested by:</b> {track.get('requester', 'Unknown')}"
        )
        kb = None
        if track.get("webpage_url"):
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Open on YouTube", url=track["webpage_url"])]
            ])
        await message.reply(text, reply_markup=kb)

    @app.on_message(filters.command("mysongs") & filters.group)
    @maintenance_check
    async def mysongs_cmd(client: Client, message: Message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        songs = await db.user_songs(chat_id, user_id)
        if not songs:
            await message.reply("You haven't requested any songs in this group yet.")
            return
        lines = [f"{i + 1}. <b>{s['_id']}</b> ({s['count']} plays)" for i, s in enumerate(songs)]
        await message.reply("<b>Your most played songs</b>\n\n" + "\n".join(lines))

    @app.on_message(filters.command("remove") & filters.group)
    @maintenance_check
    async def remove_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can remove tracks.")
            return
        args = message.command[1:]
        if not args:
            await message.reply("Usage: /remove <position>")
            return
        try:
            pos = int(args[0])
        except ValueError:
            await message.reply("Invalid position.")
            return
        chat_id = message.chat.id
        if pos == 1 and sm.get_active(chat_id):
            await message.reply("Cannot remove the currently playing track. Use /skip.")
            return
        ok = await db.remove_from_queue(chat_id, pos)
        if ok:
            from helpers.memory import mem_remove
            mem_remove(chat_id, pos)
        await message.reply(f"Removed track at position {pos}." if ok else "Invalid position.")

    @app.on_message(filters.command("move") & filters.group)
    @maintenance_check
    async def move_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can move tracks.")
            return
        args = message.command[1:]
        if len(args) < 2:
            await message.reply("Usage: /move <from> <to>")
            return
        try:
            from_pos, to_pos = int(args[0]), int(args[1])
        except ValueError:
            await message.reply("Invalid positions.")
            return
        chat_id = message.chat.id
        ok = await db.move_in_queue(chat_id, from_pos, to_pos)
        if ok:
            from helpers.memory import mem_move
            mem_move(chat_id, from_pos, to_pos)
        await message.reply(
            f"Moved track from position {from_pos} to {to_pos}." if ok else "Invalid positions."
        )

    @app.on_message(filters.command("autoplay") & filters.group)
    @maintenance_check
    async def autoplay_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can use autoplay.")
            return
        chat_id = message.chat.id
        active = sm.get_active(chat_id)
        if not active:
            await message.reply("Nothing is playing. Start a song first.")
            return

        searching_msg = await message.reply("Finding a similar song...")

        from helpers.autoplay import get_next_similar
        track_info = await get_next_similar(
            active.track["title"], active.track.get("video_id", "")
        )
        if not track_info:
            await searching_msg.edit("Could not find a similar song.")
            return

        user = message.from_user
        new_track = {
            "title": track_info["title"],
            "url": track_info["url"],
            "webpage_url": track_info.get("webpage_url", ""),
            "duration": track_info.get("duration", 0),
            "thumbnail": track_info.get("thumbnail", ""),
            "uploader": track_info.get("uploader", "Unknown"),
            "video_id": track_info.get("video_id", ""),
            "requester": user.first_name,
            "requester_id": user.id,
            "video": False,
        }

        pos = await db.add_to_queue(chat_id, new_track)
        from helpers.memory import mem_add_track
        mem_add_track(chat_id, new_track)

        await searching_msg.edit(
            f"Added similar song to queue at position <b>{pos}</b>\n"
            f"<b>{new_track['title']}</b> [{format_duration(new_track.get('duration', 0))}]"
        )
