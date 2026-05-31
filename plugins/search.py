from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import database as db
from core import stream as sm
from helpers.antiflood import is_flooded, remaining_cooldown
from helpers.downloader import fetch_track, format_duration, search_tracks
from helpers.pinmanager import pin_message
from helpers.thumbnails import generate_now_playing_card
from plugins.utils import maintenance_check, now_playing_keyboard

_search_cache: dict[str, list[dict]] = {}

def register(app: Client) -> None:

    @app.on_message(filters.command("search") & filters.group)
    @maintenance_check
    async def search_cmd(client: Client, message: Message):
        user = message.from_user
        chat_id = message.chat.id

        if is_flooded(chat_id, user.id):
            secs = remaining_cooldown(chat_id, user.id)
            await message.reply(f"⚠️ **Cooldown:** Pʟᴇᴀsᴇ ᴡᴀɪᴛ `{secs:.1f}s`.")
            return

        query = " ".join(message.command[1:]).strip()
        if not query:
            await message.reply("✧ **Usaɢᴇ:** `/search [song name]`")
            return

        await db.upsert_user(user.id, user.first_name)

        msg = await message.reply(f"`[ 🔍 ] Sᴇᴀʀᴄʜɪɴɢ ʏᴏᴜᴛᴜʙᴇ ғᴏʀ:` **{query}**")
        results = await search_tracks(query, limit=5)

        if not results:
            await msg.edit("❌ **Nᴏ ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ.** Tʀʏ ᴀ ᴅɪғғᴇʀᴇɴᴛ ɴᴀᴍᴇ.")
            return

        cache_key = f"{chat_id}:{user.id}"
        _search_cache[cache_key] = results

        buttons = []
        for i, r in enumerate(results):
            dur = format_duration(r.get("duration", 0))
            label = f"{i + 1}. {r['title'][:35]} [{dur}]"
            buttons.append([
                InlineKeyboardButton(label, callback_data=f"search_pick_{cache_key}_{i}")
            ])
        buttons.append([InlineKeyboardButton("🗑 Cᴀɴᴄᴇʟ", callback_data=f"search_cancel_{cache_key}")])

        await msg.edit(
            f"⏤͟͟͞͞★ **Sᴇᴀʀᴄʜ ʀᴇsᴜʟᴛs ғᴏʀ :** `{query}`\n\n✧ Cʜᴏᴏsᴇ ᴀ ᴛʀᴀᴄᴋ ʙᴇʟᴏᴡ:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    @app.on_callback_query(filters.regex(r"^search_(pick|cancel)_"))
    async def search_cb(client: Client, cb: CallbackQuery):
        parts = cb.data.split("_", 3)
        action = parts[1]
        cache_key_parts = parts[2:]

        if action == "cancel":
            cache_key = "_".join(cache_key_parts)
            _search_cache.pop(cache_key, None)
            await cb.message.delete()
            await cb.answer("Search Cancelled.")
            return

        try:
            idx = int(parts[-1])
            raw_key = "_".join(parts[2:-1])
        except (ValueError, IndexError):
            await cb.answer("Invalid selection.", show_alert=True)
            return

        results = _search_cache.get(raw_key)
        if not results or idx >= len(results):
            await cb.answer("Search expired! Please search again.", show_alert=True)
            try:
                await cb.message.delete()
            except Exception:
                pass
            return

        selected = results[idx]
        user = cb.from_user
        chat_id = cb.message.chat.id

        await cb.answer(f"Loading: {selected['title'][:30]}...")
        await cb.message.edit(f"`[ ✦ ] ʟᴏᴀᴅɪɴɢ ᴛʀᴀᴄᴋ:` **{selected['title']}**")

        info = await fetch_track(selected["webpage_url"])
        if not info:
            await cb.message.edit("❌ **Cᴏᴜʟᴅ ɴᴏᴛ ʟᴏᴀᴅ ᴛʜɪs ᴛʀᴀᴄᴋ.**")
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
            "video": False,
        }

        queue = await db.get_queue(chat_id)
        for t in queue:
            if t.get("video_id") and t.get("video_id") == track.get("video_id"):
                await cb.message.edit("⚠️ **Tʜɪs sᴏɴɢ ɪs ᴀʟʀᴇᴀᴅʏ ɪɴ ǫᴜᴇᴜᴇ.**")
                return

        pos = await db.add_to_queue(chat_id, track)
        _search_cache.pop(raw_key, None)

        if not sm.get_active(chat_id):
            await sm.play(chat_id, track, video=False)
            await cb.message.delete()
            
            me = await client.get_me()
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
            np_msg = await client.send_photo(
                chat_id,
                photo=buf,
                caption=f"⏤͟͟͞͞★ **{me.first_name.upper()} Sᴛʀᴇᴀᴍɪɴɢ**\n\n✧ **Sᴏɴɢ :** [{track['title'][:40]}]({track.get('webpage_url', '')})\n✧ **Rᴇǫᴜᴇsᴛ :** {track['requester']}",
                reply_markup=kb,
            )
            await pin_message(client, chat_id, np_msg.id)

            async def _on_idle(cid: int):
                active = sm.get_active(cid)
                if not active: return
                await sm.stop(cid, client)
                try:
                    await client.send_message(cid, "🛑 **Lᴇғᴛ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴅᴜᴇ ᴛᴏ ɪɴᴀᴄᴛɪᴠɪᴛʏ.**")
                except Exception:
                    pass

            sm.start_idle_timer(chat_id, _on_idle)
        else:
            await cb.message.edit(
                f"✅ **Qᴜᴇᴜᴇᴅ ᴀᴛ Pᴏsɪᴛɪᴏɴ #{pos}**\n\n"
                f"✧ **Sᴏɴɢ :** {track['title'][:40]}\n"
                f"✧ **Tɪᴍᴇ :** `{format_duration(track.get('duration', 0))}`"
    )
                    
