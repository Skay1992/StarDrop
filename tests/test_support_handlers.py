import asyncio
from types import SimpleNamespace

from database.orders import Order, PRODUCT_STARS, STATUS_PENDING_REVIEW
from database.support import STATUS_ANSWERED, STATUS_CLOSED, STATUS_OPEN, SupportTicket
from handlers.states import SupportAdminState
from handlers.support import (
    admin_support_list,
    admin_support_menu,
    admin_view_ticket,
    close_support_ticket,
    open_related_order,
    send_support_reply,
    start_support_reply,
    submit_support_ticket,
    support_tickets_command,
    view_own_ticket,
)


def make_ticket(
    status=STATUS_OPEN,
    related_order_id=42,
    admin_reply=None,
    answered_at=None,
    ticket_id=7,
    username="client",
):
    return SupportTicket(
        id=ticket_id,
        user_id=123,
        username=username,
        message="Когда придут звезды?",
        related_order_id=related_order_id,
        status=status,
        admin_reply=admin_reply,
        created_at="2026-06-29 12:00:00",
        answered_at=answered_at,
    )


def make_order():
    return Order(
        id=42,
        user_id=123,
        username="client",
        product_type=PRODUCT_STARS,
        stars_amount=50,
        premium_months=None,
        telegram_username="@receiver",
        price_rub=65,
        status=STATUS_PENDING_REVIEW,
        created_at="2026-06-29 11:00:00",
    )


class FakeRepository:
    created = None

    def create_ticket_if_no_open(self, user_id, username, message, related_order_id=None):
        FakeRepository.created = (user_id, username, message, related_order_id)
        return make_ticket(related_order_id=related_order_id), True


class FakeOrderRepository:
    def list_user_orders(self, user_id, limit=5):
        assert user_id == 123
        assert limit == 1
        return [make_order()]

    def get_order(self, order_id):
        assert order_id == 42
        return make_order()


class FakeDuplicateRepository:
    def create_ticket_if_no_open(self, user_id, username, message, related_order_id=None):
        return make_ticket(), False


class FakeNoOrderTicketRepository:
    def get_ticket(self, ticket_id):
        assert ticket_id == 7
        return make_ticket(related_order_id=None)


class FakeAdminRepository:
    updated = None
    listed_statuses = None
    listed_limit = None
    listed_offset = None

    def get_ticket(self, ticket_id):
        assert ticket_id == 7
        return make_ticket()

    def update_status(self, ticket_id, status):
        FakeAdminRepository.updated = (ticket_id, status)
        return make_ticket(status)

    def answer_ticket(self, ticket_id, admin_reply):
        FakeAdminRepository.updated = (ticket_id, admin_reply)
        return make_ticket(
            STATUS_ANSWERED,
            admin_reply=admin_reply,
            answered_at="2026-06-29 12:05:00",
        )

    def list_tickets(self, status=None, statuses=None, limit=10, offset=0):
        FakeAdminRepository.listed_statuses = statuses or ((status,) if status else None)
        FakeAdminRepository.listed_limit = limit
        FakeAdminRepository.listed_offset = offset
        return [make_ticket()]


class PagedAdminRepository:
    calls = []

    def list_tickets(self, status=None, statuses=None, limit=10, offset=0):
        PagedAdminRepository.calls.append(
            {"statuses": statuses, "limit": limit, "offset": offset}
        )
        tickets = [
            make_ticket(ticket_id=ticket_id, username=f"client{ticket_id}")
            for ticket_id in range(11, 0, -1)
        ]
        return tickets[offset : offset + limit]


class ClosingAdminRepository(FakeAdminRepository):
    def list_tickets(self, status=None, statuses=None, limit=10, offset=0):
        assert statuses == (STATUS_OPEN,)
        return [make_ticket(ticket_id=8, username="waiting")]


class FakeState:
    def __init__(self):
        self.cleared = False
        self.data = {}
        self.current_state = None

    async def clear(self):
        self.cleared = True

    async def update_data(self, **kwargs):
        self.data.update(kwargs)

    async def set_state(self, state):
        self.current_state = state

    async def get_data(self):
        return self.data


class FakeBot:
    def __init__(self):
        self.messages = []

    async def send_message(self, chat_id, text, reply_markup=None):
        self.messages.append({"chat_id": chat_id, "text": text, "reply_markup": reply_markup})


class FakeMessage:
    def __init__(self, text="Когда придут звезды?", user_id=123, username="client"):
        self.text = text
        self.from_user = SimpleNamespace(id=user_id, username=username)
        self.bot = FakeBot()
        self.answers = []
        self.edits = []

    async def answer(self, text, reply_markup=None):
        self.answers.append({"text": text, "reply_markup": reply_markup})

    async def edit_text(self, text, reply_markup=None):
        self.edits.append({"text": text, "reply_markup": reply_markup})


