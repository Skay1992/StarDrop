import asyncio
from types import SimpleNamespace

from database.support import STATUS_ANSWERED, STATUS_CLOSED, STATUS_OPEN, SupportTicket
from handlers.states import SupportAdminState
from handlers.support import (
    close_support_ticket,
    send_support_reply,
    start_support_reply,
    submit_support_ticket,
    support_tickets_command,
)


def make_ticket(status=STATUS_OPEN):
    return SupportTicket(
        id=7,
        user_id=123,
        username="client",
        message="Когда придут звезды?",
        status=status,
        created_at="2026-06-29 12:00:00",
    )


class FakeRepository:
    created = None

    def create_ticket(self, user_id, username, message):
        FakeRepository.created = (user_id, username, message)
        return make_ticket()


class FakeAdminRepository:
    updated = None

    def get_ticket(self, ticket_id):
        assert ticket_id == 7
        return make_ticket()

    def update_status(self, ticket_id, status):
        FakeAdminRepository.updated = (ticket_id, status)
        return make_ticket(status)

    def list_tickets(self, limit=10):
        assert limit == 10
        return [make_ticket()]


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
    message = FakeMessage()
    state = FakeState()
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(submit_support_ticket(message, state, settings))

    assert FakeRepository.created == (123, "client", "Когда придут звезды?")
    assert state.cleared
    assert message.answers[0]["text"] == (
        "✅ Вопрос отправлен\n\n"
        "Мы ответим как можно быстрее."
    )
    assert message.answers[0]["reply_markup"].inline_keyboard[0][0].text == "🏠 Главное меню"

    admin_message = message.bot.messages[0]
    assert admin_message["chat_id"] == 999
    assert admin_message["text"] == (
        "💬 Новое обращение №7\n\n"
        "Клиент:\n"
        "@client\n\n"
        "ID:\n"
        "123\n\n"
        "Сообщение:\n"
        "Когда придут звезды?"
    )
    buttons = admin_message["reply_markup"].inline_keyboard[0]
    assert buttons[0].text == "✉️ Ответить"
    assert buttons[0].callback_data == "support:reply:7"
    assert buttons[1].text == "✅ Закрыть"
    assert buttons[1].callback_data == "support:close:7"


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


def test_admin_reply_button_opens_reply_fsm(monkeypatch):
    monkeypatch.setattr("handlers.support.SupportTicketRepository", FakeAdminRepository)
    callback = FakeCallback()
    state = FakeState()
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(start_support_reply(callback, state, settings))

    assert callback.answers
    assert state.data == {"support_ticket_id": 7}
    assert state.current_state == SupportAdminState.reply
    assert callback.message.answers[0]["text"] == (
        "Введите ответ для обращения №7 одним сообщением."
    )


def test_admin_reply_is_sent_to_client_and_marks_ticket_answered(monkeypatch):
    monkeypatch.setattr("handlers.support.SupportTicketRepository", FakeAdminRepository)
    message = FakeMessage(text="Звезды уже отправлены.", user_id=999, username="owner")
    state = FakeState()
    state.data = {"support_ticket_id": 7}
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(send_support_reply(message, state, settings))

    assert FakeAdminRepository.updated == (7, STATUS_ANSWERED)
    assert state.cleared
    client_message = message.bot.messages[0]
    assert client_message["chat_id"] == 123
    assert client_message["text"] == (
        "💬 Ответ поддержки StarDrop\n\n"
        "Звезды уже отправлены."
    )
    assert [row[0].text for row in client_message["reply_markup"].inline_keyboard] == [
        "💬 Задать ещё вопрос",
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
    monkeypatch.setattr("handlers.support.SupportTicketRepository", FakeAdminRepository)
    callback = FakeCallback(data="support:close:7")
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(close_support_ticket(callback, settings))

    assert FakeAdminRepository.updated == (7, STATUS_CLOSED)
    assert callback.answers[-1]["text"] == "Обращение закрыто."
    assert callback.message.edits[0]["text"].endswith("Статус:\n⚫ Закрыто")
    assert callback.message.edits[0]["reply_markup"] is None


def test_admin_can_list_last_support_tickets(monkeypatch):
    monkeypatch.setattr("handlers.support.SupportTicketRepository", FakeAdminRepository)
    message = FakeMessage(user_id=999, username="owner")
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(support_tickets_command(message, settings))

    assert message.answers[0]["text"] == (
        "💬 Последние обращения\n\n"
        "#7 — @client\n"
        "Статус: 🟡 Новое\n"
        "Сообщение: Когда придут звезды?\n"
        "Дата: 2026-06-29 12:00:00"
    )


def test_support_admin_actions_are_denied_for_regular_user():
    settings = SimpleNamespace(admin_id=999)
    state = FakeState()
    reply_callback = FakeCallback(data="support:reply:7", user_id=111)
    close_callback = FakeCallback(data="support:close:7", user_id=111)
    command_message = FakeMessage(user_id=111, username="client")

    asyncio.run(start_support_reply(reply_callback, state, settings))
    asyncio.run(close_support_ticket(close_callback, settings))
    asyncio.run(support_tickets_command(command_message, settings))

    assert reply_callback.answers[0] == {
        "text": "⛔ Доступ запрещен.",
        "show_alert": True,
    }
    assert close_callback.answers[0] == {
        "text": "⛔ Доступ запрещен.",
        "show_alert": True,
    }
    assert command_message.answers[0]["text"] == "⛔ Доступ запрещен."
    assert state.current_state is None
