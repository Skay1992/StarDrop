import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery


logger = logging.getLogger(__name__)


async def answer_callback(callback: CallbackQuery) -> None:
    try:
        await callback.answer()
    except TelegramBadRequest as exc:
        message = str(exc)
        if "query is too old" not in message and "query ID is invalid" not in message:
            raise
        logger.warning("Истек срок callback: %s", callback.data)


def log_callback(callback: CallbackQuery) -> None:
    logger.info("Получен callback: %s", callback.data)
