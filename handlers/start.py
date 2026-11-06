from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo
)

from config import WEBAPP_URL
from database import ensure_user

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    await ensure_user(message.from_user)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🚀 Ilovani ochish",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            ],
            [
                KeyboardButton(text="ℹ️ Yordam")
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "Assalomu alaykum! 🔆 Demo platformaga xush kelibsiz.\n"
        "Bu sinov muhiti: 🔆 haqiqiy pul emas va yechib olinmaydi. "
        "YouTube tomoshasi uchun mukofot berilmaydi; "
        "demo ballar mustaqil topshiriqlardan olinadi.",
        reply_markup=kb
    )


@router.message(F.text == "ℹ️ Yordam")
async def help_msg(message: Message):
    await message.answer(
        "🚀 Ilovani oching. Topshiriqlar bo‘limidan demo vazifalarni bajaring."
    )
