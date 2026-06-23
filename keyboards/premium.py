from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config.pricing import PREMIUM_PRICES, premium_duration_label
from keyboards.main import back_to_menu_keyboard


def premium_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{premium_duration_label(months)} · {price} ₽",
                callback_data=f"premium:months:{months}",
            )
        ]
        for months, price in PREMIUM_PRICES.items()
    ]
    rows.append(back_to_menu_keyboard().inline_keyboard[0])
    return InlineKeyboardMarkup(inline_keyboard=rows)
