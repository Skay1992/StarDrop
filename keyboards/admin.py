from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Выполнено",
                    callback_data=f"admin:complete:{order_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отменено",
                    callback_data=f"admin:cancel:{order_id}",
                ),
            ]
        ]
    )


def admin_complete_confirmation_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, выполнить",
                    callback_data=f"admin:confirm_complete:{order_id}",
                ),
                InlineKeyboardButton(
                    text="↩️ Нет, назад",
                    callback_data=f"admin:back:{order_id}",
                ),
            ]
        ]
    )
