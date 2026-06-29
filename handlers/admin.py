from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from config.settings import Settings
from database.orders import (
    OrderRepository,
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_PENDING_REVIEW,
)
from database.statistics import StatisticsRepository, StatisticsSnapshot
from database.users import UserRepository
from handlers.callbacks import answer_callback, log_callback
from handlers.formatters import (
    format_admin_completion_confirmation,
    format_admin_order,
    format_admin_orders_list,
    format_cancelled_message,
    format_completed_message,
)
from keyboards.admin import (
    admin_back_keyboard,
    admin_complete_confirmation_keyboard,
    admin_order_keyboard,
    admin_orders_list_keyboard,
    admin_orders_menu_keyboard,
    admin_panel_keyboard,
)
from keyboards.callbacks import (
    ADMIN_LIST_ALL,
    ADMIN_LIST_CANCELLED,
    ADMIN_LIST_COMPLETED,
    ADMIN_LIST_PENDING,
    ADMIN_MENU,
    ADMIN_ORDERS,
    ADMIN_PROMOCODES,
    ADMIN_SETTINGS,
    ADMIN_STATISTICS,
    ADMIN_USERS,
)
from keyboards.orders import order_cancelled_keyboard, order_completed_keyboard


router = Router()

ADMIN_PANEL_TEXT = (
    "━━━━━━━━━━━━━━\n\n"
    "📊 Панель StarDrop\n\n"
    "Выберите раздел.\n\n"
    "━━━━━━━━━━━━━━"
)
ACCESS_DENIED_TEXT = "⛔ Доступ запрещен."
ADMIN_LISTS = {
    ADMIN_LIST_PENDING: (STATUS_PENDING_REVIEW, "🟠 Заказы на проверке"),
    ADMIN_LIST_COMPLETED: (STATUS_COMPLETED, "🟢 Выполненные заказы"),
    ADMIN_LIST_CANCELLED: (STATUS_CANCELLED, "🔴 Отмененные заказы"),
    ADMIN_LIST_ALL: (None, "📦 Все заказы"),
}


def _is_admin(user_id: int, settings: Settings) -> bool:
    return user_id == settings.admin_id


def format_statistics(stats: StatisticsSnapshot) -> str:
    return (
        "📈 Статистика\n\n"
        "Сегодня\n\n"
        f"📦 Заказов: {stats.today_orders}\n"
        f"💰 Выручка: {stats.today_revenue} ₽\n"
        f"⭐ Stars: {stats.today_stars}\n"
        f"💎 Premium: {stats.today_premium_months} мес.\n"
        f"💬 Обращения: {stats.today_tickets}\n\n"
        "━━━━━━━━━━━━━━\n\n"
        "За всё время\n\n"
        f"📦 Всего заказов: {stats.total_orders}\n"
        f"👥 Пользователей: {stats.total_users}\n"
        f"⭐ Продано Stars: {stats.total_stars}\n"
        f"💎 Продано Premium: {stats.total_premium_months} мес.\n"
        f"💰 Общая выручка: {stats.total_revenue} ₽"
    )


def format_users(stats: StatisticsSnapshot, users) -> str:
    lines = [
        "👥 Пользователи",
        "",
        f"Всего: {stats.total_users}",
        f"Сегодня: {stats.today_users}",
        f"За неделю: {stats.week_users}",
        "",
        "Последние регистрации",
    ]
    for user in users:
        try:
            registered = datetime.strptime(
                user.registered_at,
                "%Y-%m-%d %H:%M:%S",
            ).strftime("%d.%m.%Y")
        except ValueError:
            registered = user.registered_at
        username = f"@{user.username}" if user.username else f"ID {user.user_id}"
        lines.extend(["", f"{username} — {registered}"])
    if not users:
        lines.extend(["", "Регистраций пока нет."])
    return "\n".join(lines)


