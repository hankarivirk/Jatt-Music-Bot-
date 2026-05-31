import logging
import sys
from datetime import datetime

from config import LOG_GROUP_ID, BOT_VERSION

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

log = logging.getLogger("jatt")

async def send_startup_log(bot) -> None:
    if not LOG_GROUP_ID:
        return
    me = await bot.get_me()
    text = (
        f"⏤͟͟͞͞★ **{me.first_name.upper()} ⏤ Oɴʟɪɴᴇ ⚡️**\n\n"
        f"✧ **Vᴇʀsɪᴏɴ:** `v{BOT_VERSION}`\n"
        f"✧ **Tɪᴍᴇ:** `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`\n"
        f"✧ **Sᴛᴀᴛᴜs:** `Sʏsᴛᴇᴍ ᴀᴄᴛɪᴠᴇ & ʀᴇᴀᴅʏ`"
    )
    try:
        await bot.send_message(LOG_GROUP_ID, text)
    except Exception as e:
        log.warning(f"Could not send startup log: {e}")

async def send_error_log(bot, error: Exception, context: str = "") -> None:
    if not LOG_GROUP_ID:
        return
    text = (
        f"⏤͟͟͞͞★ **Sʏsᴛᴇᴍ Eʀʀᴏʀ ⚠️**\n\n"
        f"✧ **Cᴏɴᴛᴇxᴛ:** `{context}`\n"
        f"✧ **Lᴏɢ:** `{type(error).__name__}: {error}`"
    )
    try:
        await bot.send_message(LOG_GROUP_ID, text)
    except Exception:
        pass
        
