import aiosqlite
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")


async def init_db():
    """Initialize the database with all required tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # API keys table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                api_key TEXT UNIQUE NOT NULL,
                name TEXT DEFAULT 'Default',
                is_active INTEGER DEFAULT 1,
                requests_today INTEGER DEFAULT 0,
                daily_limit INTEGER DEFAULT 100,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_used TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        # Request logs table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS request_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                api_key_id INTEGER,
                bot_name TEXT NOT NULL,
                input_data TEXT NOT NULL,
                response_data TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
            )
        """)
        # Response cache
        await db.execute("""
            CREATE TABLE IF NOT EXISTS response_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_name TEXT NOT NULL,
                input_data TEXT NOT NULL,
                response_data TEXT NOT NULL,
                cached_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(bot_name, input_data)
            )
        """)
        await db.commit()


# ──────────────── User Operations ────────────────

async def create_user(username: str, password_hash: str, role: str = "user", status: str = "pending"):
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO users (username, password_hash, role, status) VALUES (?, ?, ?, ?)",
                (username, password_hash, role, status)
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def get_user_by_username(username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE username = ?", (username,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_user_by_id(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT id, username, role, status, created_at, updated_at FROM users ORDER BY created_at DESC") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def update_user_status(user_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET status = ?, updated_at = ? WHERE id = ?",
            (status, datetime.utcnow().isoformat(), user_id)
        )
        await db.commit()


async def delete_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM api_keys WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        await db.commit()


# ──────────────── API Key Operations ────────────────

async def create_api_key(user_id: int, api_key: str, name: str = "Default"):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO api_keys (user_id, api_key, name) VALUES (?, ?, ?)",
            (user_id, api_key, name)
        )
        await db.commit()


async def get_api_key(api_key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT ak.*, u.status as user_status, u.username FROM api_keys ak JOIN users u ON ak.user_id = u.id WHERE ak.api_key = ?",
            (api_key,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_user_api_keys(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM api_keys WHERE user_id = ?", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def increment_api_key_usage(api_key_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE api_keys SET requests_today = requests_today + 1, last_used = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), api_key_id)
        )
        await db.commit()


async def reset_daily_limits():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE api_keys SET requests_today = 0")
        await db.commit()


# ──────────────── Request Log Operations ────────────────

async def log_request(user_id: int, api_key_id: int, bot_name: str, input_data: str, response_data: str = None, status: str = "success"):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO request_logs (user_id, api_key_id, bot_name, input_data, response_data, status) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, api_key_id, bot_name, input_data, response_data, status)
        )
        await db.commit()


async def get_request_logs(user_id: int = None, limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if user_id:
            query = "SELECT rl.*, u.username FROM request_logs rl JOIN users u ON rl.user_id = u.id WHERE rl.user_id = ? ORDER BY rl.created_at DESC LIMIT ?"
            params = (user_id, limit)
        else:
            query = "SELECT rl.*, u.username FROM request_logs rl JOIN users u ON rl.user_id = u.id ORDER BY rl.created_at DESC LIMIT ?"
            params = (limit,)
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        stats = {}
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            stats["total_users"] = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE status = 'approved'") as c:
            stats["approved_users"] = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE status = 'pending'") as c:
            stats["pending_users"] = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE status = 'banned'") as c:
            stats["banned_users"] = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM request_logs") as c:
            stats["total_requests"] = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM request_logs WHERE DATE(created_at) = DATE('now')") as c:
            stats["today_requests"] = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM api_keys WHERE is_active = 1") as c:
            stats["active_api_keys"] = (await c.fetchone())[0]
        return stats


# ──────────────── Cache Operations ────────────────

async def get_cached_response(bot_name: str, input_data: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM response_cache WHERE bot_name = ? AND input_data = ?",
            (bot_name, input_data)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def cache_response(bot_name: str, input_data: str, response_data: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO response_cache (bot_name, input_data, response_data, cached_at) VALUES (?, ?, ?, ?)",
            (bot_name, input_data, response_data, datetime.utcnow().isoformat())
        )
        await db.commit()
