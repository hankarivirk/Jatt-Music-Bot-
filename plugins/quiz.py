from __future__ import annotations

import asyncio
import random
import re

from pyrogram import Client, filters
from pyrogram.types import Message

import database as db
from core import stream as sm
from helpers.downloader import fetch_track
from plugins.utils import maintenance_check

# ─── Handpicked Desi Hits Database ────────────────────────────────────────────
QUIZ_TRACKS = [
    # Punjabi Hits
    {"title": "Same Beef", "query": "Same Beef Bohemia Sidhu Moosewala audio", "answers": ["same beef", "same beef bohemia"]},
    {"title": "Excuses", "query": "Excuses AP Dhillon audio", "answers": ["excuses", "excuse", "excuses ap dhillon"]},
    {"title": "Lover", "query": "Lover Diljit Dosanjh audio", "answers": ["lover", "lover diljit"]},
    {"title": "Brown Munde", "query": "Brown Munde AP Dhillon audio", "answers": ["brown munde", "brown munde ap dhillon"]},
    {"title": "295", "query": "295 Sidhu Moosewala audio", "answers": ["295", "two ninety five"]},
    {"title": "Khaab", "query": "Khaab Akhil audio", "answers": ["khaab", "khab", "khwab"]},
    {"title": "So High", "query": "So High Sidhu Moosewala audio", "answers": ["so high", "so high sidhu"]},
    {"title": "We Rollin", "query": "We Rollin Shubh audio", "answers": ["we rollin", "we rolling", "we rollin shubh"]},
    {"title": "Softly", "query": "Softly Karan Aujla audio", "answers": ["softly", "softly karan aujla"]},
    {"title": "Lemonade", "query": "Lemonade Diljit Dosanjh audio", "answers": ["lemonade", "lemonade diljit"]},
    
    # Bollywood / Hindi Hits
    {"title": "Tum Hi Ho", "query": "Tum Hi Ho Arijit Singh audio", "answers": ["tum hi ho", "tum hi ho arijit"]},
    {"title": "Chaleya", "query": "Chaleya Jawan Arijit Singh audio", "answers": ["chaleya", "chale ya", "chaleya jawan"]},
    {"title": "Apna Bana Le", "query": "Apna Bana Le Jawan audio", "answers": ["apna bana le", "apna banale"]},
    {"title": "Channa Mereya", "query": "Channa Mereya audio", "answers": ["channa mereya", "chana mereya"]},
    {"title": "Desi Kalakaar", "query": "Desi Kalakaar Yo Yo Honey Singh audio", "answers": ["desi kalakaar", "desi kalakar"]},
    {"title": "Blue Eyes", "query": "Blue Eyes Yo Yo Honey Singh audio", "answers": ["blue eyes", "blue eye"]},
    {"title": "Khairiyat", "query": "Khairiyat Arijit Singh audio", "answers": ["khairiyat", "khairiyat pucho"]},
]

# Active Quizzes Dictionary: chat_id -> dict
_active_quizzes: dict[int, dict] = {}

def clean_string(text: str) -> str:
    """Removes special characters and extra spaces for fuzzy matching."""
    return re.sub(r'[^a-z0-9]', '', text.lower().strip())

