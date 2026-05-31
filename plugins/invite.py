from __future__ import annotations

import asyncio

from pyrogram import Client, filters
from pyrogram.types import Message

from plugins.utils import is_dj_or_admin, maintenance_check

def register(app: Client) -> None:

    @app.on_message(filters.command("invite") & filters.group)
    @maintenance_check
    async def invite_cmd(client: Client, message: Message):
        chat_id = message.chat.id
        user = message.from_user

        if not await is_dj_or_admin(client, chat_id, user.id):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
            return

        msg = await message.reply("`[ 🔄 ] Iɴᴠɪᴛɪɴɢ ɢʀᴏᴜᴘ ᴍᴇᴍʙᴇʀs ᴛᴏ Vᴏɪᴄᴇ Cʜᴀᴛ...`")

        try:
            members = client.get_chat_members(chat_id)
            invited = 0
            failed = 0
            async for member in members:
                if member.user.is_bot or member.user.id == (await client.get_me()).id:
                    continue
                try:
                    await client.invite_group_call_participants(
                        chat_id, [await client.resolve_peer(member.user.id)]
                    )
                    invited += 1
                    await asyncio.sleep(0.3)
                except Exception:
                    failed += 1

            await msg.edit(
                f"⏤͟͟͞͞★ **Iɴᴠɪᴛᴀᴛɪᴏɴs Sᴇɴᴛ**\n\n"
                f"✧ **Sᴜᴄᴄᴇss:** `{invited}` ᴍᴇᴍʙᴇʀs\n"
                f"✧ **Fᴀɪʟᴇᴅ:** `{failed}` ᴍᴇᴍʙᴇʀs"
            )
        except Exception as e:
            await msg.edit(f"❌ **Eʀʀᴏʀ ɪɴᴠɪᴛɪɴɢ ᴍᴇᴍʙᴇʀs:** `{e}`")
            