class FakeCallback:
    def __init__(self, data="support:reply:7", user_id=999):
        self.data = data
        self.from_user = SimpleNamespace(id=user_id)
        self.message = FakeMessage()
        self.answers = []

    async def answer(self, text=None, show_alert=None):
        self.answers.append({"text": text, "show_alert": show_alert})


def test_user_message_creates_ticket_and_notifies_admin(monkeypatch):
    monkeypatch.setattr("handlers.support.SupportTicketRepository", FakeRepository)
    monkeypatch.setattr("handlers.support.OrderRepository", FakeOrderRepository)
    message = FakeMessage()
    state = FakeState()
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(submit_support_ticket(message, state, settings))

    assert FakeRepository.created == (123, "client", "Когда придут звезды?", 42)
    assert state.cleared
    assert message.answers[0]["text"] == (
        "✅ Вопрос отправлен\n\n"
        "Мы ответим как можно быстрее."
    )
    assert message.answers[0]["reply_markup"].inline_keyboard[0][0].text == "🏠 Главное меню"

    admin_message = message.bot.messages[0]
    assert admin_message["chat_id"] == 999
    assert admin_message["text"] == (
        "🔔 Новое обращение #7\n\n"
        "👤 Клиент:\n"
        "@client\n\n"
        "ID:\n"
        "123\n\n"
        "📦 Последний заказ:\n"
        "#42\n"
        "Telegram Stars / 65 ₽ / 🟠 Проверяем оплату\n\n"
        "Сообщение:\n"
        "Когда придут звезды?"
    )
    buttons = [
        button
        for row in admin_message["reply_markup"].inline_keyboard
        for button in row
    ]
    assert [(button.text, button.callback_data) for button in buttons] == [
        ("✉️ Ответить", "support:reply:7"),
        ("📦 Открыть заказ", "support:order:7"),
        ("✅ Закрыть", "support:close:7"),
    ]


def test_support_rejects_non_text_message_without_losing_navigation(monkeypatch):
    monkeypatch.setattr("handlers.support.SupportTicketRepository", FakeRepository)
    message = FakeMessage(text=None)
    state = FakeState()
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(submit_support_ticket(message, state, settings))

    assert not state.cleared
    assert message.answers[0]["text"] == "Отправьте вопрос текстовым сообщением."
    assert message.answers[0]["reply_markup"].inline_keyboard[0][0].text == "🏠 Главное меню"
    assert not message.bot.messages


def test_user_cannot_create_second_open_ticket(monkeypatch):
    monkeypatch.setattr("handlers.support.SupportTicketRepository", FakeDuplicateRepository)
    monkeypatch.setattr("handlers.support.OrderRepository", FakeOrderRepository)
    message = FakeMessage(text="Еще один вопрос")
    state = FakeState()
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(submit_support_ticket(message, state, settings))

    assert state.cleared
    assert message.answers[0]["text"] == (
        "У вас уже есть открытое обращение.\n"
        "Дождитесь ответа поддержки."
    )
    assert [row[0].text for row in message.answers[0]["reply_markup"].inline_keyboard] == [
        "👀 Посмотреть обращение",
        "🏠 Главное меню",
    ]
    assert not message.bot.messages


def test_user_can_view_existing_open_ticket(monkeypatch):
    monkeypatch.setattr("handlers.support.SupportTicketRepository", FakeAdminRepository)
    callback = FakeCallback(data="support:mine:7", user_id=123)

    asyncio.run(view_own_ticket(callback))

    assert callback.answers
    assert callback.message.edits[0]["text"] == (
        "💬 Обращение #7\n\n"
        "Статус: 🟠 Открыто\n\n"
        "Сообщение:\n"
        "Когда придут звезды?"
    )
    assert callback.message.edits[0]["reply_markup"].inline_keyboard[0][0].text == (
        "🏠 Главное меню"
    )


def test_admin_reply_button_opens_reply_fsm(monkeypatch):
    monkeypatch.setattr("handlers.support.SupportTicketRepository", FakeAdminRepository)
    callback = FakeCallback()
    state = FakeState()
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(start_support_reply(callback, state, settings))

    assert callback.answers
    assert state.data == {"support_ticket_id": 7}
    assert state.current_state == SupportAdminState.reply
    assert callback.message.answers[0]["text"] == "Введите ответ клиенту"


