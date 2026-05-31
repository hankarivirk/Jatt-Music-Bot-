from __future__ import annotations

import time
from typing import Any, Optional

import motor.motor_asyncio
from pymongo import ASCENDING, DESCENDING, IndexModel

from config import MONGO_URI, MAX_HISTORY

_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
_db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None


def get_db() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialised — call init_db() first")
    return _db


async def init_db() -> None:
    global _client, _db
    _client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    _db = _client["jatt_music_bot"]
    await _ensure_indexes()


async def _ensure_indexes() -> None:
    db = get_db()
    await db.play_stats.create_indexes([
        IndexModel([("timestamp", ASCENDING)], expireAfterSeconds=30 * 24 * 3600),
        IndexModel([("chat_id", ASCENDING)]),
        IndexModel([("user_id", ASCENDING)]),
    ])
    await db.queue.create_indexes([IndexModel([("chat_id", ASCENDING)])])
    await db.history.create_indexes([IndexModel([("chat_id", ASCENDING)])])
    await db.global_bans.create_indexes([IndexModel([("user_id", ASCENDING)], unique=True)])
    await db.global_mutes.create_indexes([IndexModel([("user_id", ASCENDING)], unique=True)])


# ─── Queue ────────────────────────────────────────────────────────────────────

async def get_queue(chat_id: int) -> list[dict]:
    db = get_db()
    doc = await db.queue.find_one({"chat_id": chat_id})
    return doc["tracks"] if doc else []


async def add_to_queue(chat_id: int, track: dict) -> int:
    db = get_db()
    doc = await db.queue.find_one({"chat_id": chat_id})
    tracks = doc["tracks"] if doc else []
    track["position"] = len(tracks) + 1
    tracks.append(track)
    await db.queue.update_one(
        {"chat_id": chat_id}, {"$set": {"tracks": tracks}}, upsert=True
    )
    return track["position"]


async def remove_from_queue(chat_id: int, position: int) -> bool:
    db = get_db()
    doc = await db.queue.find_one({"chat_id": chat_id})
    if not doc:
        return False
    tracks = doc["tracks"]
    if position < 1 or position > len(tracks):
        return False
    tracks.pop(position - 1)
    for i, t in enumerate(tracks):
        t["position"] = i + 1
    await db.queue.update_one({"chat_id": chat_id}, {"$set": {"tracks": tracks}})
    return True


async def move_in_queue(chat_id: int, from_pos: int, to_pos: int) -> bool:
    db = get_db()
    doc = await db.queue.find_one({"chat_id": chat_id})
    if not doc:
        return False
    tracks = doc["tracks"]
    n = len(tracks)
    if not (1 <= from_pos <= n and 1 <= to_pos <= n):
        return False
    track = tracks.pop(from_pos - 1)
    tracks.insert(to_pos - 1, track)
    for i, t in enumerate(tracks):
        t["position"] = i + 1
    await db.queue.update_one({"chat_id": chat_id}, {"$set": {"tracks": tracks}})
    return True


async def clear_queue(chat_id: int) -> None:
    db = get_db()
    await db.queue.delete_one({"chat_id": chat_id})


async def shuffle_queue(chat_id: int) -> None:
    import random
    db = get_db()
    doc = await db.queue.find_one({"chat_id": chat_id})
    if not doc or len(doc["tracks"]) < 2:
        return
    first = doc["tracks"][0]
    rest = doc["tracks"][1:]
    random.shuffle(rest)
    tracks = [first] + rest
    for i, t in enumerate(tracks):
        t["position"] = i + 1
    await db.queue.update_one({"chat_id": chat_id}, {"$set": {"tracks": tracks}})


# ─── History ──────────────────────────────────────────────────────────────────

async def add_to_history(chat_id: int, track: dict) -> None:
    db = get_db()
    doc = await db.history.find_one({"chat_id": chat_id})
    tracks = doc["tracks"] if doc else []
    tracks.insert(0, track)
    tracks = tracks[:MAX_HISTORY]
    await db.history.update_one(
        {"chat_id": chat_id}, {"$set": {"tracks": tracks}}, upsert=True
    )


