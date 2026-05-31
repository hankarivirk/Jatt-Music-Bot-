from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

import database as db
from core import stream as sm
from helpers.downloader import format_duration
from helpers.memory import is_muted
from helpers.pinmanager import pin_message
from helpers.thumbnails import generate_now_playing_card
from plugins.utils import (
    is_dj_or_admin,
    loop_keyboard,
    maintenance_check,
    now_playing_keyboard,
    seek_keyboard,
)


def register(app: Client) -> None:

    @app.on_message(filters.command("pause") & filters.group)
    @maintenance_check
    async def pause_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can pause.")
            return
        ok = await sm.pause(message.chat.id)
        await message.reply("Paused." if ok else "Nothing is playing or already paused.")

    @app.on_message(filters.command("resume") & filters.group)
    @maintenance_check
    async def resume_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can resume.")
            return
        ok = await sm.resume(message.chat.id)
        await message.reply("Resumed." if ok else "Nothing is paused.")

    @app.on_message(filters.command("mute") & filters.group)
    @maintenance_check
    async def mute_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can mute.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("Nothing is playing.")
            return
        if is_muted(message.chat.id):
            await message.reply("Already muted. Use /unmute.")
            return
        ok = await sm.mute(message.chat.id)
        await message.reply("Muted." if ok else "Could not mute.")

    @app.on_message(filters.command("unmute") & filters.group)
    @maintenance_check
    async def unmute_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can unmute.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("Nothing is playing.")
            return
        if not is_muted(message.chat.id):
            await message.reply("Not muted. Use /mute to mute.")
            return
        ok = await sm.unmute(message.chat.id)
        await message.reply("Unmuted." if ok else "Could not unmute.")

    @app.on_message(filters.command("skip") & filters.group)
    @maintenance_check
    async def skip_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can skip.")
            return
        chat_id = message.chat.id
        active = sm.get_active(chat_id)
        if not active:
            await message.reply("Nothing is playing.")
            return
        await db.add_to_history(chat_id, active.track)
        next_track = await sm.skip_to_next(chat_id, client)
        if next_track:
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
                caption=f"<b>Now Playing</b>\n<b>{next_track['title']}</b>",
                reply_markup=kb,
            )
            await pin_message(client, chat_id, np_msg.id)
            stream = sm.get_active(chat_id)
            if stream:
                stream.message_id = np_msg.id
        else:
            await sm.stop(chat_id, client)
            await message.reply("Queue ended. Left voice chat.")

    @app.on_message(filters.command("stop") & filters.group)
    @maintenance_check
    async def stop_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can stop.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("Nothing is playing.")
            return
        await sm.stop(message.chat.id, client)
        await message.reply("Stopped and left the voice chat.")

    @app.on_message(filters.command("shuffle") & filters.group)
    @maintenance_check
    async def shuffle_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can shuffle.")
            return
        chat_id = message.chat.id
        await db.shuffle_queue(chat_id)
        from helpers.memory import mem_shuffle
        mem_shuffle(chat_id)
        await message.reply("Queue shuffled.")

    @app.on_message(filters.command("loop") & filters.group)
    @maintenance_check
    async def loop_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can set loop mode.")
            return
        current = await db.get_setting(message.chat.id, "loop_mode")
        await message.reply(
            f"Current loop mode: <b>{current}</b>. Choose new mode:",
            reply_markup=loop_keyboard(message.chat.id),
        )

    @app.on_message(filters.command("seek") & filters.group)
    @maintenance_check
    async def seek_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can seek.")
            return
        active = sm.get_active(message.chat.id)
        if not active:
            await message.reply("Nothing is playing.")
            return

        args = message.command[1:]
        if not args:
            await message.reply("Choose seek action:", reply_markup=seek_keyboard(message.chat.id))
            return

        time_str = args[0].strip()
        current = active.elapsed

        if time_str.startswith("+"):
            seconds = current + _parse_time(time_str[1:])
        elif time_str.startswith("-"):
            seconds = max(0, current - _parse_time(time_str[1:]))
        else:
            seconds = _parse_time(time_str)

        ok = await sm.seek(message.chat.id, seconds)
        await message.reply(f"Seeked to {format_duration(seconds)}." if ok else "Could not seek.")

    @app.on_message(filters.command("clearqueue") & filters.group)
    @maintenance_check
    async def clearqueue_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can clear the queue.")
            return
        chat_id = message.chat.id
        active = sm.get_active(chat_id)
        if active:
            current_track = active.track
            await db.clear_queue(chat_id)
            from helpers.memory import mem_clear, mem_add_track
            mem_clear(chat_id)
            await db.add_to_queue(chat_id, current_track)
            mem_add_track(chat_id, current_track)
        else:
            await db.clear_queue(chat_id)
            from helpers.memory import mem_clear
            mem_clear(chat_id)
        await message.reply("Queue cleared (current track preserved).")

    @app.on_message(filters.command("fix") & filters.group)
    @maintenance_check
    async def fix_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can use /fix.")
            return
        chat_id = message.chat.id
        active = sm.get_active(chat_id)
        if not active:
            await message.reply("Nothing is playing.")
            return
        track = active.track
        elapsed = active.elapsed
        try:
            await sm.stop(chat_id, client)
        except Exception:
            pass
        # Refresh URL before reconnecting
        if track.get("webpage_url"):
            try:
                from helpers.downloader import fetch_track
                fresh = await fetch_track(track["webpage_url"])
                if fresh and fresh.get("url"):
                    track["url"] = fresh["url"]
            except Exception:
                pass
        try:
            await sm.play(chat_id, track, seek=elapsed)
            await message.reply(f"Reconnected and resumed at {format_duration(elapsed)}.")
        except Exception as e:
            await message.reply(f"Failed to reconnect: {e}")

    # ─── Callback Query Handlers ──────────────────────────────────────────────

    @app.on_callback_query(filters.regex(r"^np_"))
    async def np_cb(client: Client, cb: CallbackQuery):
        parts = cb.data.split("_")
        action = parts[1]
        chat_id = int(parts[2])

        if not await is_dj_or_admin(client, chat_id, cb.from_user.id):
            await cb.answer("Only DJs and admins can use these controls.", show_alert=True)
            return

        if action == "pause":
            ok = await sm.pause(chat_id)
            await cb.answer("Paused." if ok else "Already paused.")
            if ok:
                try:
                    await cb.message.edit_reply_markup(
                        reply_markup=now_playing_keyboard(chat_id, paused=True)
                    )
                except Exception:
                    pass

        elif action == "resume":
            ok = await sm.resume(chat_id)
            await cb.answer("Resumed." if ok else "Not paused.")
            if ok:
                try:
                    await cb.message.edit_reply_markup(
                        reply_markup=now_playing_keyboard(chat_id, paused=False)
                    )
                except Exception:
                    pass

        elif action == "skip":
            active = sm.get_active(chat_id)
            if not active:
                await cb.answer("Nothing playing.")
                return
            await db.add_to_history(chat_id, active.track)
            next_track = await sm.skip_to_next(chat_id, client)
            await cb.answer("Skipped." if next_track else "Queue ended.")

        elif action == "stop":
            await sm.stop(chat_id, client)
            await cb.answer("Stopped.")
            try:
                await cb.message.delete()
            except Exception:
                pass

        elif action == "voldwn":
            active = sm.get_active(chat_id)
            if active:
                new_vol = max(0, active.volume - 10)
                await sm.set_volume(chat_id, new_vol)
                await cb.answer(f"Volume: {new_vol}%")
            else:
                await cb.answer("Nothing playing.")

        elif action == "volup":
            active = sm.get_active(chat_id)
            if active:
                new_vol = min(200, active.volume + 10)
                await sm.set_volume(chat_id, new_vol)
                await cb.answer(f"Volume: {new_vol}%")
            else:
                await cb.answer("Nothing playing.")

        elif action == "shuffle":
            await db.shuffle_queue(chat_id)
            from helpers.memory import mem_shuffle
            mem_shuffle(chat_id)
            await cb.answer("Queue shuffled.")

        elif action == "loop":
            current = await db.get_setting(chat_id, "loop_mode")
            await cb.message.reply(
                f"Loop mode: <b>{current}</b>. Choose:",
                reply_markup=loop_keyboard(chat_id),
            )
            await cb.answer()

        elif action == "queue":
            queue = await db.get_queue(chat_id)
            if not queue:
                await cb.answer("Queue is empty.", show_alert=True)
                return
            from plugins.utils import format_track, queue_keyboard
            page = 1
            per_page = 10
            total_pages = max(1, (len(queue) + per_page - 1) // per_page)
            start = (page - 1) * per_page
            lines = [format_track(t, i + start + 1) for i, t in enumerate(queue[start:start + per_page])]
            text = f"<b>Queue ({len(queue)} tracks)</b>\n\n" + "\n".join(lines)
            await cb.message.reply(text, reply_markup=queue_keyboard(chat_id, page, total_pages))
            await cb.answer()

        elif action == "replay":
            active = sm.get_active(chat_id)
            if not active:
                await cb.answer("Nothing playing.")
                return
            await sm.seek(chat_id, 0)
            await cb.answer("Replaying from start.")

    @app.on_callback_query(filters.regex(r"^loop_"))
    async def loop_cb(client: Client, cb: CallbackQuery):
        parts = cb.data.split("_")
        mode = parts[1]
        chat_id = int(parts[2])

        if not await is_dj_or_admin(client, chat_id, cb.from_user.id):
            await cb.answer("Only DJs and admins can change loop mode.", show_alert=True)
            return

        await db.set_setting(chat_id, "loop_mode", mode)
        await cb.answer(f"Loop: {mode}")
        try:
            await cb.message.delete()
        except Exception:
            pass

    @app.on_callback_query(filters.regex(r"^seek_"))
    async def seek_cb(client: Client, cb: CallbackQuery):
        parts = cb.data.split("_")
        direction = parts[1]
        chat_id = int(parts[2])

        if not await is_dj_or_admin(client, chat_id, cb.from_user.id):
            await cb.answer("Only DJs and admins can seek.", show_alert=True)
            return

        active = sm.get_active(chat_id)
        if not active:
            await cb.answer("Nothing playing.")
            return

        new_pos = max(0, active.elapsed - 10) if direction == "back" else active.elapsed + 10
        await sm.seek(chat_id, new_pos)
        await cb.answer(f"Seeked to {format_duration(new_pos)}")


def _parse_time(time_str: str) -> int:
    time_str = time_str.strip().rstrip("s")
    if ":" in time_str:
        parts = time_str.split(":")
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return int(parts[0]) * 60 + int(parts[1])
    try:
        return int(time_str)
    except ValueError:
        return 0