def test_admin_reply_is_sent_to_client_and_marks_ticket_answered(monkeypatch):
    monkeypatch.setattr("handlers.support.SupportTicketRepository", FakeAdminRepository)
    message = FakeMessage(text="Звезды уже отправлены.", user_id=999, username="owner")
    state = FakeState()
    state.data = {"support_ticket_id": 7}
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(send_support_reply(message, state, settings))

    assert FakeAdminRepository.updated == (7, "Звезды уже отправлены.")
    assert state.cleared
    client_message = message.bot.messages[0]
    assert client_message["chat_id"] == 123
    assert client_message["text"] == (
        "💬 Ответ поддержки StarDrop\n\n"
        "Звезды уже отправлены."
    )
    assert [row[0].text for row in client_message["reply_markup"].inline_keyboard] == [
        "💬 Ответить ещё",
        "🏠 Главное меню",
    ]
    assert message.answers[0]["text"] == "Ответ отправлен."


def test_admin_reply_requires_text_message(monkeypatch):
    monkeypatch.setattr("handlers.support.SupportTicketRepository", FakeAdminRepository)
    message = FakeMessage(text=None, user_id=999, username="owner")
    state = FakeState()
    state.data = {"support_ticket_id": 7}
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(send_support_reply(message, state, settings))

    assert not state.cleared
    assert message.answers[0]["text"] == "Отправьте ответ текстовым сообщением."
    assert not message.bot.messages


def test_admin_can_close_support_ticket(monkeypatch):
    monkeypatch.setattr(
        "handlers.support.SupportTicketRepository",
        ClosingAdminRepository,
    )
    callback = FakeCallback(data="support:close:7")
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(close_support_ticket(callback, settings))

    assert FakeAdminRepository.updated == (7, STATUS_CLOSED)
    assert callback.message.edits[0]["text"].startswith("🟠 Открытые обращения")
    assert "#7" not in callback.message.edits[0]["text"]
    assert "#8 — @waiting" in callback.message.edits[0]["text"]
    assert callback.answers[-1] == {
        "text": "Обращение #7 закрыто.",
        "show_alert": None,
    }


def test_admin_can_open_order_linked_to_ticket(monkeypatch):
    monkeypatch.setattr("handlers.support.SupportTicketRepository", FakeAdminRepository)
    monkeypatch.setattr("handlers.support.OrderRepository", FakeOrderRepository)
    callback = FakeCallback(data="support:order:7")
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(open_related_order(callback, settings))

    edit = callback.message.edits[0]
    assert "🆕 Заказ №42" in edit["text"]
    assert "⭐ Telegram Stars" in edit["text"]
    assert edit["reply_markup"].inline_keyboard[0][0].text == "↩️ К обращению"
    assert edit["reply_markup"].inline_keyboard[0][0].callback_data == "support:admin:view:7"


def test_open_order_reports_when_client_has_no_orders(monkeypatch):
    monkeypatch.setattr("handlers.support.SupportTicketRepository", FakeNoOrderTicketRepository)
    callback = FakeCallback(data="support:order:7")
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(open_related_order(callback, settings))

    assert callback.answers[0] == {
        "text": "У клиента пока нет заказов.",
        "show_alert": True,
    }
    assert not callback.message.edits


def test_admin_can_list_last_support_tickets(monkeypatch):
    monkeypatch.setattr("handlers.support.SupportTicketRepository", FakeAdminRepository)
    message = FakeMessage(user_id=999, username="owner")
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(support_tickets_command(message, settings))

    assert message.answers[0]["text"] == (
        "💬 Последние обращения\n\n"
        "#7 — @client\n"
        "Статус: 🟠 Открыто\n"
        "Сообщение: Когда придут звезды?\n"
        "Дата: 2026-06-29 12:00:00"
    )


def test_admin_support_section_shows_open_tickets_by_default(monkeypatch):
    monkeypatch.setattr("handlers.support.SupportTicketRepository", FakeAdminRepository)
    callback = FakeCallback(data="admin:support")
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(admin_support_menu(callback, settings))

    assert callback.answers
    assert FakeAdminRepository.listed_statuses == (STATUS_OPEN,)
    assert callback.message.edits[0]["text"].startswith("🟠 Открытые обращения")
    button_texts = [
        button.text
        for row in callback.message.edits[0]["reply_markup"].inline_keyboard
        for button in row
    ]
    assert button_texts == [
        "💬 #7 — @client",
        "🟠 Открытые",
        "📂 Архив",
        "📋 Все",
        "↩️ Админ меню",
        "🏠 Главное меню",
    ]


def test_admin_can_filter_and_open_support_tickets(monkeypatch):
    monkeypatch.setattr("handlers.support.SupportTicketRepository", FakeAdminRepository)
    callback = FakeCallback(data="admin:support:list:open")
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(admin_support_list(callback, settings))

    assert FakeAdminRepository.listed_statuses == (STATUS_OPEN,)
    edit = callback.message.edits[0]
    assert edit["text"].startswith("🟠 Открытые обращения")
    assert "#7 — @client" in edit["text"]
    assert edit["reply_markup"].inline_keyboard[0][0].callback_data == "support:admin:view:7"
    assert edit["reply_markup"].inline_keyboard[-2][0].text == "↩️ Админ меню"
    assert edit["reply_markup"].inline_keyboard[-1][0].text == "🏠 Главное меню"


