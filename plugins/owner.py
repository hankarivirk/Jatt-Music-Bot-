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
        msg = await message.reply("Pong!")
        elapsed = (time.monotonic() - start) * 1000
        await msg.edit(f"Pong! <b>{elapsed:.2f}ms</b>")

    @app.on_message(filters.command("uptime") & filters.private)
    @owner_only
    async def uptime_cmd(client: Client, message: Message):
        delta = timedelta(seconds=int(time.monotonic() - _START_TIME))
        days = delta.days
        hours, rem = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        await message.reply(
            f"<b>Uptime:</b> {days}d {hours}h {minutes}m {seconds}s"
        )

    @app.on_message(filters.command("stats") & filters.private)
    @owner_only
    async def stats_cmd(client: Client, message: Message):
        stats = await db.global_stats()
        await message.reply(
            f"<b>JATT MUSIC BOT — Global Stats</b>\n\n"
            f"<b>Total Users:</b> {stats['total_users']}\n"
            f"<b>Total Groups:</b> {stats['total_chats']}\n"
            f"<b>Total Plays:</b> {stats['total_plays']}"
        )

    @app.on_message(filters.command("botinfo") & filters.private)
    @owner_only
    async def botinfo_cmd(client: Client, message: Message):
        import sys
        import platform
        me = await client.get_me()
        await message.reply(
            f"<b>Bot Information</b>\n\n"
            f"<b>Name:</b> {me.first_name}\n"
            f"<b>Username:</b> @{me.username}\n"
            f"<b>Version:</b> {config.BOT_VERSION}\n"
            f"<b>Python:</b> {sys.version.split()[0]}\n"
            f"<b>Platform:</b> {platform.system()} {platform.release()}"
        )

    @app.on_message(filters.command("maintenance") & filters.private)
    @owner_only
    async def maintenance_cmd(client: Client, message: Message):
        config.MAINTENANCE_MODE = not config.MAINTENANCE_MODE
        state = "enabled" if config.MAINTENANCE_MODE else "disabled"
        await message.reply(f"Maintenance mode <b>{state}</b>.")

    @app.on_message(filters.command("broadcast") & filters.private)
    @owner_only
    async def broadcast_cmd(client: Client, message: Message):
        args = message.command[1:]
        if not args:
            await message.reply(
                "Usage: /broadcast -all/-users/-groups/-pin <message>\n\n"
                "Flags:\n"
                "-all: Send to all users and groups\n"
                "-users: Send to all private users only\n"
                "-groups: Send to all groups only\n"
                "-pin: Pin message in groups"
            )
            return

        flags = {a for a in args if a.startswith("-")}
        text_parts = [a for a in args if not a.startswith("-")]
        text = " ".join(text_parts).strip()

        if not text:
            if message.reply_to_message:
                text = message.reply_to_message.text or ""
            if not text:
                await message.reply("Please provide a message to broadcast.")
                return

        pin = "-pin" in flags
        send_to_users = "-all" in flags or "-users" in flags
        send_to_groups = "-all" in flags or "-groups" in flags

        msg = await message.reply("Broadcasting...")

        sent = 0
        failed = 0

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
            f"<b>Broadcast complete</b>\n"
            f"<b>Sent:</b> {sent}\n"
            f"<b>Failed:</b> {failed}"
        )
