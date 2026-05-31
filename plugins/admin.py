from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.types import Message

import database as db
from plugins.utils import group_admin_only, maintenance_check

def register(app: Client) -> None:

    @app.on_message(filters.command("auth") & filters.group)
    @maintenance_check
    @group_admin_only
    async def auth_cmd(client: Client, message: Message):
        if not message.reply_to_message:
            await message.reply("⚠️ Rᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ɢʀᴀɴᴛ ᴛʜᴇᴍ DJ ʀᴏʟᴇ.")
            return
        target = message.reply_to_message.from_user
        if target.is_bot:
            await message.reply("❌ Cᴀɴɴᴏᴛ ɢʀᴀɴᴛ DJ ʀᴏʟᴇ ᴛᴏ ᴀ ʙᴏᴛ.")
            return
        await db.add_dj(message.chat.id, target.id)
        await message.reply(f"⏤͟͟͞͞★ **Aᴜᴛʜᴏʀɪᴢᴀᴛɪᴏɴ**\n✧ 👤 **{target.first_name}** ɪs ɴᴏᴡ ᴀ **DJ** ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ.")

    @app.on_message(filters.command("unauth") & filters.group)
    @maintenance_check
    @group_admin_only
    async def unauth_cmd(client: Client, message: Message):
        if not message.reply_to_message:
            await message.reply("⚠️ Rᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴛʜᴇɪʀ DJ ʀᴏʟᴇ.")
            return
        target = message.reply_to_message.from_user
        await db.remove_dj(message.chat.id, target.id)
        await message.reply(f"⏤͟͟͞͞★ **Aᴜᴛʜᴏʀɪᴢᴀᴛɪᴏɴ**\n✧ 👤 **{target.first_name}**'s DJ ʀᴏʟᴇ ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ.")

    @app.on_message(filters.command("adminonly") & filters.group)
    @maintenance_check
    @group_admin_only
    async def adminonly_cmd(client: Client, message: Message):
        chat_id = message.chat.id
        current = await db.get_setting(chat_id, "admin_only")
        new_val = not current
        await db.set_setting(chat_id, "admin_only", new_val)
        state = "Eɴᴀʙʟᴇᴅ" if new_val else "Dɪsᴀʙʟᴇᴅ"
        await message.reply(f"⏤͟͟͞͞★ **Sᴇᴛᴛɪɴɢs**\n✧ **Aᴅᴍɪɴ-Oɴʟʏ Mᴏᴅᴇ :** `{state}`")

    @app.on_message(filters.command("setlog") & filters.group)
    @maintenance_check
    @group_admin_only
    async def setlog_cmd(client: Client, message: Message):
        args = message.command[1:]
        if not args:
            await message.reply("✧ **Usaɢᴇ:** `/setlog [channel_id]`")
            return
        try:
            channel_id = int(args[0])
        except ValueError:
            await message.reply("❌ Iɴᴠᴀʟɪᴅ Cʜᴀɴɴᴇʟ ID.")
            return
        await db.set_setting(message.chat.id, "log_channel", channel_id)
        await message.reply(f"⏤͟͟͞͞★ **Sᴇᴛᴛɪɴɢs**\n✧ **Lᴏɢ Cʜᴀɴɴᴇʟ Sᴇᴛ Tᴏ :** `{channel_id}`")

    @app.on_message(filters.command("setwelcome") & filters.group)
    @maintenance_check
    @group_admin_only
    async def setwelcome_cmd(client: Client, message: Message):
        text = " ".join(message.command[1:]).strip()
        if not text:
            await message.reply("✧ **Usaɢᴇ:** `/setwelcome [welcome text]`\nUse `{name}` and `{group}` as placeholders.")
            return
        await db.set_setting(message.chat.id, "welcome", text)
        await message.reply(f"⏤͟͟͞͞★ **Wᴇʟᴄᴏᴍᴇ Mᴇssᴀɢᴇ Sᴇᴛ:**\n\n{text}")

    @app.on_message(filters.command("setprefix") & filters.group)
    @maintenance_check
    @group_admin_only
    async def setprefix_cmd(client: Client, message: Message):
        args = message.command[1:]
        if not args:
            await message.reply("✧ **Usaɢᴇ:** `/setprefix [symbol]`")
            return
        prefix = args[0].strip()
        if len(prefix) > 3:
            await message.reply("❌ Prefix must be 1-3 characters long.")
            return
        await db.set_setting(message.chat.id, "prefix", prefix)
        await message.reply(f"⏤͟͟͞͞★ **Sᴇᴛᴛɪɴɢs**\n✧ **Cᴏᴍᴍᴀɴᴅ Pʀᴇғɪx Sᴇᴛ Tᴏ :** `{prefix}`")

    @app.on_message(filters.command("quality") & filters.group)
    @maintenance_check
    @group_admin_only
    async def quality_cmd(client: Client, message: Message):
        args = message.command[1:]
        if not args or args[0].lower() not in ("high", "medium", "low"):
            await message.reply("✧ **Usaɢᴇ:** `/quality [high/medium/low]`")
            return
        quality = args[0].lower()
        await db.set_setting(message.chat.id, "quality", quality)
        await message.reply(f"⏤͟͟͞͞★ **Sᴇᴛᴛɪɴɢs**\n✧ **Aᴜᴅɪᴏ Qᴜᴀʟɪᴛʏ :** `{quality.capitalize()}`")

    @app.on_message(filters.command("ban") & filters.group)
    @maintenance_check
    @group_admin_only
    async def ban_cmd(client: Client, message: Message):
        if not message.reply_to_message:
            await message.reply("⚠️ Rᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ʙᴀɴ ᴛʜᴇᴍ ғʀᴏᴍ ᴛʜᴇ ʙᴏᴛ.")
            return
        target = message.reply_to_message.from_user
        from plugins.utils import is_sudo
        if is_sudo(target.id):
            await message.reply("❌ Cᴀɴɴᴏᴛ ʙᴀɴ ᴀ Sᴜᴅᴏ Usᴇʀ.")
            return
        await db.ban_user_in_chat(message.chat.id, target.id)
        await message.reply(f"⛔️ 👤 **{target.first_name}** ʜᴀs ʙᴇᴇɴ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜᴇ ʙᴏᴛ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ.")

    @app.on_message(filters.command("unban") & filters.group)
    @maintenance_check
    @group_admin_only
    async def unban_cmd(client: Client, message: Message):
        if not message.reply_to_message:
            await message.reply("⚠️ Rᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ᴜɴʙᴀɴ ᴛʜᴇᴍ.")
            return
        target = message.reply_to_message.from_user
        await db.unban_user_in_chat(message.chat.id, target.id)
        await message.reply(f"✅ 👤 **{target.first_name}** ᴄᴀɴ ɴᴏᴡ ᴜsᴇ ᴛʜᴇ ʙᴏᴛ ᴀɢᴀɪɴ.")

    @app.on_message(filters.new_chat_members & filters.group)
    async def welcome_handler(client: Client, message: Message):
        chat_id = message.chat.id
        welcome_text = await db.get_setting(chat_id, "welcome")
        if not welcome_text:
            return
        for member in message.new_chat_members:
            if member.is_bot:
                continue
            text = welcome_text.replace("{name}", member.first_name)
            text = text.replace("{group}", message.chat.title or "this group")
            try:
                await message.reply(f"⏤͟͟͞͞★ {text}")
            except Exception:
                pass
                