def test_admin_support_archive_combines_answered_and_closed(monkeypatch):
    monkeypatch.setattr("handlers.support.SupportTicketRepository", FakeAdminRepository)
    callback = FakeCallback(data="admin:support:list:archive")
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(admin_support_list(callback, settings))

    assert FakeAdminRepository.listed_statuses == (STATUS_ANSWERED, STATUS_CLOSED)
    assert callback.message.edits[0]["text"].startswith("📂 Архив обращений")


def test_admin_support_list_is_paginated_by_ten_tickets(monkeypatch):
    PagedAdminRepository.calls = []
    monkeypatch.setattr("handlers.support.SupportTicketRepository", PagedAdminRepository)
    settings = SimpleNamespace(admin_id=999)

    first_page = FakeCallback(data="admin:support:list:open:0")
    asyncio.run(admin_support_list(first_page, settings))

    first_buttons = [
        button
        for row in first_page.message.edits[0]["reply_markup"].inline_keyboard
        for button in row
    ]
    ticket_buttons = [button for button in first_buttons if button.text.startswith("💬")]
    assert len(ticket_buttons) == 10
    assert ticket_buttons[0].text == "💬 #11 — @client11"
    assert ticket_buttons[-1].text == "💬 #2 — @client2"
    assert any(
        button.text == "➡️ Вперёд"
        and button.callback_data == "admin:support:list:open:1"
        for button in first_buttons
    )

    second_page = FakeCallback(data="admin:support:list:open:1")
    asyncio.run(admin_support_list(second_page, settings))

    second_buttons = [
        button
        for row in second_page.message.edits[0]["reply_markup"].inline_keyboard
        for button in row
    ]
    assert [button.text for button in second_buttons if button.text.startswith("💬")] == [
        "💬 #1 — @client1"
    ]
    assert any(
        button.text == "⬅️ Назад"
        and button.callback_data == "admin:support:list:open:0"
        for button in second_buttons
    )
    assert PagedAdminRepository.calls == [
        {"statuses": (STATUS_OPEN,), "limit": 11, "offset": 0},
        {"statuses": (STATUS_OPEN,), "limit": 11, "offset": 10},
    ]


def test_admin_can_open_support_ticket_card(monkeypatch):
    monkeypatch.setattr("handlers.support.SupportTicketRepository", FakeAdminRepository)
    monkeypatch.setattr("handlers.support.OrderRepository", FakeOrderRepository)
    callback = FakeCallback(data="support:admin:view:7")
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(admin_view_ticket(callback, settings))

    edit = callback.message.edits[0]
    assert edit["text"].startswith("💬 Обращение #7")
    assert "📦 Последний заказ:\n#42" in edit["text"]
    assert "Статус: 🟠 Открыто" in edit["text"]
    buttons = [button for row in edit["reply_markup"].inline_keyboard for button in row]
    assert buttons[0].callback_data == "support:reply:7"
    assert buttons[1].callback_data == "support:order:7"


def test_support_admin_actions_are_denied_for_regular_user():
    settings = SimpleNamespace(admin_id=999)
    state = FakeState()
    reply_callback = FakeCallback(data="support:reply:7", user_id=111)
    close_callback = FakeCallback(data="support:close:7", user_id=111)
    order_callback = FakeCallback(data="support:order:7", user_id=111)
    ticket_callback = FakeCallback(data="support:admin:view:7", user_id=111)
    menu_callback = FakeCallback(data="admin:support", user_id=111)
    list_callback = FakeCallback(data="admin:support:list:open", user_id=111)
    command_message = FakeMessage(user_id=111, username="client")

    asyncio.run(start_support_reply(reply_callback, state, settings))
    asyncio.run(close_support_ticket(close_callback, settings))
    asyncio.run(open_related_order(order_callback, settings))
    asyncio.run(admin_view_ticket(ticket_callback, settings))
    asyncio.run(admin_support_menu(menu_callback, settings))
    asyncio.run(admin_support_list(list_callback, settings))
    asyncio.run(support_tickets_command(command_message, settings))

    assert reply_callback.answers[0] == {"text": None, "show_alert": None}
    assert close_callback.answers[0] == {"text": None, "show_alert": None}
    for callback in (order_callback, ticket_callback, menu_callback, list_callback):
        assert callback.answers[0] == {"text": None, "show_alert": None}
    assert command_message.answers[0]["text"] == "⛔ Доступ запрещен."
    assert state.current_state is None
