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
            await message.reply("Only DJs and admins can use /invite.")
            return

        msg = await message.reply("Inviting group members to voice chat...")

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
                f"Invitation complete.\n"
                f"<b>Invited:</b> {invited}\n"
                f"<b>Failed:</b> {failed}"
            )
        except Exception as e:
            await msg.edit(f"Could not invite members: {e}")
