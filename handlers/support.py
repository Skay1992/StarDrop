import logging
from typing import Iterable, Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config.settings import Settings
from database.orders import Order, OrderRepository
from database.support import (
    STATUS_ANSWERED,
    STATUS_CLOSED,
    STATUS_OPEN,
    SupportTicket,
    SupportTicketRepository,
)
from handlers.callbacks import answer_callback, log_callback
from handlers.formatters import (
    format_admin_order,
    product_label,
    status_label,
    support_status_label,
)
from handlers.security import require_admin_callback
from handlers.states import SupportAdminState, SupportUserState
from keyboards.callbacks import (
    ADMIN_SUPPORT,
    ADMIN_SUPPORT_ALL,
    ADMIN_SUPPORT_ANSWERED,
    ADMIN_SUPPORT_CLOSED,
    ADMIN_SUPPORT_OPEN,
    LEGACY_SUPPORT,
    SUPPORT,
)
from keyboards.main import home_menu_keyboard
from keyboards.support import (
    admin_support_menu_keyboard,
    admin_support_list_keyboard,
    existing_open_ticket_keyboard,
    support_answer_keyboard,
    support_order_back_keyboard,
    support_ticket_admin_keyboard,
)


router = Router()
logger = logging.getLogger(__name__)

SUPPORT_TEXT = (
    "💬 Поддержка StarDrop\n\n"
    "Опишите вопрос одним сообщением.\n"
    "Мы ответим прямо в этом чате.\n\n"
    "⏱ Обычно отвечаем в течение 5–15 минут."
)

MAX_SUPPORT_MESSAGE_LENGTH = 3000
ADMIN_SUPPORT_TEXT = "💬 Поддержка StarDrop\n\nВыберите список обращений."
ADMIN_SUPPORT_LISTS = {
    ADMIN_SUPPORT_OPEN: (STATUS_OPEN, "🟢 Открытые обращения"),
    ADMIN_SUPPORT_ANSWERED: (STATUS_ANSWERED, "✅ Отвеченные обращения"),
    ADMIN_SUPPORT_CLOSED: (STATUS_CLOSED, "🔒 Закрытые обращения"),
    ADMIN_SUPPORT_ALL: (None, "📋 Все обращения"),
}


def format_admin_ticket(
    ticket: SupportTicket,
    order: Optional[Order] = None,
    heading: Optional[str] = None,
    include_status: bool = False,
) -> str:
    username = f"@{ticket.username}" if ticket.username else "не указан"
    title = heading or f"🔔 Новое обращение #{ticket.id}"
    if order is None:
        order_text = "нет"
    else:
        order_text = (
            f"#{order.id}\n"
            f"{product_label(order)} / {order.price_rub} ₽ / {status_label(order.status)}"
        )
    text = (
        f"{title}\n\n"
        "👤 Клиент:\n"
        f"{username}\n\n"
        "ID:\n"
        f"{ticket.user_id}\n\n"
        "📦 Последний заказ:\n"
        f"{order_text}\n\n"
        "Сообщение:\n"
        f"{ticket.message}"
    )
    if include_status:
        text += f"\n\nСтатус: {support_status_label(ticket.status)}"
        if ticket.admin_reply:
            text += f"\n\nОтвет администратора:\n{ticket.admin_reply}"
    return text


def format_support_tickets(
    tickets: Iterable[SupportTicket],
    title: str = "💬 Последние обращения",
) -> str:
    tickets = list(tickets)
    if not tickets:
        return f"{title}\n\nОбращений пока нет."

    lines = [title]
    for ticket in tickets:
        username = f"@{ticket.username}" if ticket.username else f"ID {ticket.user_id}"
        message_preview = " ".join(ticket.message.split())
        if len(message_preview) > 200:
            message_preview = f"{message_preview[:197]}..."
        lines.extend(
            [
                "",
                f"#{ticket.id} — {username}",
                f"Статус: {support_status_label(ticket.status)}",
                f"Сообщение: {message_preview}",
                f"Дата: {ticket.created_at}",
            ]
        )
    return "\n".join(lines)


