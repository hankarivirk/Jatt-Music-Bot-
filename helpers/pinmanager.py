from __future__ import annotations

from typing import Optional

from pyrogram import Client
from pyrogram.errors import ChatAdminRequired, MessageIdInvalid

_pinned: dict[int, int] = {}


async def pin_message(client: Client, chat_id: int, message_id: int) -> None:
    try:
        old_id = _pinned.pop(chat_id, None)
        if old_id and old_id != message_id:
            try:
                await client.unpin_chat_message(chat_id, old_id)
            except (MessageIdInvalid, ChatAdminRequired):
                pass
        await client.pin_chat_message(chat_id, message_id, disable_notification=True)
        _pinned[chat_id] = message_id
    except ChatAdminRequired:
        pass
    except Exception:
        pass


async def unpin_message(client: Client, chat_id: int) -> None:
    msg_id = _pinned.pop(chat_id, None)
    if not msg_id:
        return
    try:
        await client.unpin_chat_message(chat_id, msg_id)
    except (MessageIdInvalid, ChatAdminRequired):
        pass
    except Exception:
        pass


def get_pinned(chat_id: int) -> Optional[int]:
    return _pinned.get(chat_id)