async def get_history(chat_id: int, limit: int = 10) -> list[dict]:
    db = get_db()
    doc = await db.history.find_one({"chat_id": chat_id})
    return (doc["tracks"] if doc else [])[:limit]


# ─── DJ Users ─────────────────────────────────────────────────────────────────

async def add_dj(chat_id: int, user_id: int) -> None:
    db = get_db()
    await db.dj_users.update_one(
        {"chat_id": chat_id},
        {"$addToSet": {"users": user_id}},
        upsert=True,
    )


async def remove_dj(chat_id: int, user_id: int) -> None:
    db = get_db()
    await db.dj_users.update_one({"chat_id": chat_id}, {"$pull": {"users": user_id}})


async def is_dj(chat_id: int, user_id: int) -> bool:
    db = get_db()
    doc = await db.dj_users.find_one({"chat_id": chat_id})
    return user_id in (doc["users"] if doc else [])


# ─── Chat Settings ────────────────────────────────────────────────────────────

_settings_defaults: dict[str, Any] = {
    "admin_only": False,
    "loop_mode": "off",
    "prefix": "/",
    "quality": "high",
    "vc247": False,
    "welcome": None,
    "log_channel": None,
}


async def get_setting(chat_id: int, key: str) -> Any:
    db = get_db()
    doc = await db.chat_settings.find_one({"chat_id": chat_id})
    if doc:
        return doc.get(key, _settings_defaults.get(key))
    return _settings_defaults.get(key)


async def set_setting(chat_id: int, key: str, value: Any) -> None:
    db = get_db()
    await db.chat_settings.update_one(
        {"chat_id": chat_id}, {"$set": {key: value}}, upsert=True
    )


async def get_all_settings(chat_id: int) -> dict:
    db = get_db()
    doc = await db.chat_settings.find_one({"chat_id": chat_id})
    if not doc:
        return dict(_settings_defaults)
    result = dict(_settings_defaults)
    result.update({k: v for k, v in doc.items() if k != "_id"})
    return result


# ─── Bot Users ────────────────────────────────────────────────────────────────

async def upsert_user(user_id: int, name: str) -> None:
    db = get_db()
    await db.bot_users.update_one(
        {"user_id": user_id},
        {"$set": {"name": name}, "$setOnInsert": {"banned": False}},
        upsert=True,
    )


async def ban_user_in_chat(chat_id: int, user_id: int) -> None:
    db = get_db()
    await db.bot_users.update_one(
        {"user_id": user_id},
        {"$addToSet": {"chat_banned": chat_id}},
        upsert=True,
    )


async def unban_user_in_chat(chat_id: int, user_id: int) -> None:
    db = get_db()
    await db.bot_users.update_one(
        {"user_id": user_id}, {"$pull": {"chat_banned": chat_id}}
    )


async def is_banned_in_chat(chat_id: int, user_id: int) -> bool:
    db = get_db()
    doc = await db.bot_users.find_one({"user_id": user_id})
    return chat_id in (doc.get("chat_banned", []) if doc else [])


# ─── Bot Chats ────────────────────────────────────────────────────────────────

async def upsert_chat(chat_id: int, title: str) -> None:
    db = get_db()
    await db.bot_chats.update_one(
        {"chat_id": chat_id},
        {"$set": {"title": title, "active": True}},
        upsert=True,
    )


async def get_all_chats() -> list[dict]:
    db = get_db()
    return await db.bot_chats.find({"active": True}).to_list(None)


async def get_all_users() -> list[dict]:
    db = get_db()
    return await db.bot_users.find().to_list(None)


# ─── Play Stats ───────────────────────────────────────────────────────────────

async def record_play(chat_id: int, user_id: int, title: str) -> None:
    db = get_db()
    await db.play_stats.insert_one(
        {"chat_id": chat_id, "user_id": user_id, "title": title, "timestamp": time.time()}
    )