@router.callback_query(F.data == ADMIN_SUPPORT)
async def admin_support_menu(callback: CallbackQuery, settings: Settings) -> None:
    if not await require_admin_callback(callback, settings):
        return

    await callback.answer()
    await callback.message.edit_text(
        ADMIN_SUPPORT_TEXT,
        reply_markup=admin_support_menu_keyboard(),
    )


@router.callback_query(F.data.startswith("admin:support:list:"))
async def admin_support_list(callback: CallbackQuery, settings: Settings) -> None:
    if not await require_admin_callback(callback, settings):
        return

    status, title = ADMIN_SUPPORT_LISTS.get(
        callback.data,
        (None, "📋 Все обращения"),
    )
    tickets = SupportTicketRepository().list_tickets(status=status, limit=10)
    await callback.answer()
    await callback.message.edit_text(
        format_support_tickets(tickets, title),
        reply_markup=admin_support_list_keyboard(tickets),
    )


@router.callback_query(F.data.startswith("support:admin:view:"))
async def admin_view_ticket(callback: CallbackQuery, settings: Settings) -> None:
    if not await require_admin_callback(callback, settings):
        return

    ticket_id = int(callback.data.split(":")[-1])
    ticket = SupportTicketRepository().get_ticket(ticket_id)
    if ticket is None:
        await callback.answer("Обращение не найдено.", show_alert=True)
        return

    order = None
    if ticket.related_order_id is not None:
        order = OrderRepository().get_order(ticket.related_order_id)

    await callback.answer()
    await callback.message.edit_text(
        format_admin_ticket(
            ticket,
            order,
            heading=f"💬 Обращение #{ticket.id}",
            include_status=True,
        ),
        reply_markup=support_ticket_admin_keyboard(
            ticket.id,
            include_navigation=True,
        ),
    )


@router.message(Command("support_tickets"))
async def support_tickets_command(message: Message, settings: Settings) -> None:
    if message.from_user.id != settings.admin_id:
        await message.answer("⛔ Доступ запрещен.")
        return

    repository = SupportTicketRepository()
    tickets = repository.list_tickets(limit=10)
    await message.answer(format_support_tickets(tickets))


@router.callback_query(F.data.in_({SUPPORT, LEGACY_SUPPORT}))
async def support(callback: CallbackQuery, state: FSMContext) -> None:
    await answer_callback(callback)
    log_callback(callback)
    await state.set_state(SupportUserState.message)
    await callback.message.edit_text(
        SUPPORT_TEXT,
        reply_markup=home_menu_keyboard(),
    )


