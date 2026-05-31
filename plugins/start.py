from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

import database as db
from config import OWNER_CHANNEL, SUPPORT_GROUP, UPDATE_CHANNEL, START_IMAGE_URL
from plugins.utils import help_keyboard, start_keyboard

# Premium Formatted Help Text
HELP_TEXT = {
    "playback": (
        "⏤͟͟͞͞★ **Pʟᴀʏʙᴀᴄᴋ Cᴏᴍᴍᴀɴᴅs**\n\n"
        "✧ `/play` ᴏʀ `/song` : Pʟᴀʏ ᴀ sᴏɴɢ (Nᴀᴍᴇ ᴏʀ Uʀʟ)\n"
        "✧ `/vplay` : Pʟᴀʏ ᴠɪᴅᴇᴏ ɪɴ VC\n"
        "✧ `/playforce` : Fᴏʀᴄᴇ ᴘʟᴀʏ (Sᴋɪᴘs ᴄᴜʀʀᴇɴᴛ)\n"
        "✧ `/search` : Sᴇᴀʀᴄʜ ᴛʀᴀᴄᴋs ᴏɴ YᴏᴜTᴜʙᴇ\n"
        "✧ `/playlist` : Lᴏᴀᴅ ᴀ ғᴜʟʟ YᴏᴜTᴜʙᴇ ᴘʟᴀʏʟɪsᴛ\n"
        "✧ `/np` : Cᴜʀʀᴇɴᴛ ᴘʟᴀʏɪɴɢ ɪɴғᴏ\n"
        "✧ `/queue` : Vɪᴇᴡ ᴄᴜʀʀᴇɴᴛ ǫᴜᴇᴜᴇ\n"
        "✧ `/history` : Lᴀsᴛ 10 ᴘʟᴀʏᴇᴅ ᴛʀᴀᴄᴋs\n"
        "✧ `/replay` : Rᴇᴘʟᴀʏ ᴄᴜʀʀᴇɴᴛ sᴏɴɢ\n"
        "✧ `/skipto` : Jᴜᴍᴘ ᴛᴏ ᴀ ᴛʀᴀᴄᴋ ɴᴜᴍʙᴇʀ\n"
        "✧ `/mysongs` : Tʀᴀᴄᴋs ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ ʏᴏᴜ\n"
    ),
    "controls": (
        "⏤͟͟͞͞★ **Cᴏɴᴛʀᴏʟ Cᴏᴍᴍᴀɴᴅs**\n\n"
        "✧ `/pause` : Pᴀᴜsᴇ ᴛʜᴇ sᴛʀᴇᴀᴍ\n"
        "✧ `/resume` : Rᴇsᴜᴍᴇ ᴘʟᴀʏʙᴀᴄᴋ\n"
        "✧ `/mute` / `/unmute` : Mᴜᴛᴇ ʙᴏᴛ ɪɴ VC\n"
        "✧ `/skip` : Sᴋɪᴘ ᴛᴏ ɴᴇxᴛ ᴛʀᴀᴄᴋ\n"
        "✧ `/stop` : Sᴛᴏᴘ ᴀɴᴅ ʟᴇᴀᴠᴇ VC\n"
        "✧ `/shuffle` : Sʜᴜғғʟᴇ ᴛʜᴇ ǫᴜᴇᴜᴇ\n"
        "✧ `/loop` : Tᴏɢɢʟᴇ ʟᴏᴏᴘ ᴍᴏᴅᴇ\n"
        "✧ `/seek` : Sᴇᴇᴋ (Fᴡᴅ/Bᴀᴄᴋ)\n"
        "✧ `/speed` : Cʜᴀɴɢᴇ sᴘᴇᴇᴅ (0.5-2.0)\n"
        "✧ `/bass` : Bᴀss ʙᴏᴏsᴛ ʟᴇᴠᴇʟ (1-10)\n"
        "✧ `/pitch` : Cʜᴀɴɢᴇ ᴘɪᴛᴄʜ (0.5-2.0)\n"
        "✧ `/reverb` / `/nightcore` : Aᴜᴅɪᴏ ᴇғғᴇᴄᴛs\n"
        "✧ `/volume` : Sᴇᴛ ᴠᴏʟᴜᴍᴇ (0-200)\n"
        "✧ `/clearqueue` : Cʟᴇᴀʀ ᴇɴᴛɪʀᴇ ǫᴜᴇᴜᴇ\n"
        "✧ `/autoplay` : Aᴜᴛᴏ-ᴘʟᴀʏ sɪᴍɪʟᴀʀ ᴛʀᴀᴄᴋ\n"
    ),
    "admin": (
        "⏤͟͟͞͞★ **Aᴅᴍɪɴ Cᴏᴍᴍᴀɴᴅs**\n\n"
        "✧ `/auth` / `/unauth` : Gʀᴀɴᴛ ᴏʀ ʀᴇᴍᴏᴠᴇ DJ Rᴏʟᴇ\n"
        "✧ `/adminonly` : Tᴏɢɢʟᴇ ᴀᴅᴍɪɴ-ᴏɴʟʏ ᴄᴏɴᴛʀᴏʟs\n"
        "✧ `/setlog` : Sᴇᴛ Gʀᴏᴜᴘ ʟᴏɢ ᴄʜᴀɴɴᴇʟ\n"
        "✧ `/setwelcome` : Sᴇᴛ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ\n"
        "✧ `/setprefix` : Cʜᴀɴɢᴇ ᴄᴏᴍᴍᴀɴᴅ ᴘʀᴇғɪx\n"
        "✧ `/quality` : Sᴇᴛ Aᴜᴅɪᴏ Qᴜᴀʟɪᴛʏ\n"
        "✧ `/topplays` : Mᴏsᴛ ᴘʟᴀʏᴇᴅ sᴏɴɢs\n"
        "✧ `/leaderboard` : Tᴏᴘ ʀᴇǫᴜᴇsᴛᴇʀs\n"
        "✧ `/ban` / `/unban` : Bᴀɴ/Uɴʙᴀɴ ᴜsᴇʀ ғʀᴏᴍ Bᴏᴛ\n"
    ),
    "owner": (
        "⏤͟͟͞͞★ **Oᴡɴᴇʀ Cᴏᴍᴍᴀɴᴅs**\n\n"
        "✧ `/broadcast` : Sᴇɴᴅ ᴍᴇssᴀɢᴇ ᴛᴏ ᴀʟʟ\n"
        "✧ `/stats` : Bᴏᴛ ɢʟᴏʙᴀʟ sᴛᴀᴛs\n"
        "✧ `/maintenance` : Tᴏɢɢʟᴇ Mᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴍᴏᴅᴇ\n"
        "✧ `/ping` / `/uptime` : Cʜᴇᴄᴋ sᴛᴀᴛᴜs\n"
        "✧ `/gban` / `/ungban` : Gʟᴏʙᴀʟ Bᴀɴ ᴀ ᴜsᴇʀ\n"
    ),
}

