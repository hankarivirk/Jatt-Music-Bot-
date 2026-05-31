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
            try:
                target_id = int(args[0])
            except ValueError:
                pass
        if target_id is None and message.reply_to_message:
            target_id = message.reply_to_message.from_user.id

        if not target_id:
            await message.reply("Usage: /gban <user_id> [reason]")
            return

        from plugins.utils import is_sudo
        if is_sudo(target_id):
            await message.reply("Cannot gban a sudo user.")
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
            f"User <code>{target_id}</code> has been globally banned.\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Banned from:</b> {kicked} groups"
        )

    @app.on_message(filters.command("ungban") & filters.private)
    @owner_only
    async def ungban_cmd(client: Client, message: Message):
        args = message.command[1:]
        if not args:
            await message.reply("Usage: /ungban <user_id>")
            return
        try:
            target_id = int(args[0])
        except ValueError:
            await message.reply("Invalid user ID.")
            return

        ok = await db.remove_gban(target_id)
        if not ok:
            await message.reply("This user is not globally banned.")
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

        await message.reply(
            f"User <code>{target_id}</code> has been globally unbanned.\n"
            f"<b>Removed from:</b> {unbanned} groups"
        )

    @app.on_message(filters.command("gmute") & filters.private)
    @owner_only
    async def gmute_cmd(client: Client, message: Message):
        args = message.command[1:]
        reason = " ".join(args[1:]) if len(args) > 1 else "No reason provided"

        target_id = None
        if args:
            try:
                target_id = int(args[0])
            except ValueError:
                pass
        if target_id is None and message.reply_to_message:
            target_id = message.reply_to_message.from_user.id

        if not target_id:
            await message.reply("Usage: /gmute <user_id> [reason]")
            return

        from plugins.utils import is_sudo
        if is_sudo(target_id):
            await message.reply("Cannot gmute a sudo user.")
            return

        await db.add_gmute(target_id, reason)
        await message.reply(
            f"User <code>{target_id}</code> has been globally muted.\n"
            f"<b>Reason:</b> {reason}\n"
            "Their messages will be deleted in all groups."
        )

    @app.on_message(filters.command("ungmute") & filters.private)
    @owner_only
    async def ungmute_cmd(client: Client, message: Message):
        args = message.command[1:]
        if not args:
            await message.reply("Usage: /ungmute <user_id>")
            return
        try:
            target_id = int(args[0])
        except ValueError:
            await message.reply("Invalid user ID.")
            return

        ok = await db.remove_gmute(target_id)
        await message.reply(
            f"User <code>{target_id}</code> has been globally unmuted."
            if ok else "This user is not globally muted."
        )

    @app.on_message(filters.command("gkick") & filters.private)
    @owner_only
    async def gkick_cmd(client: Client, message: Message):
        args = message.command[1:]
        if not args:
            await message.reply("Usage: /gkick <user_id>")
            return
        try:
            target_id = int(args[0])
        except ValueError:
            await message.reply("Invalid user ID.")
            return

        from plugins.utils import is_sudo
        if is_sudo(target_id):
            await message.reply("Cannot gkick a sudo user.")
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

        await message.reply(
            f"User <code>{target_id}</code> kicked from <b>{kicked}</b> groups."
        )

    @app.on_message(filters.command("gbanlist") & filters.private)
    @owner_only
    async def gbanlist_cmd(client: Client, message: Message):
        banned = await db.get_gban_list()
        if not banned:
            await message.reply("No globally banned users.")
            return
        lines = [
            f"• <code>{u['user_id']}</code> — {u.get('reason', 'N/A')}"
            for u in banned
        ]
        text = "<b>Globally Banned Users</b>\n\n" + "\n".join(lines)
        if len(text) > 4000:
            text = text[:4000] + "\n..."
        await message.reply(text)

    @app.on_message(filters.command("gmutelist") & filters.private)
    @owner_only
    async def gmutelist_cmd(client: Client, message: Message):
        muted = await db.get_gmute_list()
        if not muted:
            await message.reply("No globally muted users.")
            return
        lines = [
            f"• <code>{u['user_id']}</code> — {u.get('reason', 'N/A')}"
            for u in muted
        ]
        text = "<b>Globally Muted Users</b>\n\n" + "\n".join(lines)
        if len(text) > 4000:
            text = text[:4000] + "\n..."
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
