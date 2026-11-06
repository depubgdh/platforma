from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_IDS
from database import connect
from services.youtube import parse_video_id

router = Router()


def admin(m):
    return m.from_user and m.from_user.id in ADMIN_IDS


@router.message(Command("admin"))
async def help_admin(m: Message):
    if admin(m):
        await m.answer(
            "🛠 ADMIN BUYRUQLARI\n"
            "/addvideo Sarlavha | https://youtu.be/VIDEO_ID\n"
            "/videos\n"
            "/delvideo ID\n"
            "/addtask Sarlavha | Tavsif | 2\n"
            "/tasks\n"
            "/deltask ID\n"
            "/stats\n"
            "Barcha mukofotlar demo 🔆 hisoblanadi."
        )


@router.message(Command("addvideo"))
async def addvideo(m: Message):
    if not admin(m):
        return

    try:
        title, url = [
            x.strip()
            for x in m.text.partition(" ")[2].split("|", 1)
        ]

        vid = parse_video_id(url)

        async with await connect() as db:
            await db.execute(
                """
                INSERT INTO videos(title, youtube_url, youtube_id)
                VALUES(?, ?, ?)
                """,
                (title, url, vid)
            )
            await db.commit()

        await m.answer("✅ Video qo‘shildi.")

    except Exception as e:
        await m.answer(
            f"Xato: {e}\n"
            "Namuna: /addvideo Sarlavha | https://youtu.be/VIDEO_ID"
        )


@router.message(Command("videos"))
async def videos(m: Message):
    if not admin(m):
        return

    async with await connect() as db:
        cur = await db.execute(
            "SELECT id, title, active FROM videos ORDER BY id DESC"
        )
        rows = await cur.fetchall()

    await m.answer(
        "\n".join(
            f'{r["id"]}. {r["title"]} — '
            f'{"faol" if r["active"] else "nofaol"}'
            for r in rows
        ) or "Video yo‘q"
    )


@router.message(Command("delvideo"))
async def delvideo(m: Message):
    if not admin(m):
        return

    try:
        i = int(m.text.split(maxsplit=1)[1])

        async with await connect() as db:
            await db.execute(
                "DELETE FROM videos WHERE id=?",
                (i,)
            )
            await db.commit()

        await m.answer("🗑 Video o‘chirildi.")

    except Exception:
        await m.answer("Foydalanish: /delvideo ID")


@router.message(Command("addtask"))
async def addtask(m: Message):
    if not admin(m):
        return

    try:
        title, desc, reward = [
            x.strip()
            for x in m.text.partition(" ")[2].split("|", 2)
        ]

        reward = float(reward)

        if not 0 < reward <= 1000:
            raise ValueError("Mukofot 0–1000 oralig‘ida bo‘lsin")

        async with await connect() as db:
            await db.execute(
                """
                INSERT INTO tasks(title, description, reward)
                VALUES(?, ?, ?)
                """,
                (title, desc, reward)
            )
            await db.commit()

        await m.answer("✅ Topshiriq yaratildi.")

    except Exception as e:
        await m.answer(
            f"Xato: {e}\n"
            "Namuna: /addtask Test | Demo vazifa | 2"
        )


@router.message(Command("tasks"))
async def tasks(m: Message):
    if not admin(m):
        return

    async with await connect() as db:
        cur = await db.execute(
            "SELECT id, title, reward FROM tasks ORDER BY id DESC"
        )
        rows = await cur.fetchall()

    await m.answer(
        "\n".join(
            f'{r["id"]}. {r["title"]} — {r["reward"]} 🔆'
            for r in rows
        ) or "Topshiriq yo‘q"
    )


@router.message(Command("deltask"))
async def deltask(m: Message):
    if not admin(m):
        return

    try:
        i = int(m.text.split(maxsplit=1)[1])

        async with await connect() as db:
            await db.execute(
                "DELETE FROM tasks WHERE id=?",
                (i,)
            )
            await db.commit()

        await m.answer("🗑 Topshiriq o‘chirildi.")

    except Exception:
        await m.answer("Foydalanish: /deltask ID")


@router.message(Command("stats"))
async def stats(m: Message):
    if not admin(m):
        return

    async with await connect() as db:
        a = await (
            await db.execute(
                """
                SELECT COUNT(*) n, COALESCE(SUM(balance), 0) b
                FROM users
                """
            )
        ).fetchone()

        v = await (
            await db.execute(
                "SELECT COUNT(*) n FROM videos WHERE active=1"
            )
        ).fetchone()

        t = await (
            await db.execute(
                "SELECT COUNT(*) n FROM tasks WHERE active=1"
            )
        ).fetchone()

    await m.answer(
        f"👥 Foydalanuvchilar: {a['n']}\n"
        f"🔆 Demo balanslar yig‘indisi: {a['b']:.2f}\n"
        f"🎬 Videolar: {v['n']}\n"
        f"🎯 Topshiriqlar: {t['n']}"
    )
