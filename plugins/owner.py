from __future__ import annotations

import asyncio
import time
from datetime import timedelta

from pyrogram import Client, filters
from pyrogram.types import Message

import config
import database as db
from plugins.utils import owner_only

_START_TIME = time.monotonic()

def register(app: Client) -> None:

    @app.on_message(filters.command("ping") & filters.private)
    @owner_only
    async def ping_cmd(client: Client, message: Message):
        start = time.monotonic()
        msg = await message.reply("`[ ◯ ] ᴘɪɴɢɪɴɢ sᴇʀᴠᴇʀ...`")
        elapsed = (time.monotonic() - start) * 1000
        await msg.edit(f"`[ ⚡️ ] sʏsᴛᴇᴍ ᴏɴʟɪɴᴇ: {elapsed:.2f}ᴍs`")

    @app.on_message(filters.command("uptime") & filters.private)
    @owner_only
    async def uptime_cmd(client: Client, message: Message):
        delta = timedelta(seconds=int(time.monotonic() - _START_TIME))
        days = delta.days
        hours, rem = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        await message.reply(f"⏤͟͟͞͞★ **Sʏsᴛᴇᴍ Uᴘᴛɪᴍᴇ :**\n✧ `{days}d {hours}h {minutes}m {seconds}s`")

    @app.on_message(filters.command("stats") & filters.private)
    @owner_only
    async def stats_cmd(client: Client, message: Message):
        stats = await db.global_stats()
        me = await client.get_me()
        await message.reply(
            f"⏤͟͟͞͞★ **{me.first_name.upper()} — Gʟᴏʙᴀʟ Sᴛᴀᴛs**\n\n"
            f"✧ **Tᴏᴛᴀʟ Usᴇʀs:** `{stats['total_users']}`\n"
            f"✧ **Tᴏᴛᴀʟ Gʀᴏᴜᴘs:** `{stats['total_chats']}`\n"
            f"✧ **Tᴏᴛᴀʟ Pʟᴀʏs:** `{stats['total_plays']}`"
        )

    @app.on_message(filters.command("botinfo") & filters.private)
    @owner_only
    async def botinfo_cmd(client: Client, message: Message):
        import sys
        import platform
        me = await client.get_me()
        await message.reply(
            f"⏤͟͟͞͞★ **Bᴏᴛ Iɴғᴏʀᴍᴀᴛɪᴏɴ**\n\n"
            f"✧ **Nᴀᴍᴇ:** {me.first_name}\n"
            f"✧ **Usᴇʀɴᴀᴍᴇ:** @{me.username}\n"
            f"✧ **Vᴇʀsɪᴏɴ:** `{config.BOT_VERSION}`\n"
            f"✧ **Pʏᴛʜᴏɴ:** `{sys.version.split()[0]}`\n"
            f"✧ **Pʟᴀᴛғᴏʀᴍ:** `{platform.system()} {platform.release()}`"
        )

    @app.on_message(filters.command("maintenance") & filters.private)
    @owner_only
    async def maintenance_cmd(client: Client, message: Message):
        config.MAINTENANCE_MODE = not config.MAINTENANCE_MODE
        state = "Eɴᴀʙʟᴇᴅ" if config.MAINTENANCE_MODE else "Dɪsᴀʙʟᴇᴅ"
        await message.reply(f"⏤͟͟͞͞★ **Mᴀɪɴᴛᴇɴᴀɴᴄᴇ Mᴏᴅᴇ :** `{state}`")

    @app.on_message(filters.command("broadcast") & filters.private)
    @owner_only
    async def broadcast_cmd(client: Client, message: Message):
        args = message.command[1:]
        if not args:
            await message.reply(
                "✧ **Usaɢᴇ:** `/broadcast -all/-users/-groups/-pin [message]`\n\n"
                "**Fʟᴀɢs:**\n"
                "`-all` : Sᴇɴᴅ ᴛᴏ ᴀʟʟ ᴜsᴇʀs & ɢʀᴏᴜᴘs\n"
                "`-users` : Pʀɪᴠᴀᴛᴇ ᴜsᴇʀs ᴏɴʟʏ\n"
                "`-groups` : Gʀᴏᴜᴘs ᴏɴʟʏ\n"
                "`-pin` : Pɪɴ ᴍᴇssᴀɢᴇ ɪɴ ɢʀᴏᴜᴘs"
            )
            return

        flags = {a for a in args if a.startswith("-")}
        text_parts = [a for a in args if not a.startswith("-")]
        text = " ".join(text_parts).strip()

        if not text:
            if message.reply_to_message:
                text = message.reply_to_message.text or ""
            if not text:
                await message.reply("⚠️ Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ.")
                return

        pin = "-pin" in flags
        send_to_users = "-all" in flags or "-users" in flags
        send_to_groups = "-all" in flags or "-groups" in flags

        msg = await message.reply("`[ 🔄 ] Bʀᴏᴀᴅᴄᴀsᴛɪɴɢ ɪɴ ᴘʀᴏɢʀᴇss...`")

        sent, failed = 0, 0

        if send_to_users:
            users = await db.get_all_users()
            for user in users:
                try:
                    await client.send_message(user["user_id"], text)
                    sent += 1
                    await asyncio.sleep(0.05)
                except Exception:
                    failed += 1

        if send_to_groups:
            chats = await db.get_all_chats()
            for chat in chats:
                try:
                    m = await client.send_message(chat["chat_id"], text)
                    if pin:
                        try:
                            await client.pin_chat_message(chat["chat_id"], m.id, disable_notification=True)
                        except Exception:
                            pass
                    sent += 1
                    await asyncio.sleep(0.05)
                except Exception:
                    failed += 1

        await msg.edit(
            f"⏤͟͟͞͞★ **Bʀᴏᴀᴅᴄᴀsᴛ Cᴏᴍᴘʟᴇᴛᴇ**\n\n"
            f"✧ **Sᴇɴᴛ:** `{sent}`\n"
            f"✧ **Fᴀɪʟᴇᴅ:** `{failed}`"
        )
        
