import asyncio
from pyrogram import Client, idle
from pytgcalls import PyTgCalls

import config
import database as db
from core.stream import init_stream
from helpers.logger import log, send_startup_log

# ─── Load All Plugins ─────────────────────────────────────────────────────────
import plugins.admin as admin
import plugins.controls as controls
import plugins.effects as effects
import plugins.invite as invite
import plugins.moderation as moderation
import plugins.owner as owner
import plugins.play as play
import plugins.playlist as playlist
import plugins.queue as queue
import plugins.quiz as quiz       # 🎮 Nawa Game Plugin
import plugins.search as search
import plugins.start as start
import plugins.stats as stats
import plugins.vc247 as vc247

async def main() -> None:
    # 1. Initialize Database
    log.info("Initializing Database...")
    await db.init()

    # 2. Setup Pyrogram Client
    app = Client(
        "JattMusicBot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN,
    )

    # 3. Setup PyTgCalls Engine
    call = PyTgCalls(app)

    # 4. Register All Plugins
    log.info("Loading Plugins...")
    admin.register(app)
    controls.register(app)
    effects.register(app)
    invite.register(app)
    moderation.register(app)
    owner.register(app)
    play.register(app)
    playlist.register(app)
    queue.register(app)
    quiz.register(app)           # Game Registered
    search.register(app)
    start.register(app)
    stats.register(app)
    vc247.register(app)

    # 5. Start Clients
    log.info("Starting Pyrogram Client...")
    await app.start()
    
    log.info("Initializing PyTgCalls Stream Engine...")
    init_stream(call, app)
    
    log.info("Starting PyTgCalls...")
    await call.start()

    # 6. Send Startup Log to Owner Group
    await send_startup_log(app)
    log.info("⏤͟͟͞͞★ Jatt Music Bot is now ONLINE & READY!")

    # 7. Keep Bot Running
    await idle()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Bot stopped by user.")
        
