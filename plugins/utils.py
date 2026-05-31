from __future__ import annotations

import functools
from typing import Callable

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

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
        # Pyrogram 2.x: group owner status value is "owner", not "creator"
        return member.status.value in ("administrator", "owner")
    except Exception:
        return False


async def is_dj_or_admin(client: Client, chat_id: int, user_id: int) -> bool:
    if await is_admin(client, chat_id, user_id):
        return True
    return await db.is_dj(chat_id, user_id)


# ─── Keyboards ────────────────────────────────────────────────────────────────

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def now_playing_keyboard(chat_id: int, paused: bool = False) -> InlineKeyboardMarkup:
    pause_text = "Resume" if paused else "Pause"
    pause_cb = f"np_resume_{chat_id}" if paused else f"np_pause_{chat_id}"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(pause_text, callback_data=pause_cb),
            InlineKeyboardButton("Skip", callback_data=f"np_skip_{chat_id}"),
            InlineKeyboardButton("Stop", callback_data=f"np_stop_{chat_id}"),
        ],
        [
            InlineKeyboardButton("Vol-", callback_data=f"np_voldwn_{chat_id}"),
            InlineKeyboardButton("Vol+", callback_data=f"np_volup_{chat_id}"),
            InlineKeyboardButton("Shuffle", callback_data=f"np_shuffle_{chat_id}"),
        ],
        [
            InlineKeyboardButton("Loop", callback_data=f"np_loop_{chat_id}"),
            InlineKeyboardButton("Queue", callback_data=f"np_queue_{chat_id}"),
            InlineKeyboardButton("Replay", callback_data=f"np_replay_{chat_id}"),
        ],
    ])


def loop_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Track", callback_data=f"loop_track_{chat_id}"),
            InlineKeyboardButton("Queue", callback_data=f"loop_queue_{chat_id}"),
            InlineKeyboardButton("Off", callback_data=f"loop_off_{chat_id}"),
        ]
    ])


def seek_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Back 10s", callback_data=f"seek_back_{chat_id}"),
            InlineKeyboardButton("Forward 10s", callback_data=f"seek_fwd_{chat_id}"),
            InlineKeyboardButton("Close", callback_data=f"close_{chat_id}"),
        ]
    ])


def queue_keyboard(chat_id: int, page: int, total_pages: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "Prev" if page > 1 else " ",
                callback_data=f"queue_prev_{chat_id}_{page}" if page > 1 else "noop",
            ),
            InlineKeyboardButton(
                f"{page}/{total_pages}", callback_data="noop"
            ),
            InlineKeyboardButton(
                "Next" if page < total_pages else " ",
                callback_data=f"queue_next_{chat_id}_{page}" if page < total_pages else "noop",
            ),
            InlineKeyboardButton("Close", callback_data=f"close_{chat_id}"),
        ]
    ])


def start_keyboard(support: str = "", channel: str = "", updates: str = "") -> InlineKeyboardMarkup:
    buttons = []
    row1 = [InlineKeyboardButton("Add to Group", callback_data="start_addgroup")]
    row1.append(InlineKeyboardButton("Commands", callback_data="start_commands"))
    buttons.append(row1)
    row2 = []
    if updates:
        row2.append(InlineKeyboardButton("Updates", url=updates))
    if support:
        row2.append(InlineKeyboardButton("Support", url=support))
    if row2:
        buttons.append(row2)
    buttons.append([
        InlineKeyboardButton("How to Play", callback_data="start_howtoplay"),
        InlineKeyboardButton("Stats", callback_data="start_stats"),
    ])
    if channel:
        buttons.append([InlineKeyboardButton("Owner Channel", url=channel)])
    return InlineKeyboardMarkup(buttons)


def help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Playback", callback_data="help_playback"),
            InlineKeyboardButton("Controls", callback_data="help_controls"),
        ],
        [
            InlineKeyboardButton("Admin", callback_data="help_admin"),
            InlineKeyboardButton("Owner", callback_data="help_owner"),
        ],
        [InlineKeyboardButton("Close", callback_data="help_close")],
    ])


# ─── Decorators ───────────────────────────────────────────────────────────────

def owner_only(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(client: Client, message: Message):
        if not message.from_user:
            return
        if not is_sudo(message.from_user.id):
            return await message.reply("This command is for owner/sudo only.")
        return await func(client, message)
    return wrapper


def group_admin_only(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(client: Client, message: Message):
        if not message.from_user:
            return
        if not await is_admin(client, message.chat.id, message.from_user.id):
            return await message.reply("This command is for group admins only.")
        return await func(client, message)
    return wrapper


def maintenance_check(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(client: Client, message: Message):
        if not message.from_user:
            return
        import config
        if config.MAINTENANCE_MODE and not is_sudo(message.from_user.id):
            return await message.reply("Bot is in maintenance mode. Please try again later.")
        return await func(client, message)
    return wrapper


# ─── Helpers ──────────────────────────────────────────────────────────────────

def format_track(track: dict, index: int = 0) -> str:
    from helpers.downloader import format_duration
    dur = format_duration(track.get("duration", 0))
    title = track.get("title", "Unknown")
    requester = track.get("requester", "Unknown")
    prefix = f"{index}. " if index else ""
    return f"{prefix}<b>{title}</b> [{dur}] — {requester}"
