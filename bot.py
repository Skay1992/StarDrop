import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config.settings import load_settings
from database.db import init_db
from handlers import admin, cabinet, diagnostics, orders, premium, stars, start, support


async def main() -> None:
    settings = load_settings()
    init_db(settings.db_path)

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())
    dp["settings"] = settings

    dp.include_router(start.router)
    dp.include_router(stars.router)
    dp.include_router(premium.router)
    dp.include_router(orders.router)
    dp.include_router(cabinet.router)
    dp.include_router(support.router)
    dp.include_router(admin.router)
    dp.include_router(diagnostics.router)

    print("BOT STARTED: polling Telegram updates", flush=True)
    await dp.start_polling(bot)


def run() -> None:
    try:
        asyncio.run(main())
    except RuntimeError as exc:
        message = str(exc)
        if "BOT_TOKEN" in message or "ADMIN_ID" in message or ".env" in message:
            print(f"Ошибка настройки: {message}", file=sys.stderr)
            raise SystemExit(1) from None
        raise


if __name__ == "__main__":
    run()
