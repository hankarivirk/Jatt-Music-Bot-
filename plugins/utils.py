from __future__ import annotations

import functools
from typing import Callable

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup

import database as db
from config import OWNER_ID, SUDO_USERS, MAINTENANCE_MODE

# ─── Permission Checks ────────────────────────────────────────────────────────

def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

def is_sudo(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in SUDO_USERS

async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    if is_sudo(user_id):
        return True
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status.value in ("administrator", "owner")
    except Exception:
        return False

async def is_dj_or_admin(client: Client, chat_id: int, user_id: int) -> bool:
    if await is_admin(client, chat_id, user_id):
        return True
    return await db.is_dj(chat_id, user_id)

# ─── Premium Keyboards ────────────────────────────────────────────────────────

def now_playing_keyboard(chat_id: int, paused: bool = False) -> InlineKeyboardMarkup:
    play_pause_btn = InlineKeyboardButton("▷ ᴘʟᴀʏ", callback_data=f"np_resume_{chat_id}") if paused else InlineKeyboardButton("❙❙ ᴘᴀᴜsᴇ", callback_data=f"np_pause_{chat_id}")
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("◁ ᴘʀᴇᴠ", callback_data=f"seek_back_{chat_id}"),
            play_pause_btn,
            InlineKeyboardButton("ɴᴇxᴛ ▷", callback_data=f"np_skip_{chat_id}")
        ],
        [
            InlineKeyboardButton("⚙️ ᴄᴏɴᴛʀᴏʟs", callback_data=f"np_queue_{chat_id}"),
            InlineKeyboardButton("🛑 sᴛᴏᴘ", callback_data=f"np_stop_{chat_id}")
        ]
    ])

def loop_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔂 Tʀᴀᴄᴋ", callback_data=f"loop_track_{chat_id}"),
            InlineKeyboardButton("🔁 Qᴜᴇᴜᴇ", callback_data=f"loop_queue_{chat_id}"),
            InlineKeyboardButton("✖️ Oғғ", callback_data=f"loop_off_{chat_id}")
        ]
    ])

def seek_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏪ 10s", callback_data=f"seek_back_{chat_id}"),
            InlineKeyboardButton("10s ⏩", callback_data=f"seek_fwd_{chat_id}")
        ],
        [InlineKeyboardButton("🗑 Cʟᴏsᴇ", callback_data=f"close_{chat_id}")]
    ])

def queue_keyboard(chat_id: int, page: int, total_pages: int, track_indices: list[int]) -> InlineKeyboardMarkup:
    buttons = []
    
    # Track Jump Number Buttons
    row = []
    for i in track_indices:
        row.append(InlineKeyboardButton(f"[ {i} ]", callback_data=f"qjump_{chat_id}_{i}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Clean Pagination Buttons
    nav_row = []
    nav_row.append(InlineKeyboardButton("◁ ᴘʀᴇᴠ", callback_data=f"queue_prev_{chat_id}_{page}") if page > 1 else InlineKeyboardButton(" ", callback_data="noop"))
    nav_row.append(InlineKeyboardButton(f"📄 {page} / {total_pages}", callback_data="noop"))
    nav_row.append(InlineKeyboardButton("ɴᴇxᴛ ▷", callback_data=f"queue_next_{chat_id}_{page}") if page < total_pages else InlineKeyboardButton(" ", callback_data="noop"))
    
    buttons.append(nav_row)
    buttons.append([InlineKeyboardButton("🗑 Cʟᴏsᴇ", callback_data=f"close_{chat_id}")])
    return InlineKeyboardMarkup(buttons)

def start_keyboard(support: str = "", channel: str = "", updates: str = "") -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("➕ Aᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ Gʀᴏᴜᴘ", callback_data="start_addgroup")],
        [InlineKeyboardButton("📚 Cᴏᴍᴍᴀɴᴅs", callback_data="start_commands"), InlineKeyboardButton("📊 Sᴛᴀᴛs", callback_data="start_stats")]
    ]
    row2 = []
    if updates: row2.append(InlineKeyboardButton("📢 Uᴘᴅᴀᴛᴇs", url=updates))
    if support: row2.append(InlineKeyboardButton("💬 Sᴜᴘᴘᴏʀᴛ", url=support))
    if row2: buttons.append(row2)
    buttons.append([InlineKeyboardButton("❓ Hᴏᴡ ᴛᴏ Pʟᴀʏ", callback_data="start_howtoplay")])
    if channel: buttons.append([InlineKeyboardButton("👑 Oᴡɴᴇʀ", url=channel)])
    return InlineKeyboardMarkup(buttons)

def help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎵 Pʟᴀʏʙᴀᴄᴋ", callback_data="help_playback"),
            InlineKeyboardButton("⚙️ Cᴏɴᴛʀᴏʟs", callback_data="help_controls")
        ],
        [
            InlineKeyboardButton("🛡 Aᴅᴍɪɴ", callback_data="help_admin"),
            InlineKeyboardButton("👑 Oᴡɴᴇʀ", callback_data="help_owner")
        ],
        [InlineKeyboardButton("🗑 Cʟᴏsᴇ", callback_data="help_close")]
    ])

# ─── Decorators ───────────────────────────────────────────────────────────────

def owner_only(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(client: Client, message: Message):
        if not message.from_user: return
        if not is_sudo(message.from_user.id):
            return await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** Sudo/Owner only command.")
        return await func(client, message)
    return wrapper

def group_admin_only(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(client: Client, message: Message):
        if not message.from_user: return
        if not await is_admin(client, message.chat.id, message.from_user.id):
            return await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** Group Admins only.")
        return await func(client, message)
    return wrapper

def maintenance_check(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(client: Client, message: Message):
        if not message.from_user: return
        import config
        if config.MAINTENANCE_MODE and not is_sudo(message.from_user.id):
            return await message.reply("🛠 **Mᴀɪɴᴛᴇɴᴀɴᴄᴇ Mᴏᴅᴇ:** Bot is currently upgrading. Try again later.")
        return await func(client, message)
    return wrapper

# ─── Helpers ──────────────────────────────────────────────────────────────────

def format_track(track: dict, index: int = 0) -> str:
    from helpers.downloader import format_duration
    dur = format_duration(track.get("duration", 0))
    title = track.get("title", "Unknown")[:40]
    requester = track.get("requester", "Unknown")
    prefix = f"`{index}.`" if index else "✧"
    return f"{prefix} **{title}** `[{dur}]`\n   └ 👤 {requester}"
