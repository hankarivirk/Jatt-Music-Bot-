from __future__ import annotations

import asyncio
import importlib
import sys

# --- PYTGCALLS PYROGRAM V2 FIX ---
# Pyrogram 2.x vich GroupcallForbidden nahi hunda, is layi aapa fake create kar rahe haan
# taaki pytgcalls import karan lagge crash na hove.
import pyrogram.errors
if not hasattr(pyrogram.errors, "GroupcallForbidden"):
    class GroupcallForbidden(Exception):
        pass
    pyrogram.errors.GroupcallForbidden = GroupcallForbidden
# ---------------------------------

from pyrogram import Client, idle
from pyrogram.types import BotCommand
from pytgcalls import PyTgCalls

from config import (
    API_HASH,
    API_ID,
    ASSISTANT_SESSION,
    BOT_TOKEN,
    LOG_GROUP_ID,
    MONGO_URI,
    OWNER_ID,
)
from core.stream import init_stream
from database import init_db
from helpers.logger import log, send_startup_log

PLUGIN_MODULES = [
    "plugins.start",
    "plugins.play",
    "plugins.controls",
    "plugins.effects",
    "plugins.queue",
    "plugins.search",
    "plugins.playlist",
    "plugins.admin",
    "plugins.stats",
    "plugins.moderation",
    "plugins.owner",
    "plugins.invite",
    "plugins.vc247",
]

BOT_COMMANDS = [
    BotCommand("play", "Play a song by name or URL"),
    BotCommand("search", "Search YouTube for a song"),
    BotCommand("np", "Now playing card"),
    BotCommand("queue", "View the current queue"),
    BotCommand("skip", "Skip to next track"),
    BotCommand("pause", "Pause playback"),
    BotCommand("resume", "Resume playback"),
    BotCommand("stop", "Stop and leave voice chat"),
    BotCommand("shuffle", "Shuffle the queue"),
    BotCommand("loop", "Toggle loop mode"),
    BotCommand("volume", "Set volume (0-200)"),
    BotCommand("help", "Show all commands"),
]


def _validate_config() -> None:
    missing = []
    if not API_ID:
        missing.append("API_ID")
    if not API_HASH:
        missing.append("API_HASH")
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not OWNER_ID:
        missing.append("OWNER_ID")
    if not ASSISTANT_SESSION:
        missing.append("ASSISTANT_SESSION")
    if not MONGO_URI:
        missing.append("MONGO_URI")
    if missing:
        log.critical(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)
    if not LOG_GROUP_ID:
        log.warning("LOG_GROUP_ID not set — startup/error logs will only go to stdout")


async def main() -> None:
    _validate_config()

    log.info("Connecting to MongoDB...")
    await init_db()
    log.info("MongoDB connected.")

    bot = Client(
        "jatt_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
    )

    assistant = Client(
        "jatt_assistant",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=ASSISTANT_SESSION,
        no_updates=True,
    )

    call = PyTgCalls(assistant)

    # Register pytgcalls callbacks + store bot client reference
    init_stream(call, bot)

    log.info("Registering plugins...")
    for module_name in PLUGIN_MODULES:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "register"):
                module.register(bot)
                log.info(f"  Loaded: {module_name}")
            else:
                log.warning(f"  No register() in {module_name} — skipping")
        except Exception as e:
            log.error(f"  Failed to load {module_name}: {e}", exc_info=True)

    log.info("Starting clients...")
    await bot.start()
    await assistant.start()
    await call.start()

    me = await bot.get_me()
    log.info(f"Bot started as @{me.username} (ID: {me.id})")

    # Set bot commands via API
    try:
        await bot.set_bot_commands(BOT_COMMANDS)
        log.info("Bot commands registered.")
    except Exception as e:
        log.warning(f"Could not set bot commands: {e}")

    # Validate LOG_GROUP_ID access
    if LOG_GROUP_ID:
        try:
            member = await bot.get_chat_member(LOG_GROUP_ID, me.id)
            if member.status.value not in ("administrator", "creator"):
                log.warning(
                    "Bot is not admin in LOG_GROUP_ID — promote it to send logs"
                )
        except Exception:
            log.warning(
                "Could not access LOG_GROUP_ID — make sure bot is added and promoted"
            )

    await send_startup_log(bot)

    log.info("JATT MUSIC BOT is running. Press Ctrl+C to stop.")

    # Use pyrogram's idle() — properly handles signals and keeps the loop alive
    await idle()

    log.info("Shutting down...")
    await call.stop()
    await assistant.stop()
    await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
        
