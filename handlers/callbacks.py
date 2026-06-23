from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery


async def answer_callback(callback: CallbackQuery) -> None:
    try:
        await callback.answer()
    except TelegramBadRequest as exc:
        message = str(exc)
        if "query is too old" not in message and "query ID is invalid" not in message:
            raise
        print(f"CALLBACK ANSWER EXPIRED: {callback.data}", flush=True)


def log_callback(callback: CallbackQuery) -> None:
    print(f"CALLBACK RECEIVED: {callback.data}", flush=True)
