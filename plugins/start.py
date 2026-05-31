from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

import database as db
from config import OWNER_CHANNEL, SUPPORT_GROUP, UPDATE_CHANNEL, START_IMAGE_URL
from plugins.utils import help_keyboard, start_keyboard

HELP_TEXT = {
    "playback": (
        "<b>Playback Commands</b>\n\n"
        "/play &lt;name or URL&gt; — Play a song\n"
        "/song &lt;name or URL&gt; — Alias for /play\n"
        "/vplay &lt;name or URL&gt; — Play video in VC\n"
        "/playforce &lt;name or URL&gt; — Force play (skips current)\n"
        "/search &lt;query&gt; — Search YouTube (5 results)\n"
        "/playlist &lt;URL&gt; — Load full YouTube playlist\n"
        "/np — Now playing info\n"
        "/queue — View current queue\n"
        "/history — Last 10 played songs\n"
        "/replay — Replay current song\n"
        "/skipto &lt;number&gt; — Jump to track number\n"
        "/songinfo — Full song info\n"
        "/mysongs — Songs you requested\n"
    ),
    "controls": (
        "<b>Control Commands</b>\n\n"
        "/pause — Pause playback\n"
        "/resume — Resume playback\n"
        "/mute — Mute bot audio in VC\n"
        "/unmute — Unmute bot audio in VC\n"
        "/skip — Skip to next track\n"
        "/stop — Stop and leave VC\n"
        "/shuffle — Shuffle the queue\n"
        "/loop — Toggle loop mode\n"
        "/seek &lt;time&gt; — Seek to position\n"
        "/speed &lt;0.5–2.0&gt; — Change speed\n"
        "/bass &lt;1–10&gt; — Bass boost\n"
        "/pitch &lt;0.5–2.0&gt; — Change pitch\n"
        "/reverb — Toggle reverb effect\n"
        "/nightcore — Toggle nightcore\n"
        "/normalise — Reset all effects\n"
        "/volume &lt;0–200&gt; — Set volume\n"
        "/remove &lt;pos&gt; — Remove track\n"
        "/move &lt;from&gt; &lt;to&gt; — Move track\n"
        "/clearqueue — Clear queue\n"
        "/fix — Force reconnect to VC\n"
        "/autoplay — Play a similar song now\n"
        "/247 — Toggle 24/7 mode\n"
        "/invite — Invite group members to VC\n"
    ),
    "admin": (
        "<b>Admin Commands</b>\n\n"
        "/auth — Reply to grant DJ role\n"
        "/unauth — Reply to remove DJ role\n"
        "/adminonly — Toggle admin-only controls\n"
        "/setlog &lt;channel_id&gt; — Set log channel\n"
        "/setwelcome &lt;text&gt; — Set welcome message\n"
        "/setprefix &lt;symbol&gt; — Change command prefix\n"
        "/quality &lt;high/medium/low&gt; — Set audio quality\n"
        "/topplays — Top 5 most played songs\n"
        "/topdjs — Top 5 song requesters\n"
        "/groupstats — Group music statistics\n"
        "/weekly — Top 5 songs this week\n"
        "/leaderboard — Full requester leaderboard\n"
        "/ban — Ban user from bot in this group\n"
        "/unban — Unban user in this group\n"
    ),
    "owner": (
        "<b>Owner / Sudo Commands</b>\n\n"
        "/broadcast — Broadcast message\n"
        "/stats — Global statistics\n"
        "/maintenance — Toggle maintenance mode\n"
        "/ping — Response time\n"
        "/uptime — Bot uptime\n"
        "/botinfo — Bot information\n"
        "/gban &lt;user_id&gt; — Global ban\n"
        "/ungban &lt;user_id&gt; — Remove global ban\n"
        "/gmute &lt;user_id&gt; — Global mute\n"
        "/ungmute &lt;user_id&gt; — Remove global mute\n"
        "/gkick &lt;user_id&gt; — Kick from all groups\n"
        "/gbanlist — List all globally banned users\n"
        "/gmutelist — List all globally muted users\n"
    ),
}

START_TEXT = (
    "<b>JATT MUSIC BOT</b>\n\n"
    "A powerful Telegram voice chat music bot.\n\n"
    "<b>Features:</b>\n"
    "- High quality audio streaming\n"
    "- YouTube search and playlists\n"
    "- Full audio effects (bass, reverb, nightcore)\n"
    "- Smart queue management\n"
    "- On-demand autoplay\n\n"
    "Add me to your group and use /play to start!"
)


def register(app: Client) -> None:

    @app.on_message(filters.command("start"))
    async def start_cmd(client: Client, message: Message):
        if not message.from_user:
            return
        user = message.from_user
        await db.upsert_user(user.id, user.first_name)

        kb = start_keyboard(SUPPORT_GROUP, OWNER_CHANNEL, UPDATE_CHANNEL)

        if message.chat.type.value == "private":
            if START_IMAGE_URL:
                try:
                    await message.reply_photo(START_IMAGE_URL, caption=START_TEXT, reply_markup=kb)
                    return
                except Exception:
                    pass
            await message.reply(START_TEXT, reply_markup=kb)
        else:
            await message.reply(START_TEXT, reply_markup=kb)

    @app.on_message(filters.command("help"))
    async def help_cmd(client: Client, message: Message):
        await message.reply(
            "<b>JATT MUSIC BOT — Help</b>\n\nChoose a category:",
            reply_markup=help_keyboard(),
        )

    @app.on_callback_query(filters.regex(r"^help_"))
    async def help_cb(client: Client, cb: CallbackQuery):
        data = cb.data.split("_", 1)[1]
        if data == "close":
            await cb.message.delete()
            return
        text = HELP_TEXT.get(data)
        if text:
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="help_back")]])
            await cb.message.edit(text, reply_markup=back_kb)
        elif data == "back":
            await cb.message.edit(
                "<b>JATT MUSIC BOT — Help</b>\n\nChoose a category:",
                reply_markup=help_keyboard(),
            )
        await cb.answer()

    @app.on_callback_query(filters.regex(r"^start_"))
    async def start_cb(client: Client, cb: CallbackQuery):
        action = cb.data.split("_", 1)[1]
        if action == "commands":
            await cb.answer("Use /help to see all commands", show_alert=True)
        elif action == "howtoplay":
            await cb.answer(
                "1. Add bot to group\n2. Join a voice chat\n3. Use /play <song name>",
                show_alert=True,
            )
        elif action == "stats":
            stats = await db.global_stats()
            await cb.answer(
                f"Users: {stats['total_users']}\nGroups: {stats['total_chats']}\nPlays: {stats['total_plays']}",
                show_alert=True,
            )
        elif action == "addgroup":
            await cb.answer("Add me to your group using the button below!", show_alert=True)
        else:
            await cb.answer()

    @app.on_callback_query(filters.regex(r"^close_"))
    async def close_cb(client: Client, cb: CallbackQuery):
        await cb.message.delete()
        await cb.answer()

    @app.on_callback_query(filters.regex(r"^noop$"))
    async def noop_cb(client: Client, cb: CallbackQuery):
        await cb.answer()
