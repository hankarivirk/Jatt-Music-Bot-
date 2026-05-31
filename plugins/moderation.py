from __future__ import annotations

import asyncio

from pyrogram import Client, filters
from pyrogram.types import Message

import database as db
from plugins.utils import maintenance_check, owner_only

def register(app: Client) -> None:

    @app.on_message(filters.command("gban") & filters.private)
    @owner_only
    async def gban_cmd(client: Client, message: Message):
        args = message.command[1:]
        reason = " ".join(args[1:]) if len(args) > 1 else "No reason provided"

        target_id = None
        if args:
            try: target_id = int(args[0])
            except ValueError: pass
        if target_id is None and message.reply_to_message:
            target_id = message.reply_to_message.from_user.id

        if not target_id:
            await message.reply("✧ **Usaɢᴇ:** `/gban [user_id] [reason]`")
            return

        from plugins.utils import is_sudo
        if is_sudo(target_id):
            await message.reply("❌ Cᴀɴɴᴏᴛ ɢʙᴀɴ ᴀ Sᴜᴅᴏ ᴜsᴇʀ.")
            return

        await db.add_gban(target_id, reason)
        chats = await db.get_all_chats()
        kicked = 0
        for chat in chats:
            try:
                await client.ban_chat_member(chat["chat_id"], target_id)
                kicked += 1
                await asyncio.sleep(0.1)
            except Exception:
                pass

        await message.reply(
            f"⚠️ **Gʟᴏʙᴀʟ Bᴀɴ Exᴇᴄᴜᴛᴇᴅ**\n\n"
            f"✧ **Usᴇʀ:** `{target_id}`\n"
            f"✧ **Rᴇᴀsᴏɴ:** {reason}\n"
            f"✧ **Rᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ:** `{kicked}` ɢʀᴏᴜᴘs"
        )

    @app.on_message(filters.command("ungban") & filters.private)
    @owner_only
    async def ungban_cmd(client: Client, message: Message):
        args = message.command[1:]
        if not args:
            await message.reply("✧ **Usaɢᴇ:** `/ungban [user_id]`")
            return
        try:
            target_id = int(args[0])
        except ValueError:
            await message.reply("❌ Iɴᴠᴀʟɪᴅ Usᴇʀ ID.")
            return

        ok = await db.remove_gban(target_id)
        if not ok:
            await message.reply("⚠️ Usᴇʀ ɪs ɴᴏᴛ G-Bᴀɴɴᴇᴅ.")
            return

        chats = await db.get_all_chats()
        unbanned = 0
        for chat in chats:
            try:
                await client.unban_chat_member(chat["chat_id"], target_id)
                unbanned += 1
                await asyncio.sleep(0.1)
            except Exception:
                pass

        await message.reply(f"✅ **Gʟᴏʙᴀʟ Bᴀɴ Rᴇᴍᴏᴠᴇᴅ**\n✧ **Usᴇʀ:** `{target_id}`\n✧ **Uɴʙᴀɴɴᴇᴅ ɪɴ:** `{unbanned}` ɢʀᴏᴜᴘs")

    @app.on_message(filters.command("gmute") & filters.private)
    @owner_only
    async def gmute_cmd(client: Client, message: Message):
        args = message.command[1:]
        reason = " ".join(args[1:]) if len(args) > 1 else "No reason provided"

        target_id = None
        if args:
            try: target_id = int(args[0])
            except ValueError: pass
        if target_id is None and message.reply_to_message:
            target_id = message.reply_to_message.from_user.id

        if not target_id:
            await message.reply("✧ **Usaɢᴇ:** `/gmute [user_id] [reason]`")
            return

        from plugins.utils import is_sudo
        if is_sudo(target_id):
            await message.reply("❌ Cᴀɴɴᴏᴛ ɢᴍᴜᴛᴇ ᴀ Sᴜᴅᴏ ᴜsᴇʀ.")
            return

        await db.add_gmute(target_id, reason)
        await message.reply(
            f"🔇 **Gʟᴏʙᴀʟ Mᴜᴛᴇ Exᴇᴄᴜᴛᴇᴅ**\n\n"
            f"✧ **Usᴇʀ:** `{target_id}`\n"
            f"✧ **Rᴇᴀsᴏɴ:** {reason}\n"
            "*(Tʜᴇɪʀ ᴍᴇssᴀɢᴇs ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇᴅ ɪɴ ᴀʟʟ ɢʀᴏᴜᴘs)*"
        )

    @app.on_message(filters.command("ungmute") & filters.private)
    @owner_only
    async def ungmute_cmd(client: Client, message: Message):
        args = message.command[1:]
        if not args:
            await message.reply("✧ **Usaɢᴇ:** `/ungmute [user_id]`")
            return
        try:
            target_id = int(args[0])
        except ValueError:
            await message.reply("❌ Iɴᴠᴀʟɪᴅ Usᴇʀ ID.")
            return

        ok = await db.remove_gmute(target_id)
        await message.reply(f"✅ **Gʟᴏʙᴀʟ Mᴜᴛᴇ Rᴇᴍᴏᴠᴇᴅ** ғᴏʀ `{target_id}`" if ok else "⚠️ Usᴇʀ ɪs ɴᴏᴛ G-Mᴜᴛᴇᴅ.")

    @app.on_message(filters.command("gkick") & filters.private)
    @owner_only
    async def gkick_cmd(client: Client, message: Message):
        args = message.command[1:]
        if not args:
            await message.reply("✧ **Usaɢᴇ:** `/gkick [user_id]`")
            return
        try:
            target_id = int(args[0])
        except ValueError:
            await message.reply("❌ Iɴᴠᴀʟɪᴅ Usᴇʀ ID.")
            return

        from plugins.utils import is_sudo
        if is_sudo(target_id):
            await message.reply("❌ Cᴀɴɴᴏᴛ ɢᴋɪᴄᴋ ᴀ Sᴜᴅᴏ ᴜsᴇʀ.")
            return

        chats = await db.get_all_chats()
        kicked = 0
        for chat in chats:
            try:
                await client.ban_chat_member(chat["chat_id"], target_id)
                await asyncio.sleep(0.05)
                await client.unban_chat_member(chat["chat_id"], target_id)
                kicked += 1
                await asyncio.sleep(0.1)
            except Exception:
                pass

        await message.reply(f"👢 **Gʟᴏʙᴀʟ Kɪᴄᴋ Exᴇᴄᴜᴛᴇᴅ**\n✧ Usᴇʀ `{target_id}` ᴋɪᴄᴋᴇᴅ ғʀᴏᴍ `{kicked}` ɢʀᴏᴜᴘs.")

    @app.on_message(filters.command("gbanlist") & filters.private)
    @owner_only
    async def gbanlist_cmd(client: Client, message: Message):
        banned = await db.get_gban_list()
        if not banned:
            await message.reply("✅ **Nᴏ ɢʟᴏʙᴀʟʟʏ ʙᴀɴɴᴇᴅ ᴜsᴇʀs.**")
            return
        lines = [f"• `{u['user_id']}` — {u.get('reason', 'N/A')}" for u in banned]
        text = "⏤͟͟͞͞★ **Gʟᴏʙᴀʟʟʏ Bᴀɴɴᴇᴅ Usᴇʀs**\n\n" + "\n".join(lines)
        if len(text) > 4000: text = text[:4000] + "\n..."
        await message.reply(text)

    @app.on_message(filters.command("gmutelist") & filters.private)
    @owner_only
    async def gmutelist_cmd(client: Client, message: Message):
        muted = await db.get_gmute_list()
        if not muted:
            await message.reply("✅ **Nᴏ ɢʟᴏʙᴀʟʟʏ ᴍᴜᴛᴇᴅ ᴜsᴇʀs.**")
            return
        lines = [f"• `{u['user_id']}` — {u.get('reason', 'N/A')}" for u in muted]
        text = "⏤͟͟͞͞★ **Gʟᴏʙᴀʟʟʏ Mᴜᴛᴇᴅ Usᴇʀs**\n\n" + "\n".join(lines)
        if len(text) > 4000: text = text[:4000] + "\n..."
        await message.reply(text)

    @app.on_message(filters.group)
    async def auto_delete_gmuted(client: Client, message: Message):
        if not message.from_user:
            return
        user_id = message.from_user.id
        from plugins.utils import is_sudo
        if is_sudo(user_id):
            return
        if await db.is_gmuted(user_id):
            try:
                await message.delete()
            except Exception:
                pass
        
