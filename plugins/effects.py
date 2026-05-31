from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.types import Message

from core import stream as sm
from plugins.utils import is_dj_or_admin, maintenance_check

def register(app: Client) -> None:

    @app.on_message(filters.command("speed") & filters.group)
    @maintenance_check
    async def speed_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.fromuser.id if message.from_user else 0):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("🔇 Nᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ.")
            return
        args = message.command[1:]
        if not args:
            await message.reply("✧ **Usaɢᴇ:** `/speed [0.5 - 2.0]` or `/speed reset`")
            return
        arg = args[0].strip().lower()
        if arg == "reset":
            await sm.set_speed(message.chat.id, 1.0)
            await message.reply("⏤͟͟͞͞★ **Aᴜᴅɪᴏ Eғғᴇᴄᴛs**\n✧ **Sᴘᴇᴇᴅ :** `Nᴏʀᴍᴀʟ (1.0x)`")
            return
        try:
            val = float(arg)
        except ValueError:
            await message.reply("❌ Invalid value. Use a number between 0.5 and 2.0.")
            return
        if not 0.5 <= val <= 2.0:
            await message.reply("⚠️ Speed must be between 0.5 and 2.0.")
            return
        await sm.set_speed(message.chat.id, val)
        await message.reply(f"⏤͟͟͞͞★ **Aᴜᴅɪᴏ Eғғᴇᴄᴛs**\n✧ **Sᴘᴇᴇᴅ :** `{val:.2f}x`")

    @app.on_message(filters.command("bass") & filters.group)
    @maintenance_check
    async def bass_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id if message.from_user else 0):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("🔇 Nᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ.")
            return
        args = message.command[1:]
        if not args:
            await message.reply("✧ **Usaɢᴇ:** `/bass [1 - 10]` or `/bass reset`")
            return
        arg = args[0].strip().lower()
        if arg == "reset":
            await sm.set_bass(message.chat.id, 0)
            await message.reply("⏤͟͟͞͞★ **Aᴜᴅɪᴏ Eғғᴇᴄᴛs**\n✧ **Bᴀss Bᴏᴏsᴛ :** `Oғғ`")
            return
        try:
            val = int(arg)
        except ValueError:
            await message.reply("❌ Invalid value. Use a number between 1 and 10.")
            return
        if not 1 <= val <= 10:
            await message.reply("⚠️ Bass must be between 1 and 10.")
            return
        await sm.set_bass(message.chat.id, val)
        await message.reply(f"⏤͟͟͞͞★ **Aᴜᴅɪᴏ Eғғᴇᴄᴛs**\n✧ **Bᴀss Bᴏᴏsᴛ :** `Lᴇᴠᴇʟ {val}`")

    @app.on_message(filters.command("pitch") & filters.group)
    @maintenance_check
    async def pitch_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id if message.from_user else 0):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("🔇 Nᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ.")
            return
        args = message.command[1:]
        if not args:
            await message.reply("✧ **Usaɢᴇ:** `/pitch [0.5 - 2.0]`")
            return
        try:
            val = float(args[0].strip())
        except ValueError:
            await message.reply("❌ Invalid value.")
            return
        if not 0.5 <= val <= 2.0:
            await message.reply("⚠️ Pitch must be between 0.5 and 2.0.")
            return
        await sm.set_pitch(message.chat.id, val)
        await message.reply(f"⏤͟͟͞͞★ **Aᴜᴅɪᴏ Eғғᴇᴄᴛs**\n✧ **Pɪᴛᴄʜ :** `{val:.2f}`")

    @app.on_message(filters.command("reverb") & filters.group)
    @maintenance_check
    async def reverb_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id if message.from_user else 0):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("🔇 Nᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ.")
            return
        enabled = await sm.toggle_reverb(message.chat.id)
        state = "Eɴᴀʙʟᴇᴅ" if enabled else "Dɪsᴀʙʟᴇᴅ"
        await message.reply(f"⏤͟͟͞͞★ **Aᴜᴅɪᴏ Eғғᴇᴄᴛs**\n✧ **Rᴇᴠᴇʀʙ :** `{state}`")

    @app.on_message(filters.command("nightcore") & filters.group)
    @maintenance_check
    async def nightcore_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id if message.from_user else 0):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("🔇 Nᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ.")
            return
        enabled = await sm.toggle_nightcore(message.chat.id)
        state = "Eɴᴀʙʟᴇᴅ" if enabled else "Dɪsᴀʙʟᴇᴅ"
        await message.reply(f"⏤͟͟͞͞★ **Aᴜᴅɪᴏ Eғғᴇᴄᴛs**\n✧ **Nɪɢʜᴛᴄᴏʀᴇ :** `{state}`")

    @app.on_message(filters.command("normalise") & filters.group)
    @maintenance_check
    async def normalise_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id if message.from_user else 0):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("🔇 Nᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ.")
            return
        await sm.normalise(message.chat.id)
        await message.reply("✅ **Aʟʟ ᴀᴜᴅɪᴏ ᴇғғᴇᴄᴛs ᴄʟᴇᴀʀᴇᴅ.**\n✧ Volume reset to 100%.")

    @app.on_message(filters.command("volume") & filters.group)
    @maintenance_check
    async def volume_cmd(client: Client, message: Message):
        if not await is_dj_or_admin(client, message.chat.id, message.from_user.id if message.from_user else 0):
            await message.reply("⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ:** DJs/Admins only.")
            return
        if not sm.get_active(message.chat.id):
            await message.reply("🔇 Nᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ.")
            return
        args = message.command[1:]
        if not args:
            active = sm.get_active(message.chat.id)
            vol = active.volume if active else 100
            await message.reply(f"✧ **Cᴜʀʀᴇɴᴛ Vᴏʟᴜᴍᴇ :** `{vol}%`\n✧ **Usaɢᴇ:** `/volume [0 - 200]`")
            return
        try:
            val = int(args[0].strip())
        except ValueError:
            await message.reply("❌ Invalid value. Use a number between 0 and 200.")
            return
        if not 0 <= val <= 200:
            await message.reply("⚠️ Volume must be between 0 and 200.")
            return
        await sm.set_volume(message.chat.id, val)
        await message.reply(f"⏤͟͟͞͞★ **Aᴜᴅɪᴏ Eғғᴇᴄᴛs**\n✧ **Vᴏʟᴜᴍᴇ :** `{val}%`")
            
