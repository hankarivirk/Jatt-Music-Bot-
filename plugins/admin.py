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
            await message.reply("Reply to a user to grant them DJ role.")
            return
        target = message.reply_to_message.from_user
        if target.is_bot:
            await message.reply("Cannot grant DJ role to a bot.")
            return
        await db.add_dj(message.chat.id, target.id)
        await message.reply(
            f"<b>{target.first_name}</b> has been granted DJ role in this group."
        )

    @app.on_message(filters.command("unauth") & filters.group)
    @maintenance_check
    @group_admin_only
    async def unauth_cmd(client: Client, message: Message):
        if not message.reply_to_message:
            await message.reply("Reply to a user to remove their DJ role.")
            return
        target = message.reply_to_message.from_user
        await db.remove_dj(message.chat.id, target.id)
        await message.reply(
            f"<b>{target.first_name}</b>'s DJ role has been removed."
        )

    @app.on_message(filters.command("adminonly") & filters.group)
    @maintenance_check
    @group_admin_only
    async def adminonly_cmd(client: Client, message: Message):
        chat_id = message.chat.id
        current = await db.get_setting(chat_id, "admin_only")
        new_val = not current
        await db.set_setting(chat_id, "admin_only", new_val)
        state = "enabled" if new_val else "disabled"
        await message.reply(f"Admin-only mode <b>{state}</b>.")

    @app.on_message(filters.command("setlog") & filters.group)
    @maintenance_check
    @group_admin_only
    async def setlog_cmd(client: Client, message: Message):
        args = message.command[1:]
        if not args:
            await message.reply("Usage: /setlog <channel_id>")
            return
        try:
            channel_id = int(args[0])
        except ValueError:
            await message.reply("Invalid channel ID.")
            return
        await db.set_setting(message.chat.id, "log_channel", channel_id)
        await message.reply(f"Log channel set to <code>{channel_id}</code>.")

    @app.on_message(filters.command("setwelcome") & filters.group)
    @maintenance_check
    @group_admin_only
    async def setwelcome_cmd(client: Client, message: Message):
        text = " ".join(message.command[1:]).strip()
        if not text:
            await message.reply("Usage: /setwelcome <welcome text>\nUse {name} and {group} as placeholders.")
            return
        await db.set_setting(message.chat.id, "welcome", text)
        await message.reply(f"Welcome message set:\n\n{text}")

    @app.on_message(filters.command("setprefix") & filters.group)
    @maintenance_check
    @group_admin_only
    async def setprefix_cmd(client: Client, message: Message):
        args = message.command[1:]
        if not args:
            await message.reply("Usage: /setprefix <symbol>")
            return
        prefix = args[0].strip()
        if len(prefix) > 3:
            await message.reply("Prefix must be 1-3 characters.")
            return
        await db.set_setting(message.chat.id, "prefix", prefix)
        await message.reply(f"Command prefix set to <code>{prefix}</code>.")

    @app.on_message(filters.command("quality") & filters.group)
    @maintenance_check
    @group_admin_only
    async def quality_cmd(client: Client, message: Message):
        args = message.command[1:]
        if not args or args[0].lower() not in ("high", "medium", "low"):
            await message.reply("Usage: /quality <high/medium/low>")
            return
        quality = args[0].lower()
        await db.set_setting(message.chat.id, "quality", quality)
        await message.reply(f"Audio quality set to <b>{quality}</b>.")

    @app.on_message(filters.command("ban") & filters.group)
    @maintenance_check
    @group_admin_only
    async def ban_cmd(client: Client, message: Message):
        if not message.reply_to_message:
            await message.reply("Reply to a user to ban them.")
            return
        target = message.reply_to_message.from_user
        from plugins.utils import is_sudo
        if is_sudo(target.id):
            await message.reply("Cannot ban a sudo user.")
            return
        await db.ban_user_in_chat(message.chat.id, target.id)
        await message.reply(
            f"<b>{target.first_name}</b> has been banned from using the bot in this group."
        )

    @app.on_message(filters.command("unban") & filters.group)
    @maintenance_check
    @group_admin_only
    async def unban_cmd(client: Client, message: Message):
        if not message.reply_to_message:
            await message.reply("Reply to a user to unban them.")
            return
        target = message.reply_to_message.from_user
        await db.unban_user_in_chat(message.chat.id, target.id)
        await message.reply(
            f"<b>{target.first_name}</b> has been unbanned in this group."
        )

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
                await message.reply(text)
            except Exception:
                pass
