from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.callbacks import BUY_PREMIUM, MAIN_MENU
from keyboards.main import back_to_menu_keyboard


def premium_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text="🟢 3 месяца ⭐ Рекомендуем",
                callback_data="premium:months:3",
            )
        ],
        [
            InlineKeyboardButton(
                text="🟣 6 месяцев",
                callback_data="premium:months:6",
            )
        ],
        [
            InlineKeyboardButton(
                text="🟡 12 месяцев",
                callback_data="premium:months:12",
            )
        ],
        [
            InlineKeyboardButton(
                text="⚪ 1 месяц 🚧 Скоро",
                callback_data="premium:soon:1",
            )
        ],
    ]
    rows.append(back_to_menu_keyboard().inline_keyboard[0])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def premium_unavailable_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💎 Выбрать другой срок",
                    callback_data=BUY_PREMIUM,
                )
            ],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)],
        ]
    )