@router.message(Command("admin"))
async def admin_command(message: Message, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer(ACCESS_DENIED_TEXT)
        return

    await message.answer(ADMIN_PANEL_TEXT, reply_markup=admin_panel_keyboard())


@router.callback_query(F.data == ADMIN_MENU)
async def admin_menu(callback: CallbackQuery, settings: Settings) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
        return

    await answer_callback(callback)
    log_callback(callback)
    await callback.message.edit_text(ADMIN_PANEL_TEXT, reply_markup=admin_panel_keyboard())


@router.callback_query(F.data == ADMIN_ORDERS)
async def admin_orders_menu(callback: CallbackQuery, settings: Settings) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
        return

    await answer_callback(callback)
    await callback.message.edit_text(
        "📦 Заказы\n\nВыберите список заказов.",
        reply_markup=admin_orders_menu_keyboard(),
    )


@router.callback_query(F.data == ADMIN_STATISTICS)
async def admin_statistics(callback: CallbackQuery, settings: Settings) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
        return

    await answer_callback(callback)
    stats = StatisticsRepository().get_snapshot()
    await callback.message.edit_text(
        format_statistics(stats),
        reply_markup=admin_back_keyboard(),
    )


@router.callback_query(F.data == ADMIN_USERS)
async def admin_users(callback: CallbackQuery, settings: Settings) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
        return

    await answer_callback(callback)
    stats = StatisticsRepository().get_snapshot()
    users = UserRepository().list_recent_users(limit=5)
    await callback.message.edit_text(
        format_users(stats, users),
        reply_markup=admin_back_keyboard(),
    )


@router.callback_query(F.data.in_({ADMIN_PROMOCODES, ADMIN_SETTINGS}))
async def admin_stub(callback: CallbackQuery, settings: Settings) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
        return

    await answer_callback(callback)
    await callback.message.edit_text(
        "🚧 Скоро появится",
        reply_markup=admin_back_keyboard(),
    )


@router.callback_query(F.data.startswith("admin:list:"))
async def admin_list_orders(callback: CallbackQuery, settings: Settings) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
        return

    await answer_callback(callback)
    log_callback(callback)
    status, title = ADMIN_LISTS.get(callback.data, (None, "📦 Все заказы"))
    repository = OrderRepository()
    orders = repository.list_orders(status=status, limit=10)
    await callback.message.edit_text(
        format_admin_orders_list(orders, title),
        reply_markup=admin_orders_list_keyboard(orders),
    )


@router.callback_query(F.data.startswith("admin:complete:"))
async def admin_complete_order(callback: CallbackQuery, settings: Settings) -> None:
    if callback.from_user.id != settings.admin_id:
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
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
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
        return

    order_id = int(callback.data.split(":")[-1])
    repository = OrderRepository()
    order = repository.get_order(order_id)
    if order is None:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    await callback.message.edit_text(
        format_admin_order(order),
        reply_markup=admin_order_keyboard(order.id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:confirm_complete:"))
async def admin_confirm_complete_order(callback: CallbackQuery, settings: Settings) -> None:
    if callback.from_user.id != settings.admin_id:
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
        return

    order_id = int(callback.data.split(":")[-1])
    repository = OrderRepository()
    current_order = repository.get_order(order_id)
    if current_order is None:
        await callback.answer("Заказ не найден.", show_alert=True)
        return
    if current_order.status != STATUS_PENDING_REVIEW:
        await callback.answer("Заказ уже обработан.", show_alert=True)
        return

    order = repository.update_status(order_id, STATUS_COMPLETED)
    if order is None:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    UserRepository().record_completed_order(order)

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
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
        return

    order_id = int(callback.data.split(":")[-1])
    repository = OrderRepository()
    order = repository.update_status(order_id, STATUS_CANCELLED)
    if order is None:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    await callback.bot.send_message(
        order.user_id,
        format_cancelled_message(),
        reply_markup=order_cancelled_keyboard(),
    )
    await callback.message.edit_text(format_admin_order(order))
    await callback.answer("Отменено.")
