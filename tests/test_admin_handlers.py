import asyncio
from types import SimpleNamespace

from database.orders import (
    Order,
    PRODUCT_STARS,
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_PENDING_REVIEW,
)
from handlers.admin import (
    admin_cancel_order,
    admin_command,
    admin_complete_order,
    admin_confirm_complete_order,
    admin_list_orders,
)


def make_order(status):
    return Order(
        id=7,
        user_id=123,
        username="client",
        product_type=PRODUCT_STARS,
        stars_amount=50,
        premium_months=None,
        telegram_username="@receiver",
        price_rub=65,
        status=status,
        created_at="2026-06-24 00:00:00",
    )


class FakeRepository:
    def __init__(self):
        pass

    def update_status(self, order_id, status):
        assert order_id == 7
        return make_order(status)


class FakeBot:
    def __init__(self):
        self.messages = []

    async def send_message(self, chat_id, text, reply_markup=None):
        self.messages.append(
            {
                "chat_id": chat_id,
                "text": text,
                "reply_markup": reply_markup,
            }
        )


class FakeMessage:
    def __init__(self):
        self.edits = []
        self.answers = []

    async def edit_text(self, text, reply_markup=None):
        self.edits.append({"text": text, "reply_markup": reply_markup})

    async def answer(self, text, reply_markup=None):
        self.answers.append({"text": text, "reply_markup": reply_markup})


class FakeCommandMessage(FakeMessage):
    def __init__(self, user_id=999):
        super().__init__()
        self.from_user = SimpleNamespace(id=user_id)


class FakeCallback:
    def __init__(self, data):
        self.data = data
        self.from_user = SimpleNamespace(id=999)
        self.bot = FakeBot()
        self.message = FakeMessage()
        self.answers = []

    async def answer(self, text=None, show_alert=None):
        self.answers.append({"text": text, "show_alert": show_alert})


class FakeListRepository:
    def __init__(self):
        pass

    def list_orders(self, status=None, limit=10):
        assert status == STATUS_PENDING_REVIEW
        assert limit == 10
        return [make_order(STATUS_PENDING_REVIEW)]


class ConfirmationOnlyRepository:
    def get_order(self, order_id):
        assert order_id == 7
        return make_order(STATUS_PENDING_REVIEW)

    def update_status(self, order_id, status):
        raise AssertionError("Статус нельзя менять до подтверждения")


def test_admin_command_shows_owner_panel():
    message = FakeCommandMessage(user_id=999)
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(admin_command(message, settings))

    sent = message.answers[0]
    assert sent["text"] == "🛠 Админ-панель StarDrop\n\nВыберите список заказов."
    assert sent["reply_markup"].inline_keyboard[0][0].callback_data == "admin:list:pending_review"


def test_admin_command_denies_non_admin_user():
    message = FakeCommandMessage(user_id=111)
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(admin_command(message, settings))

    assert message.answers[0]["text"] == "⛔ Доступ запрещен."


def test_admin_pending_orders_callback_shows_filtered_orders(monkeypatch):
    monkeypatch.setattr("handlers.admin.OrderRepository", FakeListRepository)
    callback = FakeCallback("admin:list:pending_review")
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(admin_list_orders(callback, settings))

    edit = callback.message.edits[0]
    assert "🟠 Заказы на проверке" in edit["text"]
    assert "#7 · Telegram Stars" in edit["text"]
    assert edit["reply_markup"].inline_keyboard[0][0].callback_data == "admin:complete:7"
    assert callback.answers[0]["text"] is None


def test_admin_complete_button_only_opens_confirmation(monkeypatch):
    monkeypatch.setattr("handlers.admin.OrderRepository", ConfirmationOnlyRepository)
    callback = FakeCallback("admin:complete:7")
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(admin_complete_order(callback, settings))

    edit = callback.message.edits[0]
    assert edit["text"] == "Подтвердить выполнение заказа №7?"
    assert edit["reply_markup"].inline_keyboard[0][0].callback_data == "admin:confirm_complete:7"
    assert edit["reply_markup"].inline_keyboard[0][1].text == "↩️ Назад"


def test_admin_completed_order_message_has_main_menu_and_orders(monkeypatch):
    monkeypatch.setattr("handlers.admin.OrderRepository", FakeRepository)
    callback = FakeCallback("admin:confirm_complete:7")
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(admin_confirm_complete_order(callback, settings))

    sent = callback.bot.messages[0]
    buttons = sent["reply_markup"].inline_keyboard

    assert sent["chat_id"] == 123
    assert sent["text"].startswith("✅ Заказ выполнен")
    assert buttons[0][0].text == "📦 Мои заказы"
    assert buttons[1][0].text == "🏠 Главное меню"
    assert callback.answers[-1]["text"] == "Готово."


def test_admin_cancelled_order_message_has_main_menu_and_support(monkeypatch):
    monkeypatch.setattr("handlers.admin.OrderRepository", FakeRepository)
    callback = FakeCallback("admin:cancel:7")
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(admin_cancel_order(callback, settings))

    sent = callback.bot.messages[0]
    buttons = sent["reply_markup"].inline_keyboard

    assert sent["chat_id"] == 123
    assert sent["text"] == (
        "❌ Заказ отменен\n\n"
        "Если вы оплатили заказ случайно, напишите в поддержку."
    )
    assert buttons[0][0].text == "💬 Поддержка"
    assert buttons[1][0].text == "🏠 Главное меню"
    assert callback.answers[-1]["text"] == "Отменено."
