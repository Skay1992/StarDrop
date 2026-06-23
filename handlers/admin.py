from aiogram import F, Router
from aiogram.types import CallbackQuery

from config.settings import Settings
from database.orders import OrderRepository, STATUS_CANCELLED, STATUS_COMPLETED
from handlers.formatters import (
    format_admin_completion_confirmation,
    format_admin_order,
    format_completed_message,
)
from keyboards.admin import admin_complete_confirmation_keyboard, admin_order_keyboard
from keyboards.main import home_menu_keyboard
from keyboards.orders import order_completed_keyboard


router = Router()


@router.callback_query(F.data.startswith("admin:complete:"))
async def admin_complete_order(callback: CallbackQuery, settings: Settings) -> None:
    if callback.from_user.id != settings.admin_id:
        await callback.answer("Недоступно.", show_alert=True)
        return

    order_id = int(callback.data.split(":")[-1])
    repository = OrderRepository()
    order = repository.get_order(order_id)
    if order is None:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    await callback.message.edit_text(
        format_admin_completion_confirmation(order.id),
        reply_markup=admin_complete_confirmation_keyboard(order.id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:back:"))
async def admin_back_to_order(callback: CallbackQuery, settings: Settings) -> None:
    if callback.from_user.id != settings.admin_id:
        await callback.answer("Недоступно.", show_alert=True)
        return

    order_id = int(callback.data.split(":")[-1])
    repository = OrderRepository()
    order = repository.get_order(order_id)
    if order is None:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    await callback.message.edit_text(format_admin_order(order), reply_markup=admin_order_keyboard(order.id))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:confirm_complete:"))
async def admin_confirm_complete_order(callback: CallbackQuery, settings: Settings) -> None:
    if callback.from_user.id != settings.admin_id:
        await callback.answer("Недоступно.", show_alert=True)
        return

    order_id = int(callback.data.split(":")[-1])
    repository = OrderRepository()
    order = repository.update_status(order_id, STATUS_COMPLETED)
    if order is None:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    await callback.bot.send_message(
        order.user_id,
        format_completed_message(order),
        reply_markup=order_completed_keyboard(),
    )
    await callback.message.edit_text(format_admin_order(order))
    await callback.answer("Готово.")


@router.callback_query(F.data.startswith("admin:cancel:"))
async def admin_cancel_order(callback: CallbackQuery, settings: Settings) -> None:
    if callback.from_user.id != settings.admin_id:
        await callback.answer("Недоступно.", show_alert=True)
        return

    order_id = int(callback.data.split(":")[-1])
    repository = OrderRepository()
    order = repository.update_status(order_id, STATUS_CANCELLED)
    if order is None:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    await callback.bot.send_message(
        order.user_id,
        "Заказ отменен.\nОбратитесь в поддержку.",
        reply_markup=home_menu_keyboard(),
    )
    await callback.message.edit_text(format_admin_order(order))
    await callback.answer("Отменено.")
