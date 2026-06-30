from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery

from config.pricing import premium_duration_label
from database.orders import OrderRepository, PRODUCT_PREMIUM
from database.support import SupportTicketRepository
from database.users import User, UserRepository
from handlers.callbacks import answer_callback, log_callback
from handlers.formatters import status_label, support_status_label
from keyboards.cabinet import (
    cabinet_back_keyboard,
    cabinet_keyboard,
    referral_keyboard,
    ticket_details_keyboard,
    ticket_history_keyboard,
)
from keyboards.callbacks import (
    CABINET,
    CABINET_ORDERS,
    CABINET_REFERRAL,
    CABINET_TICKETS,
)


router = Router()
BOT_USERNAME = "stardropstars_bot"


def format_cabinet(user: User) -> str:
    try:
        registration_date = datetime.strptime(
            user.registered_at,
            "%Y-%m-%d %H:%M:%S",
        ).strftime("%d.%m.%Y")
    except ValueError:
        registration_date = user.registered_at

    return (
        "👤 Личный кабинет\n\n"
        "🆔 Ваш ID:\n"
        f"{user.user_id}\n\n"
        "📅 Регистрация:\n"
        f"{registration_date}\n\n"
        "🏆 Статус:\n"
        "Новичок\n\n"
        "━━━━━━━━━━━━━━"
    )


def format_order_history(orders) -> str:
    orders = list(orders)
    if not orders:
        return "📦 История заказов\n\nУ вас пока нет заказов."

    parts = ["📦 История заказов"]
    for order in orders:
        parts.extend(["━━━━━━━━━━━━━━", f"#{order.id}"])
        if order.product_type == PRODUCT_PREMIUM:
            parts.extend(
                [
                    "💎 Telegram Premium",
                    premium_duration_label(order.premium_months),
                ]
            )
        else:
            parts.append(f"⭐ {order.stars_amount} звезд")
        parts.extend([f"{order.price_rub} ₽", status_label(order.status)])
    parts.append("━━━━━━━━━━━━━━")
    return "\n\n".join(parts)


def format_ticket_history(tickets) -> str:
    tickets = list(tickets)
    if not tickets:
        return "💬 Мои обращения\n\nУ вас пока нет обращений."

    parts = ["💬 Мои обращения"]
    for ticket in tickets:
        preview = " ".join(ticket.message.split())
        if len(preview) > 100:
            preview = f"{preview[:97]}..."
        parts.extend(
            [
                "━━━━━━━━━━━━━━",
                f"#{ticket.id}\n{support_status_label(ticket.status)}",
                preview,
            ]
        )
    parts.append("━━━━━━━━━━━━━━")
    return "\n\n".join(parts)


@router.callback_query(F.data == CABINET)
async def show_cabinet(callback: CallbackQuery) -> None:
    await answer_callback(callback)
    log_callback(callback)
    repository = UserRepository()
    user = repository.get_user(callback.from_user.id)
    if user is None:
        user, _ = repository.register_user(
            callback.from_user.id,
            callback.from_user.username,
        )
    await callback.message.edit_text(
        format_cabinet(user),
        reply_markup=cabinet_keyboard(),
    )


@router.callback_query(F.data == CABINET_ORDERS)
async def show_order_history(callback: CallbackQuery) -> None:
    await answer_callback(callback)
    orders = OrderRepository().list_user_orders(callback.from_user.id, limit=15)
    await callback.message.edit_text(
        format_order_history(orders),
        reply_markup=cabinet_back_keyboard(),
    )


@router.callback_query(F.data == CABINET_TICKETS)
async def show_ticket_history(callback: CallbackQuery) -> None:
    await answer_callback(callback)
    tickets = SupportTicketRepository().list_user_tickets(
        callback.from_user.id,
        limit=15,
    )
    await callback.message.edit_text(
        format_ticket_history(tickets),
        reply_markup=ticket_history_keyboard(tickets),
    )


@router.callback_query(F.data.startswith("cabinet:ticket:"))
async def show_ticket_details(callback: CallbackQuery) -> None:
    ticket_id = int(callback.data.split(":")[-1])
    ticket = SupportTicketRepository().get_ticket(ticket_id)
    if ticket is None or ticket.user_id != callback.from_user.id:
        await callback.answer("Обращение не найдено.", show_alert=True)
        return

    text = (
        f"💬 Обращение #{ticket.id}\n\n"
        f"Статус: {support_status_label(ticket.status)}\n\n"
        "Сообщение:\n"
        f"{ticket.message}"
    )
    if ticket.admin_reply:
        text += f"\n\nОтвет поддержки:\n{ticket.admin_reply}"

    await answer_callback(callback)
    await callback.message.edit_text(
        text,
        reply_markup=ticket_details_keyboard(),
    )


@router.callback_query(F.data == CABINET_REFERRAL)
async def show_referral(callback: CallbackQuery) -> None:
    await answer_callback(callback)
    repository = UserRepository()
    user = repository.get_user(callback.from_user.id)
    if user is None:
        user, _ = repository.register_user(
            callback.from_user.id,
            callback.from_user.username,
        )

    link = f"https://t.me/{BOT_USERNAME}?start={user.referral_code}"
    await callback.message.edit_text(
        "👥 Пригласите друзей\n\n"
        "За каждого приглашенного пользователя\n"
        "вы получите бонус.\n\n"
        "Ваша ссылка\n\n"
        f"{link}",
        reply_markup=referral_keyboard(link),
    )
