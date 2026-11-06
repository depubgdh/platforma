import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from database import connect, get_user, change_balance
from services.security import verify_init_data
from config import ADMIN_API_KEY

router = APIRouter(prefix="/api")


async def current_user(init_data):
    tg_id = verify_init_data(init_data)

    if not tg_id:
        raise HTTPException(401, "Telegram sessiyasi tasdiqlanmadi")

    user = await get_user(tg_id)

    if not user or user["is_blocked"]:
        raise HTTPException(403, "Hisob mavjud emas yoki bloklangan")

    return tg_id, user


@router.get("/me")
async def me(
    x_telegram_init_data: str | None = Header(default=None)
):
    tg_id, user = await current_user(x_telegram_init_data)

    async with await connect() as db:
        cur = await db.execute(
            """
            SELECT id, title, youtube_id
            FROM videos
            WHERE active=1
            ORDER BY RANDOM()
            LIMIT 1
            """
        )
        video = await cur.fetchone()

        cur = await db.execute(
            """
            SELECT id, title, description, reward
            FROM tasks
            WHERE active=1
            ORDER BY id DESC
            """
        )
        tasks = [dict(x) for x in await cur.fetchall()]

        cur = await db.execute(
            "SELECT task_id FROM completions WHERE telegram_id=?",
            (tg_id,)
        )
        completed = [x["task_id"] for x in await cur.fetchall()]

        cur = await db.execute(
            """
            SELECT amount, kind, note, created_at
            FROM transactions
            WHERE telegram_id=?
            ORDER BY id DESC
            LIMIT 20
            """,
            (tg_id,)
        )
        history = [dict(x) for x in await cur.fetchall()]

    return {
        "user": {
            "id": tg_id,
            "name": user["first_name"],
            "balance": user["balance"]
        },
        "video": dict(video) if video else None,
        "tasks": tasks,
        "completed_tasks": completed,
        "transactions": history,
        "currency": "🔆",
        "demo": True
    }


class CompleteTask(BaseModel):
    task_id: int
    answer: str = Field(default="", max_length=200)


@router.post("/tasks/complete")
async def complete_task(
    body: CompleteTask,
    x_telegram_init_data: str | None = Header(default=None)
):
    tg_id, _ = await current_user(x_telegram_init_data)

    async with await connect() as db:
        await db.execute("BEGIN IMMEDIATE")

        cur = await db.execute(
            "SELECT * FROM tasks WHERE id=? AND active=1",
            (body.task_id,)
        )
        task = await cur.fetchone()

        if not task:
            await db.rollback()
            raise HTTPException(404, "Topshiriq topilmadi")

        cur = await db.execute(
            """
            SELECT 1 FROM completions
            WHERE telegram_id=? AND task_id=?
            """,
            (tg_id, body.task_id)
        )

        if await cur.fetchone():
            await db.rollback()
            raise HTTPException(409, "Bu topshiriq avval bajarilgan")

        await db.execute(
            """
            INSERT INTO completions(telegram_id, task_id)
            VALUES(?, ?)
            """,
            (tg_id, body.task_id)
        )

        cur = await db.execute(
            "SELECT balance FROM users WHERE telegram_id=?",
            (tg_id,)
        )
        old = float((await cur.fetchone())["balance"])
        new = round(old + float(task["reward"]), 4)

        await db.execute(
            "UPDATE users SET balance=? WHERE telegram_id=?",
            (new, tg_id)
        )

        await db.execute(
            """
            INSERT INTO transactions(telegram_id, amount, kind, note)
            VALUES(?, ?, ?, ?)
            """,
            (
                tg_id,
                task["reward"],
                "demo_reward",
                "Topshiriq: " + task["title"]
            )
        )

        await db.commit()

    return {
        "ok": True,
        "reward": task["reward"],
        "balance": new
    }


@router.post("/bulldrop/demo-token")
async def make_demo_token(
    x_telegram_init_data: str | None = Header(default=None)
):
    tg_id, _ = await current_user(x_telegram_init_data)

    token = secrets.token_urlsafe(24)
    expires = (
        datetime.now(timezone.utc) + timedelta(minutes=5)
    ).isoformat()

    async with await connect() as db:
        await db.execute(
            """
            INSERT INTO demo_tokens(token, telegram_id, expires_at)
            VALUES(?, ?, ?)
            """,
            (token, tg_id, expires)
        )
        await db.commit()

    return {
        "token": token,
        "expires_at": expires,
        "demo": True
    }


class Adjust(BaseModel):
    telegram_id: int
    amount: float = Field(gt=0, le=1000)
    note: str = Field(min_length=2, max_length=200)


@router.post("/admin/adjust")
async def admin_adjust(
    body: Adjust,
    x_admin_key: str | None = Header(default=None)
):
    if (
        not x_admin_key
        or not ADMIN_API_KEY
        or not secrets.compare_digest(x_admin_key, ADMIN_API_KEY)
    ):
        raise HTTPException(403, "Admin ruxsati yo‘q")

    try:
        balance = await change_balance(
            body.telegram_id,
            body.amount,
            "admin_demo_adjust",
            body.note
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {
        "ok": True,
        "balance": balance
    }
