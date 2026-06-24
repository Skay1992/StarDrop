from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.orders import Order, STATUS_PENDING_REVIEW
from keyboards.callbacks import (
    ADMIN_LIST_ALL,
    ADMIN_LIST_CANCELLED,
    ADMIN_LIST_COMPLETED,
    ADMIN_LIST_PENDING,
    ADMIN_MENU,
    MAIN_MENU,
)


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟠 Проверяем оплату", callback_data=ADMIN_LIST_PENDING)],
            [InlineKeyboardButton(text="🟢 Выполненные", callback_data=ADMIN_LIST_COMPLETED)],
            [InlineKeyboardButton(text="🔴 Отмененные", callback_data=ADMIN_LIST_CANCELLED)],
            [InlineKeyboardButton(text="📦 Все заказы", callback_data=ADMIN_LIST_ALL)],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)],
        ]
    )


def admin_orders_list_keyboard(orders: list[Order]) -> InlineKeyboardMarkup:
    rows = []
    for order in orders:
        if order.status != STATUS_PENDING_REVIEW:
            continue
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"✅ #{order.id}",
                    callback_data=f"admin:complete:{order.id}",
                ),
                InlineKeyboardButton(
                    text=f"❌ #{order.id}",
                    callback_data=f"admin:cancel:{order.id}",
                ),
            ]
        )

    rows.append([InlineKeyboardButton(text="↩️ Админ меню", callback_data=ADMIN_MENU)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


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
