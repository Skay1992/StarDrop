from aiogram import Router
from aiogram.types import CallbackQuery

from handlers.callbacks import answer_callback


router = Router()


@router.callback_query()
async def log_unhandled_callback(callback: CallbackQuery) -> None:
    await answer_callback(callback)
    print(f"UNHANDLED CALLBACK RECEIVED: {callback.data}", flush=True)
