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
    text = (
        f"<b>JATT MUSIC BOT v{BOT_VERSION} started</b>\n"
        f"<b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        f"<b>Status:</b> Online and ready"
    )
    try:
        await bot.send_message(LOG_GROUP_ID, text)
    except Exception as e:
        log.warning(f"Could not send startup log: {e}")


async def send_error_log(bot, error: Exception, context: str = "") -> None:
    if not LOG_GROUP_ID:
        return
    text = (
        f"<b>Error in JATT MUSIC BOT</b>\n"
        f"<b>Context:</b> {context}\n"
        f"<b>Error:</b> <code>{type(error).__name__}: {error}</code>"
    )
    try:
        await bot.send_message(LOG_GROUP_ID, text)
    except Exception:
        pass
