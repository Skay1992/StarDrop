from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config.settings import Settings
from database.support import (
    STATUS_ANSWERED,
    STATUS_CLOSED,
    STATUS_OPEN,
    SupportTicket,
    SupportTicketRepository,
)
from handlers.callbacks import answer_callback, log_callback
from handlers.states import SupportAdminState, SupportUserState
from keyboards.callbacks import LEGACY_SUPPORT, SUPPORT
from keyboards.main import home_menu_keyboard
from keyboards.support import support_answer_keyboard, support_ticket_admin_keyboard


router = Router()

SUPPORT_TEXT = (
    "💬 Поддержка StarDrop\n\n"
    "Напишите ваш вопрос одним сообщением.\n"
    "Мы ответим как можно быстрее."
)

SUPPORT_STATUS_LABELS = {
    STATUS_OPEN: "🟡 Новое",
    STATUS_ANSWERED: "🟢 Ответ дан",
    STATUS_CLOSED: "⚫ Закрыто",
}
MAX_SUPPORT_MESSAGE_LENGTH = 3000


def format_admin_ticket(ticket: SupportTicket) -> str:
    username = f"@{ticket.username}" if ticket.username else "не указан"
    return (
        f"💬 Новое обращение №{ticket.id}\n\n"
        "Клиент:\n"
        f"{username}\n\n"
        "ID:\n"
        f"{ticket.user_id}\n\n"
        "Сообщение:\n"
        f"{ticket.message}"
    )


def format_support_tickets(tickets) -> str:
    tickets = list(tickets)
    if not tickets:
        return "💬 Последние обращения\n\nОбращений пока нет."

    lines = ["💬 Последние обращения"]
    for ticket in tickets:
        username = f"@{ticket.username}" if ticket.username else f"ID {ticket.user_id}"
        message_preview = " ".join(ticket.message.split())
        if len(message_preview) > 200:
            message_preview = f"{message_preview[:197]}..."
        lines.extend(
            [
                "",
                f"#{ticket.id} — {username}",
                f"Статус: {SUPPORT_STATUS_LABELS.get(ticket.status, '⚪ Неизвестен')}",
                f"Сообщение: {message_preview}",
                f"Дата: {ticket.created_at}",
            ]
        )
    return "\n".join(lines)


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

    repository = SupportTicketRepository()
    ticket = repository.create_ticket(
        user_id=message.from_user.id,
        username=message.from_user.username,
        message=support_message,
    )
    await state.clear()
    await message.answer(
        "✅ Вопрос отправлен\n\nМы ответим как можно быстрее.",
        reply_markup=home_menu_keyboard(),
    )
    await message.bot.send_message(
        chat_id=settings.admin_id,
        text=format_admin_ticket(ticket),
        reply_markup=support_ticket_admin_keyboard(ticket.id),
    )


@router.callback_query(F.data.startswith("support:reply:"))
async def start_support_reply(
    callback: CallbackQuery,
    state: FSMContext,
    settings: Settings,
) -> None:
    if callback.from_user.id != settings.admin_id:
        await callback.answer("⛔ Доступ запрещен.", show_alert=True)
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
    await callback.message.answer(
        f"Введите ответ для обращения №{ticket.id} одним сообщением."
    )


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
    repository.update_status(ticket.id, STATUS_ANSWERED)
    await state.clear()
    await message.answer("Ответ отправлен.")


@router.callback_query(F.data.startswith("support:close:"))
async def close_support_ticket(callback: CallbackQuery, settings: Settings) -> None:
    if callback.from_user.id != settings.admin_id:
        await callback.answer("⛔ Доступ запрещен.", show_alert=True)
        return

    ticket_id = int(callback.data.split(":")[-1])
    repository = SupportTicketRepository()
    ticket = repository.update_status(ticket_id, STATUS_CLOSED)
    if ticket is None:
        await callback.answer("Обращение не найдено.", show_alert=True)
        return

    await callback.message.edit_text(
        f"{format_admin_ticket(ticket)}\n\nСтатус:\n⚫ Закрыто",
        reply_markup=None,
    )
    await callback.answer("Обращение закрыто.")
