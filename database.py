import os
import aiosqlite

from config import DATABASE_PATH


SCHEMA = """
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS users(
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT NOT NULL DEFAULT '',
    balance REAL NOT NULL DEFAULT 0,
    is_blocked INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS videos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    youtube_url TEXT NOT NULL,
    youtube_id TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    reward REAL NOT NULL CHECK(reward>0 AND reward<=1000),
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS completions(
    telegram_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(telegram_id, task_id),
    FOREIGN KEY(telegram_id) REFERENCES users(telegram_id),
    FOREIGN KEY(task_id) REFERENCES tasks(id)
);

CREATE TABLE IF NOT EXISTS transactions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    kind TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(telegram_id) REFERENCES users(telegram_id)
);

CREATE TABLE IF NOT EXISTS demo_tokens(
    token TEXT PRIMARY KEY,
    telegram_id INTEGER NOT NULL,
    expires_at TEXT NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(telegram_id) REFERENCES users(telegram_id)
);
"""


async def connect():
    os.makedirs(os.path.dirname(DATABASE_PATH) or ".", exist_ok=True)

    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row

    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    async with await connect() as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def ensure_user(user):
    async with await connect() as db:
        await db.execute(
            """
            INSERT INTO users(telegram_id, username, first_name)
            VALUES(?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                last_seen=CURRENT_TIMESTAMP
            """,
            (user.id, user.username, user.first_name or "")
        )
        await db.commit()


async def get_user(tg_id):
    async with await connect() as db:
        cur = await db.execute(
            "SELECT * FROM users WHERE telegram_id=?",
            (tg_id,)
        )
        return await cur.fetchone()


async def change_balance(tg_id, amount, kind, note):
    async with await connect() as db:
        await db.execute("BEGIN IMMEDIATE")

        cur = await db.execute(
            "SELECT balance FROM users WHERE telegram_id=?",
            (tg_id,)
        )
        row = await cur.fetchone()

        if not row:
            await db.rollback()
            raise ValueError("Foydalanuvchi topilmadi")

        new_balance = round(
            float(row["balance"]) + float(amount),
            4
        )

        if new_balance < 0:
            await db.rollback()
            raise ValueError("Demo balans yetarli emas")

        await db.execute(
            "UPDATE users SET balance=? WHERE telegram_id=?",
            (new_balance, tg_id)
        )

        await db.execute(
            """
            INSERT INTO transactions(telegram_id, amount, kind, note)
            VALUES(?, ?, ?, ?)
            """,
            (tg_id, amount, kind, note)
        )

        await db.commit()
        return new_balance
