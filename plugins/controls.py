from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

import database as db
from core import stream as sm
from helpers.downloader import format_duration
from helpers.memory import is_muted
from helpers.pinmanager import pin_message
from helpers.thumbnails import generate_now_playing_card
from plugins.utils import (
    format_track,
    is_dj_or_admin,
    loop_keyboard,
    maintenance_check,
    now_playing_keyboard,
    queue_keyboard,
    seek_keyboard,
)

_PER_PAGE = 10

def register(app: Client) -> None:

    @app.on_message(filters.command("pause") & filters.group)
    @maintenance_check
    async def pause_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
            return
        ok = await sm.pause(message.chat.id)
        await message.reply("❙❙ **Sᴛʀᴇᴀᴍ Pᴀᴜsᴇᴅ**" if ok else "⚠️ Nᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ ᴏʀ ᴀʟʀᴇᴀᴅʏ ᴘᴀᴜsᴇᴅ.")

    @app.on_message(filters.command("resume") & filters.group)
    @maintenance_check
    async def resume_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
            return
        ok = await sm.resume(message.chat.id)
        await message.reply("▷ **Sᴛʀᴇᴀᴍ Rᴇsᴜᴍᴇᴅ**" if ok else "⚠️ Sᴛʀᴇᴀᴍ ɪs ɴᴏᴛ ᴘᴀᴜsᴇᴅ.")

    @app.on_message(filters.command("mute") & filters.group)
    @maintenance_check
    async def mute_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("🔇 Nᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ.")
            return
        if is_muted(message.chat.id):
            await message.reply("⚠️ Aʟʀᴇᴀᴅʏ ᴍᴜᴛᴇᴅ. ᴜsᴇ /unmute")
            return
        ok = await sm.mute(message.chat.id)
        await message.reply("🔇 **Bᴏᴛ Mᴜᴛᴇᴅ ɪɴ VC**" if ok else "❌ Cᴏᴜʟᴅ ɴᴏᴛ ᴍᴜᴛᴇ.")

    @app.on_message(filters.command("unmute") & filters.group)
    @maintenance_check
    async def unmute_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("🔇 Nᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ.")
            return
        if not is_muted(message.chat.id):
            await message.reply("⚠️ Nᴏᴛ ᴍᴜᴛᴇᴅ. ᴜsᴇ /mute")
            return
        ok = await sm.unmute(message.chat.id)
        await message.reply("🔊 **Bᴏᴛ Uɴᴍᴜᴛᴇᴅ ɪɴ VC**" if ok else "❌ Cᴏᴜʟᴅ ɴᴏᴛ ᴜɴᴍᴜᴛᴇ.")

    @app.on_message(filters.command("skip") & filters.group)
    @maintenance_check
    async def skip_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
            return
        chat_id = message.chat.id
        active = sm.get_active(chat_id)
        if not active:
            await message.reply("🔇 Nᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ.")
            return
            
        await db.add_to_history(chat_id, active.track)
        next_track = await sm.skip_to_next(chat_id, client)
        
        if next_track:
            me = await client.get_me()
            buf = await generate_now_playing_card(
                title=next_track["title"],
                uploader=next_track.get("uploader", "Unknown"),
                thumbnail_url=next_track.get("thumbnail", ""),
                requester=next_track.get("requester", "Unknown"),
                elapsed=0,
                duration=next_track.get("duration", 0),
                bot_name=me.first_name
            )
            kb = now_playing_keyboard(chat_id)
            np_msg = await client.send_photo(
                chat_id,
                photo=buf,
                caption=f"⏤͟͟͞͞★ **Sᴋɪᴘᴘᴇᴅ ᴛᴏ Nᴇxᴛ**\n\n✧ **Nᴏᴡ Pʟᴀʏɪɴɢ :** {next_track['title'][:40]}",
                reply_markup=kb,
            )
            await pin_message(client, chat_id, np_msg.id)
            stream = sm.get_active(chat_id)
            if stream:
                stream.message_id = np_msg.id
        else:
            await sm.stop(chat_id, client)
            await message.reply("🛑 **Qᴜᴇᴜᴇ Eɴᴅᴇᴅ.** Lᴇғᴛ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ.")

    @app.on_message(filters.command("stop") & filters.group)
    @maintenance_check
    async def stop_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("🔇 Nᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ.")
            return
        await sm.stop(message.chat.id, client)
        await message.reply("🛑 **Sᴛʀᴇᴀᴍ Sᴛᴏᴘᴘᴇᴅ & Qᴜᴇᴜᴇ Cʟᴇᴀʀᴇᴅ.**")

    @app.on_message(filters.command("shuffle") & filters.group)
    @maintenance_check
    async def shuffle_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
            return
        chat_id = message.chat.id
        await db.shuffle_queue(chat_id)
        from helpers.memory import mem_shuffle
        mem_shuffle(chat_id)
        await message.reply("🔀 **Qᴜᴇᴜᴇ Sʜᴜғғʟᴇᴅ.**")

    @app.on_message(filters.command("loop") & filters.group)
    @maintenance_check
    async def loop_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
            return
        current = await db.get_setting(message.chat.id, "loop_mode")
        await message.reply(
            f"✧ **Cᴜʀʀᴇɴᴛ Lᴏᴏᴘ :** `{current.capitalize()}`\nCʜᴏᴏsᴇ ɴᴇᴡ ᴍᴏᴅᴇ:",
            reply_markup=loop_keyboard(message.chat.id),
        )

    @app.on_message(filters.command("seek") & filters.group)
    @maintenance_check
    async def seek_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
            return
        active = sm.get_active(message.chat.id)
        if not active:
            await message.reply("🔇 Nᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ.")
            return

        args = message.command[1:]
        if not args:
            await message.reply("✧ Cʜᴏᴏsᴇ sᴇᴇᴋ ᴀᴄᴛɪᴏɴ:", reply_markup=seek_keyboard(message.chat.id))
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
        await message.reply(f"⏩ **Sᴇᴇᴋᴇᴅ ᴛᴏ :** `{format_duration(seconds)}`" if ok else "❌ Cᴏᴜʟᴅ ɴᴏᴛ sᴇᴇᴋ.")

    @app.on_message(filters.command("clearqueue") & filters.group)
    @maintenance_check
    async def clearqueue_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
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
        await message.reply("🗑 **Qᴜᴇᴜᴇ Cʟᴇᴀʀᴇᴅ** (Cᴜʀʀᴇɴᴛ ᴛʀᴀᴄᴋ ᴘʀᴇsᴇʀᴠᴇᴅ).")

    @app.on_message(filters.command("fix") & filters.group)
    @maintenance_check
    async def fix_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
            return
        chat_id = message.chat.id
        active = sm.get_active(chat_id)
        if not active:
            await message.reply("🔇 Nᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ.")
            return
        
        msg = await message.reply("`[ 🔄 ] Fɪxɪɴɢ Sᴛʀᴇᴀᴍ Cᴏɴɴᴇᴄᴛɪᴏɴ...`")
        track = active.track
        elapsed = active.elapsed
        try:
            await sm.stop(chat_id, client)
        except Exception:
            pass
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
            await msg.edit(f"✅ **Rᴇᴄᴏɴɴᴇᴄᴛᴇᴅ & Rᴇsᴜᴍᴇᴅ ᴀᴛ :** `{format_duration(elapsed)}`")
        except Exception as e:
            await msg.edit(f"❌ **Fᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴄᴏɴɴᴇᴄᴛ:** `{e}`")

    # ─── Callback Query Handlers ──────────────────────────────────────────────

    @app.on_callback_query(filters.regex(r"^np_"))
    async def np_cb(client: Client, cb: CallbackQuery):
        parts = cb.data.split("_")
        action = parts[1]
        chat_id = int(parts[2])

        if not await is_dj_or_admin(client, chat_id, cb.from_user.id):
            await cb.answer("⚠️ Admins & DJs Only!", show_alert=True)
            return

        if action == "pause":
            ok = await sm.pause(chat_id)
            await cb.answer("❙❙ Paused" if ok else "Already paused.")
            if ok:
                try:
                    await cb.message.edit_reply_markup(reply_markup=now_playing_keyboard(chat_id, paused=True))
                except Exception:
                    pass

        elif action == "resume":
            ok = await sm.resume(chat_id)
            await cb.answer("▷ Resumed" if ok else "Not paused.")
            if ok:
                try:
                    await cb.message.edit_reply_markup(reply_markup=now_playing_keyboard(chat_id, paused=False))
                except Exception:
                    pass

        elif action == "skip":
            active = sm.get_active(chat_id)
            if not active:
                await cb.answer("Nothing playing.")
                return
            await cb.answer("⏭ Skipping...")
            await db.add_to_history(chat_id, active.track)
            next_track = await sm.skip_to_next(chat_id, client)
            if not next_track:
                await cb.message.reply("🛑 **Qᴜᴇᴜᴇ Eɴᴅᴇᴅ.**")

        elif action == "stop":
            await sm.stop(chat_id, client)
            await cb.answer("🛑 Stopped.")
            try:
                await cb.message.delete()
            except Exception:
                pass

        elif action == "queue":
            queue = await db.get_queue(chat_id)
            if not queue:
                await cb.answer("Queue is empty.", show_alert=True)
                return
            
            page = 1
            total_pages = max(1, (len(queue) + _PER_PAGE - 1) // _PER_PAGE)
            start = 0
            
            current_tracks = queue[start:start + _PER_PAGE]
            track_indices = [i + 1 for i in range(start, start + len(current_tracks))]
            lines = [format_track(t, i) for t, i in zip(current_tracks, track_indices)]
            
            text = f"⏤͟͟͞͞★ **Cᴜʀʀᴇɴᴛ Qᴜᴇᴜᴇ — {len(queue)} Tʀᴀᴄᴋ(s)**\n\n" + "\n\n".join(lines)
            await cb.message.reply(text, reply_markup=queue_keyboard(chat_id, page, total_pages, track_indices))
            await cb.answer()

    @app.on_callback_query(filters.regex(r"^loop_"))
    async def loop_cb(client: Client, cb: CallbackQuery):
        parts = cb.data.split("_")
        mode = parts[1]
        chat_id = int(parts[2])

        if not await is_dj_or_admin(client, chat_id, cb.from_user.id):
            await cb.answer("⚠️ Admins & DJs Only!", show_alert=True)
            return

        await db.set_setting(chat_id, "loop_mode", mode)
        await cb.answer(f"🔁 Loop set to: {mode.capitalize()}")
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
            await cb.answer("⚠️ Admins & DJs Only!", show_alert=True)
            return

        active = sm.get_active(chat_id)
        if not active:
            await cb.answer("Nothing playing.")
            return

        new_pos = max(0, active.elapsed - 10) if direction == "back" else active.elapsed + 10
        await sm.seek(chat_id, new_pos)
        await cb.answer(f"⏩ Seeked to {format_duration(new_pos)}")


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
                    
