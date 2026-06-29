from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.callbacks import MAIN_MENU, MY_ORDERS, SUPPORT


def payment_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Я оплатил",
                    callback_data=f"order:paid:{order_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data=f"order:cancel:{order_id}",
                ),
            ],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)],
        ]
    )


def order_completed_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Мои заказы", callback_data=MY_ORDERS)],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)],
        ]
    )


def order_cancelled_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Поддержка", callback_data=SUPPORT)],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)],
        ]
    )
