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
            await message.reply("No play data yet.")
            return
        lines = [f"{i + 1}. <b>{r['_id']}</b> — {r['count']} plays" for i, r in enumerate(results)]
        await message.reply("<b>Top 5 Most Played Songs</b>\n\n" + "\n".join(lines))

    @app.on_message(filters.command("topdjs") & filters.group)
    @maintenance_check
    @group_admin_only
    async def topdjs_cmd(client: Client, message: Message):
        results = await db.top_djs(message.chat.id, limit=5)
        if not results:
            await message.reply("No data yet.")
            return
        lines = []
        for i, r in enumerate(results):
            try:
                user = await client.get_users(r["_id"])
                name = user.first_name
            except Exception:
                name = f"User {r['_id']}"
            lines.append(f"{i + 1}. <b>{name}</b> — {r['count']} songs")
        await message.reply("<b>Top 5 Song Requesters (DJs)</b>\n\n" + "\n".join(lines))

    @app.on_message(filters.command("groupstats") & filters.group)
    @maintenance_check
    @group_admin_only
    async def groupstats_cmd(client: Client, message: Message):
        stats = await db.group_stats(message.chat.id)
        text = (
            f"<b>Group Music Statistics</b>\n\n"
            f"<b>Total Plays:</b> {stats['total']}\n"
            f"<b>Unique Users:</b> {stats['unique_users']}\n"
            f"<b>Unique Songs:</b> {stats['unique_songs']}"
        )
        await message.reply(text)

    @app.on_message(filters.command("weekly") & filters.group)
    @maintenance_check
    @group_admin_only
    async def weekly_cmd(client: Client, message: Message):
        results = await db.weekly_top(message.chat.id, limit=5)
        if not results:
            await message.reply("No data from this week.")
            return
        lines = [f"{i + 1}. <b>{r['_id']}</b> — {r['count']} plays" for i, r in enumerate(results)]
        await message.reply("<b>Top 5 Songs This Week</b>\n\n" + "\n".join(lines))

    @app.on_message(filters.command("leaderboard") & filters.group)
    @maintenance_check
    @group_admin_only
    async def leaderboard_cmd(client: Client, message: Message):
        results = await db.leaderboard(message.chat.id, limit=10)
        if not results:
            await message.reply("No data yet.")
            return
        lines = []
        medals = ["", "", ""]
        for i, r in enumerate(results):
            try:
                user = await client.get_users(r["_id"])
                name = user.first_name
            except Exception:
                name = f"User {r['_id']}"
            prefix = medals[i] if i < 3 else f"{i + 1}."
            lines.append(f"{prefix} <b>{name}</b> — {r['count']} songs")
        await message.reply("<b>Leaderboard — Top Requesters</b>\n\n" + "\n".join(lines))
