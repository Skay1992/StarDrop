from aiogram import F, Router
from aiogram.types import CallbackQuery

from config.settings import Settings
from database.orders import (
    OrderRepository,
    STATUS_AWAITING_PAYMENT,
    STATUS_CANCELLED,
    STATUS_PENDING_REVIEW,
)
from handlers.callbacks import answer_callback, log_callback
from handlers.formatters import format_admin_order, format_order_summary, format_orders_list
from keyboards.admin import admin_order_keyboard
from keyboards.callbacks import LEGACY_MY_ORDERS, MY_ORDERS
from keyboards.main import home_menu_keyboard


router = Router()


@router.callback_query(F.data.in_({MY_ORDERS, LEGACY_MY_ORDERS}))
async def list_orders(callback: CallbackQuery) -> None:
    await answer_callback(callback)
    log_callback(callback)
    repository = OrderRepository()
    orders = repository.list_user_orders(callback.from_user.id)
    await callback.message.edit_text(format_orders_list(orders), reply_markup=home_menu_keyboard())


@router.callback_query(F.data.startswith("order:paid:"))
async def order_paid(callback: CallbackQuery, settings: Settings) -> None:
    order_id = int(callback.data.split(":")[-1])
    repository = OrderRepository()
    order = repository.get_order(order_id)

    if order is None or order.user_id != callback.from_user.id:
        await callback.answer("Заказ не найден.", show_alert=True)
        return
    if order.status != STATUS_AWAITING_PAYMENT:
        await callback.answer("Статус уже изменен.", show_alert=True)
        return

    order = repository.update_status(order_id, STATUS_PENDING_REVIEW)
    await callback.message.edit_text(format_order_summary(order), reply_markup=home_menu_keyboard())
    await callback.bot.send_message(
        chat_id=settings.admin_id,
        text=format_admin_order(order),
        reply_markup=admin_order_keyboard(order.id),
    )
    await callback.answer("Оплата отправлена на проверку.")


@router.callback_query(F.data.startswith("order:cancel:"))
async def order_cancel(callback: CallbackQuery) -> None:
    order_id = int(callback.data.split(":")[-1])
    repository = OrderRepository()
    order = repository.get_order(order_id)

    if order is None or order.user_id != callback.from_user.id:
        await callback.answer("Заказ не найден.", show_alert=True)
        return
    if order.status != STATUS_AWAITING_PAYMENT:
        await callback.answer("Заказ уже на проверке.", show_alert=True)
        return

    repository.update_status(order_id, STATUS_CANCELLED)
    await callback.message.edit_text("Заказ отменен.", reply_markup=home_menu_keyboard())
    await callback.answer()
