import logging
import sqlite3

from aiogram.exceptions import TelegramBadRequest

from handlers.callbacks import answer_callback
from keyboards.main import home_menu_keyboard


logger = logging.getLogger(__name__)

GENERAL_ERROR_TEXT = (
    "⚠️ Что-то пошло не так.\n\n"
    "Попробуйте ещё раз немного позже."
)
DATABASE_ERROR_TEXT = (
    "⚠️ Сервис временно недоступен.\n\n"
    "Попробуйте ещё раз немного позже."
)


async def handle_error(event) -> bool:
    exception = event.exception
    if isinstance(exception, TelegramBadRequest) and "message is not modified" in str(
        exception
    ):
        logger.info("Сообщение Telegram уже актуально; повторное изменение пропущено")
        return True

    logger.error(
        "Необработанная ошибка при обработке обновления",
        exc_info=(type(exception), exception, exception.__traceback__),
    )
    text = (
        DATABASE_ERROR_TEXT
        if isinstance(exception, sqlite3.Error)
        else GENERAL_ERROR_TEXT
    )

    try:
        callback = getattr(event.update, "callback_query", None)
        message = getattr(event.update, "message", None)
        if callback is not None:
            await answer_callback(callback)
            message = callback.message
        if message is not None:
            await message.answer(text, reply_markup=home_menu_keyboard())
    except Exception:
        logger.exception("Не удалось отправить пользователю сообщение об ошибке")

    return True
