from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.types import Message

import database as db
from plugins.utils import group_admin_only, maintenance_check

def register(app: Client) -> None:

    @app.on_message(filters.command("topplays") & filters.group)
    @maintenance_check
    @group_admin_only
    async def topplays_cmd(client: Client, message: Message):
        results = await db.top_plays(message.chat.id, limit=5)
        if not results:
            await message.reply("📝 **Nᴏ ᴘʟᴀʏ ᴅᴀᴛᴀ ʏᴇᴛ.**")
            return
        lines = [f"`{i + 1}.` **{r['_id'][:40]}** `({r['count']} ᴘʟᴀʏs)`" for i, r in enumerate(results)]
        await message.reply("⏤͟͟͞͞★ **Tᴏᴘ 5 Mᴏsᴛ Pʟᴀʏᴇᴅ Sᴏɴɢs**\n\n" + "\n".join(lines))

    @app.on_message(filters.command("topdjs") & filters.group)
    @maintenance_check
    @group_admin_only
    async def topdjs_cmd(client: Client, message: Message):
        results = await db.top_djs(message.chat.id, limit=5)
        if not results:
            await message.reply("📝 **Nᴏ ᴅᴀᴛᴀ ʏᴇᴛ.**")
            return
        lines = []
        for i, r in enumerate(results):
            try:
                user = await client.get_users(r["_id"])
                name = user.first_name
            except Exception:
                name = f"User {r['_id']}"
            lines.append(f"`{i + 1}.` 👤 **{name}** `({r['count']} sᴏɴɢs)`")
        await message.reply("⏤͟͟͞͞★ **Tᴏᴘ 5 Sᴏɴɢ Rᴇǫᴜᴇsᴛᴇʀs (DJs)**\n\n" + "\n".join(lines))

    @app.on_message(filters.command("groupstats") & filters.group)
    @maintenance_check
    @group_admin_only
    async def groupstats_cmd(client: Client, message: Message):
        stats = await db.group_stats(message.chat.id)
        text = (
            f"⏤͟͟͞͞★ **Gʀᴏᴜᴘ Mᴜsɪᴄ Sᴛᴀᴛɪsᴛɪᴄs**\n\n"
            f"✧ **Tᴏᴛᴀʟ Pʟᴀʏs:** `{stats['total']}`\n"
            f"✧ **Uɴɪǫᴜᴇ Usᴇʀs:** `{stats['unique_users']}`\n"
            f"✧ **Uɴɪǫᴜᴇ Sᴏɴɢs:** `{stats['unique_songs']}`"
        )
        await message.reply(text)

    @app.on_message(filters.command("weekly") & filters.group)
    @maintenance_check
    @group_admin_only
    async def weekly_cmd(client: Client, message: Message):
        results = await db.weekly_top(message.chat.id, limit=5)
        if not results:
            await message.reply("📝 **Nᴏ ᴅᴀᴛᴀ ғʀᴏᴍ ᴛʜɪs ᴡᴇᴇᴋ.**")
            return
        lines = [f"`{i + 1}.` **{r['_id'][:40]}** `({r['count']} ᴘʟᴀʏs)`" for i, r in enumerate(results)]
        await message.reply("⏤͟͟͞͞★ **Tᴏᴘ 5 Sᴏɴɢs (Tʜɪs Wᴇᴇᴋ)**\n\n" + "\n".join(lines))

    @app.on_message(filters.command("leaderboard") & filters.group)
    @maintenance_check
    @group_admin_only
    async def leaderboard_cmd(client: Client, message: Message):
        results = await db.leaderboard(message.chat.id, limit=10)
        if not results:
            await message.reply("📝 **Nᴏ ᴅᴀᴛᴀ ʏᴇᴛ.**")
            return
        lines = []
        medals = ["🥇", "🥈", "🥉"]
        for i, r in enumerate(results):
            try:
                user = await client.get_users(r["_id"])
                name = user.first_name
            except Exception:
                name = f"User {r['_id']}"
            prefix = medals[i] if i < 3 else f"`{i + 1}.`"
            lines.append(f"{prefix} **{name}** `({r['count']} sᴏɴɢs)`")
        await message.reply("⏤͟͟͞͞★ **Gʀᴏᴜᴘ Lᴇᴀᴅᴇʀʙᴏᴀʀᴅ (Tᴏᴘ DJs)**\n\n" + "\n".join(lines))
            
