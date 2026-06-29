from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.callbacks import MAIN_MENU, SUPPORT


def support_ticket_admin_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✉️ Ответить",
                    callback_data=f"support:reply:{ticket_id}",
                ),
                InlineKeyboardButton(
                    text="✅ Закрыть",
                    callback_data=f"support:close:{ticket_id}",
                ),
            ]
        ]
    )


def support_answer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Задать ещё вопрос", callback_data=SUPPORT)],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)],
        ]
    )
