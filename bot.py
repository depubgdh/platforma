import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from config import BOT_TOKEN, PORT
from database import init_db
from handlers.start import router as start_router
from handlers.admin import router as admin_router
from api.routes import router as api_router

app = FastAPI(title="Demo Platform API")
app.include_router(api_router)

# Mini App fayllari API marshrutlaridan keyin ulanadi.
WEBAPP_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "webapp"
)
app.mount("/", StaticFiles(directory=WEBAPP_DIR, html=True), name="webapp")


async def run_api():
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="0.0.0.0",
            port=PORT,
            log_level="info"
        )
    )
    await server.serve()


async def run_bot():
    bot = Bot(
        BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(admin_router)
    await dp.start_polling(bot)


async def main():
    await init_db()
    await asyncio.gather(run_api(), run_bot())


if __name__ == "__main__":
    asyncio.run(main())