def register(app: Client) -> None:

    @app.on_message(filters.command("start"))
    async def start_cmd(client: Client, message: Message):
        if not message.from_user:
            return
        user = message.from_user
        me = await client.get_me()
        await db.upsert_user(user.id, user.first_name)

        start_text = (
            f"⏤͟͟͞͞★ **Wᴇʟᴄᴏᴍᴇ ᴛᴏ {me.first_name.upper()}**\n\n"
            f"✧ **Tʜᴇ ᴜʟᴛɪᴍᴀᴛᴇ Lᴀɢ-Fʀᴇᴇ Vᴏɪᴄᴇ Cʜᴀᴛ Mᴜsɪᴄ Pʟᴀʏᴇʀ.**\n"
            f"✧ Sᴛʀᴇᴀᴍ ʜɪɢʜ-ǫᴜᴀʟɪᴛʏ ᴀᴜᴅɪᴏ, ᴍᴀɴᴀɢᴇ sᴍᴀʀᴛ ǫᴜᴇᴜᴇs, "
            f"ᴀɴᴅ ᴇxᴘᴇʀɪᴇɴᴄᴇ ᴘʀᴇᴍɪᴜᴍ ᴀᴜᴅɪᴏ ᴇғғᴇᴄᴛs.\n\n"
            f"➕ **Aᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ** ᴀɴᴅ ᴜsᴇ `/play` ᴛᴏ ʙᴇɢɪɴ!"
        )

        kb = start_keyboard(SUPPORT_GROUP, OWNER_CHANNEL, UPDATE_CHANNEL)

        if message.chat.type.value == "private":
            if START_IMAGE_URL:
                try:
                    await message.reply_photo(START_IMAGE_URL, caption=start_text, reply_markup=kb)
                    return
                except Exception:
                    pass
            await message.reply(start_text, reply_markup=kb)
        else:
            await message.reply(start_text, reply_markup=kb)

    @app.on_message(filters.command("help"))
    async def help_cmd(client: Client, message: Message):
        me = await client.get_me()
        await message.reply(
            f"⏤͟͟͞͞★ **{me.first_name.upper()} ⏤ Hᴇʟᴘ Mᴇɴᴜ**\n\n✧ Cʜᴏᴏsᴇ ᴀ ᴄᴀᴛᴇɢᴏʀʏ ʙᴇʟᴏᴡ ᴛᴏ ᴠɪᴇᴡ ᴄᴏᴍᴍᴀɴᴅs:",
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
            back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("◁ Bᴀᴄᴋ", callback_data="help_back")]])
            await cb.message.edit(text, reply_markup=back_kb)
        elif data == "back":
            me = await client.get_me()
            await cb.message.edit(
                f"⏤͟͟͞͞★ **{me.first_name.upper()} ⏤ Hᴇʟᴘ Mᴇɴᴜ**\n\n✧ Cʜᴏᴏsᴇ ᴀ ᴄᴀᴛᴇɢᴏʀʏ ʙᴇʟᴏᴡ ᴛᴏ ᴠɪᴇᴡ ᴄᴏᴍᴍᴀɴᴅs:",
                reply_markup=help_keyboard(),
            )
        await cb.answer()

    @app.on_callback_query(filters.regex(r"^start_"))
    async def start_cb(client: Client, cb: CallbackQuery):
        action = cb.data.split("_", 1)[1]
        if action == "commands":
            await cb.answer("Usᴇ /help ᴛᴏ sᴇᴇ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs", show_alert=True)
        elif action == "howtoplay":
            await cb.answer(
                "1. Aᴅᴅ Bᴏᴛ ᴛᴏ Gʀᴏᴜᴘ\n2. Jᴏɪɴ Vᴏɪᴄᴇ Cʜᴀᴛ\n3. Sᴇɴᴅ /play <sᴏɴɢ ɴᴀᴍᴇ>",
                show_alert=True,
            )
        elif action == "stats":
            stats = await db.global_stats()
            await cb.answer(
                f"📊 Gʟᴏʙᴀʟ Sᴛᴀᴛs:\n\n👥 Usᴇʀs: {stats['total_users']}\n💬 Gʀᴏᴜᴘs: {stats['total_chats']}\n🎵 Pʟᴀʏs: {stats['total_plays']}",
                show_alert=True,
            )
        elif action == "addgroup":
            await cb.answer("Tᴀᴘ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ᴀᴅᴅ ᴍᴇ!", show_alert=True)
        else:
            await cb.answer()

    @app.on_callback_query(filters.regex(r"^close_"))
    async def close_cb(client: Client, cb: CallbackQuery):
        await cb.message.delete()
        await cb.answer()

    @app.on_callback_query(filters.regex(r"^noop$"))
    async def noop_cb(client: Client, cb: CallbackQuery):
        await cb.answer()
        
