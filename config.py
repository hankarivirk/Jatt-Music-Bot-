import os
from dotenv import load_dotenv

load_dotenv()


def _int(key: str, default: int = 0) -> int:
    val = os.getenv(key, str(default))
    try:
        return int(val)
    except ValueError:
        return default


def _list(key: str) -> list[int]:
    raw = os.getenv(key, "")
    result = []
    for part in raw.split(","):
        part = part.strip()
        if part:
            try:
                result.append(int(part))
            except ValueError:
                pass
    return result


API_ID: int = _int("API_ID")
API_HASH: str = os.getenv("API_HASH", "")
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
OWNER_ID: int = _int("OWNER_ID")
ASSISTANT_SESSION: str = os.getenv("ASSISTANT_SESSION", "")
MONGO_URI: str = os.getenv("MONGO_URI", "")
START_IMAGE_URL: str = os.getenv("START_IMAGE_URL", "")

LOG_GROUP_ID: int = _int("LOG_GROUP_ID")
SUDO_USERS: list[int] = _list("SUDO_USERS")
OWNER_CHANNEL: str = os.getenv("OWNER_CHANNEL", "")
SUPPORT_GROUP: str = os.getenv("SUPPORT_GROUP", "")
UPDATE_CHANNEL: str = os.getenv("UPDATE_CHANNEL", "")
MAINTENANCE_MODE: bool = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"

ANTI_FLOOD_SECONDS: int = 3
NP_UPDATE_INTERVAL: int = 15
IDLE_TIMEOUT: int = 180
MAX_HISTORY: int = 100
BOT_VERSION: str = "2.0.0"
