import asyncio
from types import SimpleNamespace

from database.orders import (
    Order,
    PRODUCT_STARS,
    STATUS_AWAITING_PAYMENT,
    STATUS_CANCELLED,
    STATUS_PENDING_REVIEW,
)
from handlers.orders import order_cancel, order_paid


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
    def get_order(self, order_id):
        assert order_id == 7
        return make_order(STATUS_AWAITING_PAYMENT)

    def update_status(self, order_id, status):
        assert order_id == 7
        return make_order(status)

    def transition_status(self, order_id, expected_status, new_status):
        assert order_id == 7
        return make_order(new_status)


class AlreadyPaidRepository(FakeRepository):
    def get_order(self, order_id):
        return make_order(STATUS_PENDING_REVIEW)


class FakeMessage:
    def __init__(self):
        self.edits = []

    async def edit_text(self, text, reply_markup=None):
        self.edits.append({"text": text, "reply_markup": reply_markup})


class FakeBot:
    def __init__(self):
        self.messages = []

    async def send_message(self, chat_id, text, reply_markup=None):
        self.messages.append({"chat_id": chat_id, "text": text, "reply_markup": reply_markup})


class FakeCallback:
    def __init__(self, data="order:paid:7"):
        self.data = data
        self.from_user = SimpleNamespace(id=123)
        self.message = FakeMessage()
        self.bot = FakeBot()
        self.answers = []

    async def answer(self, text=None, show_alert=None):
        self.answers.append({"text": text, "show_alert": show_alert})


def test_paid_order_shows_review_message_with_orders_and_home_buttons(monkeypatch):
    monkeypatch.setattr("handlers.orders.OrderRepository", FakeRepository)
    callback = FakeCallback()
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(order_paid(callback, settings))

    edit = callback.message.edits[0]
    assert edit["text"] == (
        "✅ Спасибо!\n\n"
        "Заказ №7 отправлен на проверку.\n"
        "Мы уведомим вас после выполнения."
    )
    assert [row[0].text for row in edit["reply_markup"].inline_keyboard] == [
        "📦 Мои заказы",
        "🏠 Главное меню",
    ]


def test_repeated_paid_callback_reports_that_notification_was_received(monkeypatch):
    monkeypatch.setattr("handlers.orders.OrderRepository", AlreadyPaidRepository)
    callback = FakeCallback()
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(order_paid(callback, settings))

    assert callback.answers == [
        {
            "text": "Мы уже получили уведомление об оплате.\n\nОжидайте проверки.",
            "show_alert": True,
        }
    ]
    assert not callback.message.edits
    assert not callback.bot.messages


def test_cancelled_order_shows_support_and_home_buttons(monkeypatch):
    monkeypatch.setattr("handlers.orders.OrderRepository", FakeRepository)
    callback = FakeCallback("order:cancel:7")

    asyncio.run(order_cancel(callback))

    edit = callback.message.edits[0]
    assert edit["text"] == (
        "❌ Заказ отменен\n\n"
        "Если вы оплатили заказ случайно, напишите в поддержку."
    )
    assert [row[0].text for row in edit["reply_markup"].inline_keyboard] == [
        "💬 Поддержка",
        "🏠 Главное меню",
    ]
    assert make_order(STATUS_CANCELLED).status == STATUS_CANCELLED
