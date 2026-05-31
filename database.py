import motor.motor_asyncio
import config

client = None
db = None

async def init():
    global client, db
    if not config.MONGO_DB_URI:
        print("⚠️ WARNING: MONGO_DB_URI is not set in config!")
        return
    client = motor.motor_asyncio.AsyncIOMotorClient(config.MONGO_DB_URI)
    db = client.jattmusicbot  # Database Name
    print("✅ Database initialized successfully!")

def get_db():
    return db

# ─── User & Chat Tracking ─────────────────────────────────────────────────────

async def upsert_user(user_id: int, name: str):
    if db is not None:
        await db.users.update_one({"user_id": user_id}, {"$set": {"name": name}}, upsert=True)

async def upsert_chat(chat_id: int, title: str):
    if db is not None:
        await db.chats.update_one({"chat_id": chat_id}, {"$set": {"title": title}}, upsert=True)

async def get_all_users():
    if db is not None:
        return await db.users.find({}).to_list(length=None)
    return []

async def get_all_chats():
    if db is not None:
        return await db.chats.find({}).to_list(length=None)
    return []

# ─── Settings ─────────────────────────────────────────────────────────────────

async def get_setting(chat_id: int, setting: str):
    if db is None: return None
    doc = await db.settings.find_one({"chat_id": chat_id}) or {}
    defaults = {
        "loop_mode": "off",
        "vc247": False,
        "admin_only": False,
        "log_channel": 0,
        "welcome": "Welcome {name} to {group}!",
        "prefix": "/",
        "quality": "high"
    }
    return doc.get(setting, defaults.get(setting))

async def set_setting(chat_id: int, setting: str, value):
    if db is not None:
        await db.settings.update_one({"chat_id": chat_id}, {"$set": {setting: value}}, upsert=True)

# ─── Queue System ─────────────────────────────────────────────────────────────

async def add_to_queue(chat_id: int, track: dict):
    if db is None: return 1
    result = await db.queue.find_one_and_update(
        {"chat_id": chat_id},
        {"$push": {"tracks": track}},
        upsert=True,
        return_document=True
    )
    return len(result.get("tracks", []))

async def get_queue(chat_id: int):
    if db is None: return []
    doc = await db.queue.find_one({"chat_id": chat_id})
    return doc.get("tracks", []) if doc else []

async def remove_from_queue(chat_id: int, count: int):
    if db is None: return
    doc = await db.queue.find_one({"chat_id": chat_id})
    if doc and doc.get("tracks"):
        new_tracks = doc["tracks"][count:]
        await db.queue.update_one({"chat_id": chat_id}, {"$set": {"tracks": new_tracks}})

async def clear_queue(chat_id: int):
    if db is not None:
        await db.queue.update_one({"chat_id": chat_id}, {"$set": {"tracks": []}}, upsert=True)

async def shuffle_queue(chat_id: int):
    if db is None: return
    import random
    doc = await db.queue.find_one({"chat_id": chat_id})
    if doc and doc.get("tracks"):
        tracks = doc["tracks"]
        if len(tracks) > 1:
            first = tracks[0]
            rest = tracks[1:]
            random.shuffle(rest)
            await db.queue.update_one({"chat_id": chat_id}, {"$set": {"tracks": [first] + rest}})

# ─── Play History ─────────────────────────────────────────────────────────────

async def add_to_history(chat_id: int, track: dict):
    if db is not None:
        await db.history.update_one(
            {"chat_id": chat_id},
            {"$push": {"tracks": {"$each": [track], "$slice": -10}}},
            upsert=True
        )

async def get_history(chat_id: int):
    if db is None: return []
    doc = await db.history.find_one({"chat_id": chat_id})
    return doc.get("tracks", []) if doc else []

# ─── Roles & Chat Bans ────────────────────────────────────────────────────────

async def add_dj(chat_id: int, user_id: int):
    if db is not None: await db.djs.update_one({"chat_id": chat_id}, {"$addToSet": {"users": user_id}}, upsert=True)

