from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.types import Message

import database as db
from plugins.utils import is_dj_or_admin, maintenance_check

def register(app: Client) -> None:

    @app.on_message(filters.command("247") & filters.group)
    @maintenance_check
    async def vc247_cmd(client: Client, message: Message):
        chat_id = message.chat.id
        if not await is_dj_or_admin(client, chat_id, message.from_user.id):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
            return
        current = await db.get_setting(chat_id, "vc247")
        new_val = not current
        await db.set_setting(chat_id, "vc247", new_val)
        if new_val:
            await message.reply(
                "⏤͟͟͞͞★ **24/7 Mᴏᴅᴇ :** `Eɴᴀʙʟᴇᴅ`\n"
                "✧ Bᴏᴛ ᴡɪʟʟ sᴛᴀʏ ɪɴ VC ᴇᴠᴇɴ ᴡʜᴇɴ ɪᴅʟᴇ."
            )
        else:
            await message.reply(
                "⏤͟͟͞͞★ **24/7 Mᴏᴅᴇ :** `Dɪsᴀʙʟᴇᴅ`\n"
                "✧ Bᴏᴛ ᴡɪʟʟ ʟᴇᴀᴠᴇ ᴀғᴛᴇʀ ɪɴᴀᴄᴛɪᴠɪᴛʏ."
            )
            
