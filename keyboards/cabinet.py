from urllib.parse import urlencode

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.support import SupportTicket
from keyboards.callbacks import (
    CABINET,
    CABINET_ORDERS,
    CABINET_REFERRAL,
    CABINET_TICKETS,
    MAIN_MENU,
)


def cabinet_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📦 История заказов",
                    callback_data=CABINET_ORDERS,
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Мои обращения",
                    callback_data=CABINET_TICKETS,
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Пригласить друга",
                    callback_data=CABINET_REFERRAL,
                )
            ],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)],
        ]
    )


def cabinet_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅ Назад", callback_data=CABINET)],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)],
        ]
    )


def ticket_history_keyboard(tickets: list[SupportTicket]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"👀 Обращение #{ticket.id}",
                callback_data=f"cabinet:ticket:{ticket.id}",
            )
        ]
        for ticket in tickets
    ]
    rows.extend(cabinet_back_keyboard().inline_keyboard)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ticket_details_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅ Назад", callback_data=CABINET_TICKETS)],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)],
        ]
    )


def referral_keyboard(link: str) -> InlineKeyboardMarkup:
    share_url = f"https://t.me/share/url?{urlencode({'url': link})}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📤 Поделиться", url=share_url)],
            [InlineKeyboardButton(text="⬅ Назад", callback_data=CABINET)],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)],
        ]
    )