@router.callback_query(F.data.startswith("support:mine:"))
async def view_own_ticket(callback: CallbackQuery) -> None:
    ticket_id = int(callback.data.split(":")[-1])
    ticket = SupportTicketRepository().get_ticket(ticket_id)
    if ticket is None or ticket.user_id != callback.from_user.id:
        await callback.answer("Обращение не найдено.", show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(
        f"💬 Обращение #{ticket.id}\n\n"
        f"Статус: {support_status_label(ticket.status)}\n\n"
        "Сообщение:\n"
        f"{ticket.message}",
        reply_markup=home_menu_keyboard(),
    )


@router.message(SupportUserState.message)
async def submit_support_ticket(message: Message, state: FSMContext, settings: Settings) -> None:
    if not message.text or not message.text.strip():
        await message.answer(
            "Отправьте вопрос текстовым сообщением.",
            reply_markup=home_menu_keyboard(),
        )
        return

    support_message = message.text.strip()
    if len(support_message) > MAX_SUPPORT_MESSAGE_LENGTH:
        await message.answer(
            f"Сократите вопрос до {MAX_SUPPORT_MESSAGE_LENGTH} символов.",
            reply_markup=home_menu_keyboard(),
        )
        return

    orders = OrderRepository().list_user_orders(message.from_user.id, limit=1)
    last_order = orders[0] if orders else None
    repository = SupportTicketRepository()
    ticket, created = repository.create_ticket_if_no_open(
        user_id=message.from_user.id,
        username=message.from_user.username,
        message=support_message,
        related_order_id=last_order.id if last_order else None,
    )
    if not created:
        await state.clear()
        await message.answer(
            "У вас уже есть открытое обращение.\n"
            "Дождитесь ответа поддержки.",
            reply_markup=existing_open_ticket_keyboard(ticket.id),
        )
        return

    await state.clear()
    logger.info(
        "Создано обращение №%s пользователя %s",
        ticket.id,
        ticket.user_id,
    )
    await message.answer(
        "✅ Вопрос отправлен\n\nМы ответим как можно быстрее.",
        reply_markup=home_menu_keyboard(),
    )
    await message.bot.send_message(
        chat_id=settings.admin_id,
        text=format_admin_ticket(ticket, last_order),
        reply_markup=support_ticket_admin_keyboard(ticket.id),
    )


@router.callback_query(F.data.startswith("support:reply:"))
async def start_support_reply(
    callback: CallbackQuery,
    state: FSMContext,
    settings: Settings,
) -> None:
    if not await require_admin_callback(callback, settings):
        return

    ticket_id = int(callback.data.split(":")[-1])
    repository = SupportTicketRepository()
    ticket = repository.get_ticket(ticket_id)
    if ticket is None:
        await callback.answer("Обращение не найдено.", show_alert=True)
        return

    await callback.answer()
    await state.update_data(support_ticket_id=ticket.id)
    await state.set_state(SupportAdminState.reply)
    await callback.message.answer("Введите ответ клиенту")


@router.message(SupportAdminState.reply)
async def send_support_reply(message: Message, state: FSMContext, settings: Settings) -> None:
    if message.from_user.id != settings.admin_id:
        await state.clear()
        await message.answer("⛔ Доступ запрещен.")
        return

    if not message.text or not message.text.strip():
        await message.answer("Отправьте ответ текстовым сообщением.")
        return

    answer = message.text.strip()
    if len(answer) > MAX_SUPPORT_MESSAGE_LENGTH:
        await message.answer(
            f"Сократите ответ до {MAX_SUPPORT_MESSAGE_LENGTH} символов."
        )
        return

    data = await state.get_data()
    ticket_id = data.get("support_ticket_id")
    repository = SupportTicketRepository()
    ticket = repository.get_ticket(ticket_id)
    if ticket is None:
        await state.clear()
        await message.answer("Обращение не найдено.")
        return

    await message.bot.send_message(
        chat_id=ticket.user_id,
        text=f"💬 Ответ поддержки StarDrop\n\n{answer}",
        reply_markup=support_answer_keyboard(),
    )
    repository.answer_ticket(ticket.id, answer)
    logger.info("Отправлен ответ на обращение №%s", ticket.id)
    await state.clear()
    await message.answer("Ответ отправлен.")


@router.callback_query(F.data.startswith("support:order:"))
async def open_related_order(callback: CallbackQuery, settings: Settings) -> None:
    if not await require_admin_callback(callback, settings):
        return

    ticket_id = int(callback.data.split(":")[-1])
    ticket = SupportTicketRepository().get_ticket(ticket_id)
    if ticket is None:
        await callback.answer("Обращение не найдено.", show_alert=True)
        return

    if ticket.related_order_id is None:
        await callback.answer("У клиента пока нет заказов.", show_alert=True)
        return

    order = OrderRepository().get_order(ticket.related_order_id)
    if order is None:
        await callback.answer("У клиента пока нет заказов.", show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(
        format_admin_order(order),
        reply_markup=support_order_back_keyboard(ticket.id),
    )


@router.callback_query(F.data.startswith("support:close:"))
async def close_support_ticket(callback: CallbackQuery, settings: Settings) -> None:
    if not await require_admin_callback(callback, settings):
        return

    ticket_id = int(callback.data.split(":")[-1])
    repository = SupportTicketRepository()
    ticket = repository.update_status(ticket_id, STATUS_CLOSED)
    if ticket is None:
        await callback.answer("Обращение не найдено.", show_alert=True)
        return

    logger.info("Обращение №%s закрыто", ticket.id)

    await callback.message.edit_text(
        f"✅ Обращение #{ticket.id} закрыто.",
        reply_markup=None,
    )
    await callback.answer()
