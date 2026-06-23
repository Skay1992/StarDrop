from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.callbacks import BUY_PREMIUM, BUY_STARS, MAIN_MENU, MY_ORDERS, SUPPORT


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Купить звезды", callback_data=BUY_STARS)],
            [InlineKeyboardButton(text="💎 Telegram Premium", callback_data=BUY_PREMIUM)],
            [InlineKeyboardButton(text="📦 Мои заказы", callback_data=MY_ORDERS)],
            [InlineKeyboardButton(text="💬 Поддержка", callback_data=SUPPORT)],
        ]
    )


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↩️ В меню", callback_data=MAIN_MENU)]
        ]
    )


def home_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)]
        ]
    )