async def remove_dj(chat_id: int, user_id: int):
    if db is not None: await db.djs.update_one({"chat_id": chat_id}, {"$pull": {"users": user_id}}, upsert=True)

async def is_dj(chat_id: int, user_id: int):
    if db is None: return False
    doc = await db.djs.find_one({"chat_id": chat_id, "users": user_id})
    return bool(doc)

async def ban_user_in_chat(chat_id: int, user_id: int):
    if db is not None: await db.chat_bans.update_one({"chat_id": chat_id}, {"$addToSet": {"banned": user_id}}, upsert=True)

async def unban_user_in_chat(chat_id: int, user_id: int):
    if db is not None: await db.chat_bans.update_one({"chat_id": chat_id}, {"$pull": {"banned": user_id}}, upsert=True)

async def is_banned_in_chat(chat_id: int, user_id: int):
    if db is None: return False
    doc = await db.chat_bans.find_one({"chat_id": chat_id, "banned": user_id})
    return bool(doc)

# ─── Global Bans & Mutes ──────────────────────────────────────────────────────

async def add_gban(user_id: int, reason: str):
    if db is not None: await db.gbans.update_one({"user_id": user_id}, {"$set": {"reason": reason}}, upsert=True)

async def remove_gban(user_id: int):
    if db is None: return False
    res = await db.gbans.delete_one({"user_id": user_id})
    return res.deleted_count > 0

async def get_gban_list():
    if db is None: return []
    return await db.gbans.find({}).to_list(length=None)

async def add_gmute(user_id: int, reason: str):
    if db is not None: await db.gmutes.update_one({"user_id": user_id}, {"$set": {"reason": reason}}, upsert=True)

async def remove_gmute(user_id: int):
    if db is None: return False
    res = await db.gmutes.delete_one({"user_id": user_id})
    return res.deleted_count > 0

async def get_gmute_list():
    if db is None: return []
    return await db.gmutes.find({}).to_list(length=None)

async def is_gmuted(user_id: int):
    if db is None: return False
    doc = await db.gmutes.find_one({"user_id": user_id})
    return bool(doc)

# ─── Statistics & Leaderboards ────────────────────────────────────────────────

async def record_play(chat_id: int, requester_id: int, title: str):
    if db is not None:
        await db.plays.insert_one({"chat_id": chat_id, "requester_id": requester_id, "title": title})

async def global_stats():
    if db is None: return {"total_users": 0, "total_chats": 0, "total_plays": 0}
    users = await db.users.count_documents({})
    chats = await db.chats.count_documents({})
    plays = await db.plays.count_documents({})
    return {"total_users": users, "total_chats": chats, "total_plays": plays}

async def top_plays(chat_id: int, limit: int = 5):
    if db is None: return []
    pipe = [{"$match": {"chat_id": chat_id}}, {"$group": {"_id": "$title", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": limit}]
    return await db.plays.aggregate(pipe).to_list(length=limit)

async def top_djs(chat_id: int, limit: int = 5):
    if db is None: return []
    pipe = [{"$match": {"chat_id": chat_id}}, {"$group": {"_id": "$requester_id", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": limit}]
    return await db.plays.aggregate(pipe).to_list(length=limit)

async def group_stats(chat_id: int):
    if db is None: return {"total": 0, "unique_users": 0, "unique_songs": 0}
    plays = await db.plays.count_documents({"chat_id": chat_id})
    users = len(await db.plays.distinct("requester_id", {"chat_id": chat_id}))
    songs = len(await db.plays.distinct("title", {"chat_id": chat_id}))
    return {"total": plays, "unique_users": users, "unique_songs": songs}

async def weekly_top(chat_id: int, limit: int = 5):
    return await top_plays(chat_id, limit)

async def leaderboard(chat_id: int, limit: int = 10):
    return await top_djs(chat_id, limit)
        
