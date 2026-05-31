from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.types import Message

import database as db
from core import stream as sm
from helpers.antiflood import is_flooded, remaining_cooldown
from helpers.downloader import fetch_track, format_duration
from helpers.pinmanager import pin_message
from helpers.thumbnails import generate_now_playing_card
from plugins.utils import maintenance_check, now_playing_keyboard

def register(app: Client) -> None:

    @app.on_message(filters.command(["play", "vplay", "song", "playforce"]) & filters.group)
    @maintenance_check
    async def play_cmd(client: Client, message: Message):
        user = message.from_user
        if not user:
            return
            
        chat_id = message.chat.id
        cmd = message.command[0].lower()
        is_video = "v" in cmd
        is_force = "force" in cmd

        # Anti-Spam Check
        if is_flooded(chat_id, user.id):
            secs = remaining_cooldown(chat_id, user.id)
            await message.reply(f"⚠️ **Sʟᴏᴡ ᴅᴏᴡɴ!** Pʟᴇᴀsᴇ ᴡᴀɪᴛ `{secs:.1f}s` ʙᴇғᴏʀᴇ ʀᴇǫᴜᴇsᴛɪɴɢ ᴀɢᴀɪɴ.")
            return

        query = " ".join(message.command[1:]).strip()
        if not query:
            if message.reply_to_message and message.reply_to_message.audio:
                # Audio file support can be added here if needed
                await message.reply("⚠️ Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ YᴏᴜTᴜʙᴇ Lɪɴᴋ ᴏʀ Sᴏɴɢ Nᴀᴍᴇ.")
                return
            await message.reply(f"✧ **Usaɢᴇ:** `/{cmd} [song name or URL]`")
            return

        # Save User & Chat Data
        await db.upsert_user(user.id, user.first_name)
        await db.upsert_chat(chat_id, message.chat.title or "Unknown Chat")

        if await db.is_banned_in_chat(chat_id, user.id):
            await message.reply("⛔️ **Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴘʟᴀʏɪɴɢ ᴍᴜsɪᴄ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ.**")
            return

        msg = await message.reply("`[ 🔍 ] Sᴇᴀʀᴄʜɪɴɢ...`")

        # Fetch Track Info
        info = await fetch_track(query)
        if not info:
            await msg.edit("❌ **Nᴏ ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ ᴏɴ YᴏᴜTᴜʙᴇ.**")
            return

        track = {
            "title": info["title"],
            "url": info["url"],
            "webpage_url": info.get("webpage_url", ""),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail", ""),
            "uploader": info.get("uploader", "Unknown"),
            "video_id": info.get("video_id", ""),
            "requester": user.first_name,
            "requester_id": user.id,
            "video": is_video,
        }

        active = sm.get_active(chat_id)

        # Force Play Logic
        if is_force and active:
            from plugins.utils import is_dj_or_admin
            if not await is_dj_or_admin(client, chat_id, user.id):
                await msg.edit("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** Oɴʟʏ DJs/Aᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ Play-Force.")
                return
            await db.add_to_history(chat_id, active.track)
            
            # Insert at top of queue
            from database import get_db
            await get_db().queue.update_one(
                {"chat_id": chat_id},
                {"$push": {"tracks": {"$each": [track], "$position": 0}}},
                upsert=True
            )
            from helpers.memory import mem_get_queue, mem_set_queue
            q = mem_get_queue(chat_id)
            q.insert(0, track)
            mem_set_queue(chat_id, q)
            
            await sm.play(chat_id, track, video=is_video)
            pos = 1
        else:
            # Normal Play / Add to Queue
            pos = await db.add_to_queue(chat_id, track)
            from helpers.memory import mem_add_track
            mem_add_track(chat_id, track)

        # Play if nothing is playing
        if not sm.get_active(chat_id) or (is_force and active):
            try:
                await sm.play(chat_id, track, video=is_video)
            except Exception as e:
                await msg.edit(f"❌ **Fᴀɪʟᴇᴅ ᴛᴏ ᴊᴏɪɴ Vᴏɪᴄᴇ Cʜᴀᴛ:** `{str(e)}`")
                return

            await msg.delete()
            me = await client.get_me()

            # Generate Premium Thumbnail
            buf = await generate_now_playing_card(
                title=track["title"],
                uploader=track.get("uploader", "Unknown"),
                thumbnail_url=track.get("thumbnail", ""),
                requester=track.get("requester", "Unknown"),
                elapsed=0,
                duration=track.get("duration", 0),
                bot_name=me.first_name
            )
            
            kb = now_playing_keyboard(chat_id)
            caption = (
                f"⏤͟͟͞͞★ **{me.first_name.upper()} Sᴛʀᴇᴀᴍɪɴɢ**\n\n"
                f"✧ **Sᴏɴɢ :** [{track['title'][:40]}]({track.get('webpage_url', '')})\n"
                f"✧ **Tɪᴍᴇ :** `{format_duration(track.get('duration', 0))}`\n"
                f"✧ **Rᴇǫᴜᴇsᴛ :** {track['requester']}"
            )
            
            np_msg = await client.send_photo(
                chat_id,
                photo=buf,
                caption=caption,
                reply_markup=kb,
            )
            await pin_message(client, chat_id, np_msg.id)
            
            stream = sm.get_active(chat_id)
            if stream:
                stream.message_id = np_msg.id

            # Start Idle Timer
            async def _on_idle(cid: int):
                active_stream = sm.get_active(cid)
                if not active_stream:
                    return
                await sm.stop(cid, client)
                try:
                    await client.send_message(cid, "🛑 **Qᴜᴇᴜᴇ ᴇɴᴅᴇᴅ.** Bᴏᴛ ʜᴀs ʟᴇғᴛ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ.")
                except Exception:
                    pass

            sm.start_idle_timer(chat_id, _on_idle)

        else:
            # Added to Queue Message
            await msg.edit(
                f"✅ **Aᴅᴅᴇᴅ ᴛᴏ Qᴜᴇᴜᴇ ᴀᴛ #{pos}**\n\n"
                f"✧ **Sᴏɴɢ :** {track['title'][:40]}\n"
                f"✧ **Tɪᴍᴇ :** `{format_duration(track.get('duration', 0))}`"
            )
