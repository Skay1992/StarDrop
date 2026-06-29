from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config.settings import DEFAULT_REVIEWS_URL
from keyboards.callbacks import BUY_PREMIUM, BUY_STARS, CABINET, MAIN_MENU, SUPPORT


def main_menu_keyboard(reviews_url: str = DEFAULT_REVIEWS_URL) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Купить Stars", callback_data=BUY_STARS)],
            [InlineKeyboardButton(text="💎 Telegram Premium", callback_data=BUY_PREMIUM)],
            [InlineKeyboardButton(text="⭐ Отзывы", url=reviews_url)],
            [InlineKeyboardButton(text="👤 Личный кабинет", callback_data=CABINET)],
            [InlineKeyboardButton(text="💬 Поддержка", callback_data=SUPPORT)],
        ]
    )


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)]
        ]
    )


def home_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)]
        ]
    )