def register(app: Client) -> None:

    @app.on_message(filters.command("musicquiz") & filters.group)
    @maintenance_check
    async def musicquiz_cmd(client: Client, message: Message):
        chat_id = message.chat.id

        if chat_id in _active_quizzes:
            await message.reply("⚠️ **A ǫᴜɪᴢ ɪs ᴀʟʀᴇᴀᴅʏ ʀᴜɴɴɪɴɢ!** Gᴜᴇss ᴛʜᴇ sᴏɴɢ ǫᴜɪᴄᴋ!")
            return

        if sm.get_active(chat_id):
            await message.reply("🔇 **Pʟᴇᴀsᴇ sᴛᴏᴘ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ sᴛʀᴇᴀᴍ ғɪʀsᴛ.**\n✧ Usᴇ `/stop` ᴛᴏ ᴇɴᴅ ᴛʜᴇ ᴍᴜsɪᴄ, ᴛʜᴇɴ sᴛᴀʀᴛ ᴛʜᴇ ǫᴜɪᴢ.")
            return

        msg = await message.reply("`[ 🎮 ] Pʀᴇᴘᴀʀɪɴɢ ᴛʜᴇ ᴍᴜsɪᴄ ǫᴜɪᴢ... Lᴏᴀᴅɪɴɢ ᴀ Hɪᴛ Tʀᴀᴄᴋ!`")

        # Pick a random song from the database
        song = random.choice(QUIZ_TRACKS)
        info = await fetch_track(song["query"])

        if not info:
            await msg.edit("❌ **Eʀʀᴏʀ ʟᴏᴀᴅɪɴɢ ᴛʀᴀᴄᴋ.** Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.")
            return

        track = {
            "title": "Guess The Track! 🎮",
            "url": info["url"],
            "duration": info.get("duration", 0),
            "video_id": info.get("video_id", ""),
            "requester": "Jatt Music Quiz",
            "video": False,
        }

        try:
            # Play the track directly starting from 25 seconds (to skip silent intros)
            await sm.play(chat_id, track, video=False, seek=25)
        except Exception as e:
            await msg.edit(f"❌ **Fᴀɪʟᴇᴅ ᴛᴏ ᴊᴏɪɴ Vᴏɪᴄᴇ Cʜᴀᴛ:** `{str(e)}`")
            return

        # Setup Quiz State
        _active_quizzes[chat_id] = {
            "answers": [clean_string(a) for a in song["answers"]],
            "correct_title": song["title"],
            "winner": None,
        }

        await msg.edit(
            f"⏤͟͟͞͞★ **Mᴜsɪᴄ Qᴜɪᴢ Sᴛᴀʀᴛᴇᴅ!** 🎧\n\n"
            f"✧ **Lɪsᴛᴇɴ ᴛᴏ ᴛʜᴇ Vᴏɪᴄᴇ Cʜᴀᴛ!**\n"
            f"✧ **Yᴏᴜ ʜᴀᴠᴇ 30 sᴇᴄᴏɴᴅs ᴛᴏ ɢᴜᴇss ᴛʜᴇ sᴏɴɢ ɴᴀᴍᴇ.**\n\n"
            f"*(Tʏᴘᴇ ʏᴏᴜʀ ᴀɴsᴡᴇʀ ɪɴ ᴛʜᴇ ᴄʜᴀᴛ)*"
        )

        # 30-Second Timer
        await asyncio.sleep(30)

        # Check if the quiz is still active (meaning no one guessed it)
        if chat_id in _active_quizzes:
            quiz_data = _active_quizzes.pop(chat_id)
            await sm.stop(chat_id, client)
            await client.send_message(
                chat_id,
                f"⏰ **Tɪᴍᴇ's ᴜᴘ!**\n\n"
                f"✧ Nᴏ ᴏɴᴇ ɢᴜᴇssᴇᴅ ɪᴛ ʀɪɢʜᴛ.\n"
                f"✧ Tʜᴇ ᴄᴏʀʀᴇᴄᴛ ᴀɴsᴡᴇʀ ᴡᴀs: **{quiz_data['correct_title']}**"
            )

    # Listen to all text messages in the group to catch the answer
    @app.on_message(filters.text & filters.group, group=1)
    async def catch_quiz_answer(client: Client, message: Message):
        chat_id = message.chat.id
        
        if chat_id not in _active_quizzes:
            return

        user_answer = clean_string(message.text)
        quiz_data = _active_quizzes[chat_id]

        # Check if the user's answer matches any of the allowed answers
        for correct_answer in quiz_data["answers"]:
            if correct_answer in user_answer or user_answer in correct_answer:
                # WINNER FOUND!
                _active_quizzes.pop(chat_id)  # Remove active quiz
                await sm.stop(chat_id, client) # Stop the music
                
                # Update Score in Database (Bonus Feature)
                try:
                    from database import get_db
                    await get_db().bot_users.update_one(
                        {"user_id": message.from_user.id},
                        {"$inc": {"quiz_score": 10}}, 
                        upsert=True
                    )
                except Exception:
                    pass

                await message.reply(
                    f"🎉 **Wᴇ ʜᴀᴠᴇ ᴀ ᴡɪɴɴᴇʀ!** 🎉\n\n"
                    f"👤 **{message.from_user.first_name}** ɢᴜᴇssᴇᴅ ɪᴛ ʀɪɢʜᴛ!\n"
                    f"✧ **Sᴏɴɢ :** {quiz_data['correct_title']}\n"
                    f"✧ **Rᴇᴡᴀʀᴅ :** `+10 DJ Pᴏɪɴᴛs` ᴀᴅᴅᴇᴅ!",
                    quote=True
                )
                break
