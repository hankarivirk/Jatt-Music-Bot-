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
            await message.reply("Only DJs and admins can toggle 24/7 mode.")
            return
        current = await db.get_setting(chat_id, "vc247")
        new_val = not current
        await db.set_setting(chat_id, "vc247", new_val)
        if new_val:
            await message.reply(
                "<b>24/7 Mode Enabled</b>\n"
                "The bot will stay in the voice chat even when idle."
            )
        else:
            await message.reply(
                "<b>24/7 Mode Disabled</b>\n"
                "The bot will leave after 3 minutes of inactivity."
            )
