from aiogram import F, Router
from aiogram.types import CallbackQuery

from handlers.callbacks import answer_callback, log_callback
from keyboards.callbacks import LEGACY_SUPPORT, SUPPORT
from keyboards.main import home_menu_keyboard


router = Router()

SUPPORT_TEXT = (
    "💬 Поддержка StarDrop\n\n"
    "Если возник вопрос по заказу — напишите:\n"
    "@StarDropSupport\n\n"
    "⏱ Обычно отвечаем в течение 5–15 минут."
)


@router.callback_query(F.data.in_({SUPPORT, LEGACY_SUPPORT}))
async def support(callback: CallbackQuery) -> None:
    await answer_callback(callback)
    log_callback(callback)
    await callback.message.edit_text(
        SUPPORT_TEXT,
        reply_markup=home_menu_keyboard(),
    )