async def top_plays(chat_id: int, limit: int = 5) -> list[dict]:
    db = get_db()
    pipeline = [
        {"$match": {"chat_id": chat_id}},
        {"$group": {"_id": "$title", "count": {"$sum": 1}}},
        {"$sort": {"count": DESCENDING}},
        {"$limit": limit},
    ]
    return await db.play_stats.aggregate(pipeline).to_list(None)


async def top_djs(chat_id: int, limit: int = 5) -> list[dict]:
    db = get_db()
    pipeline = [
        {"$match": {"chat_id": chat_id}},
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": DESCENDING}},
        {"$limit": limit},
    ]
    return await db.play_stats.aggregate(pipeline).to_list(None)


async def weekly_top(chat_id: int, limit: int = 5) -> list[dict]:
    db = get_db()
    week_ago = time.time() - 7 * 24 * 3600
    pipeline = [
        {"$match": {"chat_id": chat_id, "timestamp": {"$gte": week_ago}}},
        {"$group": {"_id": "$title", "count": {"$sum": 1}}},
        {"$sort": {"count": DESCENDING}},
        {"$limit": limit},
    ]
    return await db.play_stats.aggregate(pipeline).to_list(None)


async def leaderboard(chat_id: int, limit: int = 10) -> list[dict]:
    db = get_db()
    pipeline = [
        {"$match": {"chat_id": chat_id}},
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": DESCENDING}},
        {"$limit": limit},
    ]
    return await db.play_stats.aggregate(pipeline).to_list(None)


async def user_songs(chat_id: int, user_id: int, limit: int = 10) -> list[dict]:
    db = get_db()
    pipeline = [
        {"$match": {"chat_id": chat_id, "user_id": user_id}},
        {"$group": {"_id": "$title", "count": {"$sum": 1}}},
        {"$sort": {"count": DESCENDING}},
        {"$limit": limit},
    ]
    return await db.play_stats.aggregate(pipeline).to_list(None)


async def group_stats(chat_id: int) -> dict:
    db = get_db()
    total = await db.play_stats.count_documents({"chat_id": chat_id})
    unique_users = len(await db.play_stats.distinct("user_id", {"chat_id": chat_id}))
    unique_songs = len(await db.play_stats.distinct("title", {"chat_id": chat_id}))
    return {"total": total, "unique_users": unique_users, "unique_songs": unique_songs}


async def global_stats() -> dict:
    db = get_db()
    total_plays = await db.play_stats.count_documents({})
    total_users = await db.bot_users.count_documents({})
    total_chats = await db.bot_chats.count_documents({"active": True})
    return {"total_plays": total_plays, "total_users": total_users, "total_chats": total_chats}


# ─── Global Bans ──────────────────────────────────────────────────────────────

async def add_gban(user_id: int, reason: str) -> None:
    db = get_db()
    await db.global_bans.update_one(
        {"user_id": user_id},
        {"$set": {"reason": reason, "date": time.time()}},
        upsert=True,
    )


async def remove_gban(user_id: int) -> bool:
    db = get_db()
    result = await db.global_bans.delete_one({"user_id": user_id})
    return result.deleted_count > 0


async def is_gbanned(user_id: int) -> bool:
    db = get_db()
    return bool(await db.global_bans.find_one({"user_id": user_id}))


async def get_gban(user_id: int) -> Optional[dict]:
    db = get_db()
    return await db.global_bans.find_one({"user_id": user_id})


async def get_gban_list() -> list[dict]:
    db = get_db()
    return await db.global_bans.find().to_list(None)


# ─── Global Mutes ─────────────────────────────────────────────────────────────

async def add_gmute(user_id: int, reason: str) -> None:
    db = get_db()
    await db.global_mutes.update_one(
        {"user_id": user_id},
        {"$set": {"reason": reason, "date": time.time()}},
        upsert=True,
    )


async def remove_gmute(user_id: int) -> bool:
    db = get_db()
    result = await db.global_mutes.delete_one({"user_id": user_id})
    return result.deleted_count > 0


async def is_gmuted(user_id: int) -> bool:
    db = get_db()
    return bool(await db.global_mutes.find_one({"user_id": user_id}))


async def get_gmute_list() -> list[dict]:
    db = get_db()
    return await db.global_mutes.find().to_list(None)
