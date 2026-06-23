from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config.pricing import STARS_PRICES
from keyboards.main import back_to_menu_keyboard


def stars_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{amount} · {price} ₽",
                callback_data=f"stars:amount:{amount}",
            )
        ]
        for amount, price in STARS_PRICES.items()
    ]
    rows.append([InlineKeyboardButton(text="Своё количество", callback_data="stars:custom")])
    rows.append(back_to_menu_keyboard().inline_keyboard[0])
    return InlineKeyboardMarkup(inline_keyboard=rows)
