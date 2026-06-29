from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.support import SupportTicket
from keyboards.callbacks import (
    ADMIN_MENU,
    ADMIN_SUPPORT,
    ADMIN_SUPPORT_ALL,
    ADMIN_SUPPORT_ARCHIVE,
    ADMIN_SUPPORT_OPEN,
    MAIN_MENU,
    SUPPORT,
)


def admin_support_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟠 Открытые", callback_data=ADMIN_SUPPORT_OPEN)],
            [InlineKeyboardButton(text="📂 Архив", callback_data=ADMIN_SUPPORT_ARCHIVE)],
            [
                InlineKeyboardButton(
                    text="📋 Все",
                    callback_data=ADMIN_SUPPORT_ALL,
                )
            ],
            [InlineKeyboardButton(text="↩️ Админ меню", callback_data=ADMIN_MENU)],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)],
        ]
    )


def _ticket_button_text(ticket: SupportTicket) -> str:
    client = f"@{ticket.username}" if ticket.username else f"ID {ticket.user_id}"
    return f"💬 #{ticket.id} — {client}"


def admin_support_list_keyboard(
    tickets: list[SupportTicket],
    scope: str = "open",
    page: int = 0,
    has_next: bool = False,
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=_ticket_button_text(ticket),
                callback_data=f"support:admin:view:{ticket.id}",
            )
        ]
        for ticket in tickets
    ]
    pagination = []
    callback_base = f"admin:support:list:{scope}"
    if page > 0:
        pagination.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"{callback_base}:{page - 1}",
            )
        )
    if has_next:
        pagination.append(
            InlineKeyboardButton(
                text="➡️ Вперёд",
                callback_data=f"{callback_base}:{page + 1}",
            )
        )
    if pagination:
        rows.append(pagination)

    rows.extend(admin_support_menu_keyboard().inline_keyboard[:3])
    rows.append([InlineKeyboardButton(text="↩️ Админ меню", callback_data=ADMIN_MENU)])
    rows.append(
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def support_ticket_admin_keyboard(
    ticket_id: int,
    include_navigation: bool = False,
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text="✉️ Ответить",
                callback_data=f"support:reply:{ticket_id}",
            ),
            InlineKeyboardButton(
                text="📦 Открыть заказ",
                callback_data=f"support:order:{ticket_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="✅ Закрыть",
                callback_data=f"support:close:{ticket_id}",
            )
        ],
    ]
    if include_navigation:
        rows.extend(
            [
                [
                    InlineKeyboardButton(
                        text="↩️ К поддержке",
                        callback_data=ADMIN_SUPPORT,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🏠 Главное меню",
                        callback_data=MAIN_MENU,
                    )
                ],
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def support_answer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Ответить ещё", callback_data=SUPPORT)],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)],
        ]
    )


def existing_open_ticket_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👀 Посмотреть обращение",
                    callback_data=f"support:mine:{ticket_id}",
                )
            ],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)],
        ]
    )


def support_order_back_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="↩️ К обращению",
                    callback_data=f"support:admin:view:{ticket_id}",
                )
            ],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)],
        ]
    )
