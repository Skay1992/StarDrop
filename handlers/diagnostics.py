import logging

from aiogram import Router
from aiogram.types import CallbackQuery

from handlers.callbacks import answer_callback


router = Router()
logger = logging.getLogger(__name__)


@router.callback_query()
async def log_unhandled_callback(callback: CallbackQuery) -> None:
    await answer_callback(callback)
    logger.warning("Получен неизвестный callback: %s", callback.data)
