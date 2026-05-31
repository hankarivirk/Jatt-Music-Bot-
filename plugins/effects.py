from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.types import Message

from core import stream as sm
from plugins.utils import is_dj_or_admin, maintenance_check


def register(app: Client) -> None:

    @app.on_message(filters.command("speed") & filters.group)
    @maintenance_check
    async def speed_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can change speed.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("Nothing is playing.")
            return
        args = message.command[1:]
        if not args:
            await message.reply("Usage: /speed <0.5–2.0> or /speed reset")
            return
        arg = args[0].strip().lower()
        if arg == "reset":
            await sm.set_speed(message.chat.id, 1.0)
            await message.reply("Speed reset to 1.0x.")
            return
        try:
            val = float(arg)
        except ValueError:
            await message.reply("Invalid value. Use a number between 0.5 and 2.0.")
            return
        if not 0.5 <= val <= 2.0:
            await message.reply("Speed must be between 0.5 and 2.0.")
            return
        await sm.set_speed(message.chat.id, val)
        await message.reply(f"Speed set to <b>{val:.2f}x</b>.")

    @app.on_message(filters.command("bass") & filters.group)
    @maintenance_check
    async def bass_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can change bass.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("Nothing is playing.")
            return
        args = message.command[1:]
        if not args:
            await message.reply("Usage: /bass <1–10> or /bass reset")
            return
        arg = args[0].strip().lower()
        if arg == "reset":
            await sm.set_bass(message.chat.id, 0)
            await message.reply("Bass reset.")
            return
        try:
            val = int(arg)
        except ValueError:
            await message.reply("Invalid value. Use a number between 1 and 10.")
            return
        if not 1 <= val <= 10:
            await message.reply("Bass must be between 1 and 10.")
            return
        await sm.set_bass(message.chat.id, val)
        await message.reply(f"Bass boost set to <b>{val}</b>.")

    @app.on_message(filters.command("pitch") & filters.group)
    @maintenance_check
    async def pitch_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can change pitch.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("Nothing is playing.")
            return
        args = message.command[1:]
        if not args:
            await message.reply("Usage: /pitch <0.5–2.0>")
            return
        try:
            val = float(args[0].strip())
        except ValueError:
            await message.reply("Invalid value.")
            return
        if not 0.5 <= val <= 2.0:
            await message.reply("Pitch must be between 0.5 and 2.0.")
            return
        await sm.set_pitch(message.chat.id, val)
        await message.reply(f"Pitch set to <b>{val:.2f}</b>.")

    @app.on_message(filters.command("reverb") & filters.group)
    @maintenance_check
    async def reverb_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can use reverb.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("Nothing is playing.")
            return
        enabled = await sm.toggle_reverb(message.chat.id)
        state = "enabled" if enabled else "disabled"
        await message.reply(f"Reverb <b>{state}</b>.")

    @app.on_message(filters.command("nightcore") & filters.group)
    @maintenance_check
    async def nightcore_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can use nightcore.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("Nothing is playing.")
            return
        enabled = await sm.toggle_nightcore(message.chat.id)
        state = "enabled" if enabled else "disabled"
        await message.reply(f"Nightcore effect <b>{state}</b>.")

    @app.on_message(filters.command("normalise") & filters.group)
    @maintenance_check
    async def normalise_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can normalise audio.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("Nothing is playing.")
            return
        await sm.normalise(message.chat.id)
        await message.reply("All audio effects cleared. Volume reset to 100%.")

    @app.on_message(filters.command("volume") & filters.group)
    @maintenance_check
    async def volume_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id):
            await message.reply("Only DJs and admins can set volume.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("Nothing is playing.")
            return
        args = message.command[1:]
        if not args:
            active = sm.get_active(message.chat.id)
            vol = active.volume if active else 100
            await message.reply(f"Current volume: <b>{vol}%</b>\nUsage: /volume <0–200>")
            return
        try:
            val = int(args[0].strip())
        except ValueError:
            await message.reply("Invalid value. Use a number between 0 and 200.")
            return
        if not 0 <= val <= 200:
            await message.reply("Volume must be between 0 and 200.")
            return
        await sm.set_volume(message.chat.id, val)
        await message.reply(f"Volume set to <b>{val}%</b>.")
