import asyncio
from types import SimpleNamespace

from database.orders import (
    Order,
    PRODUCT_STARS,
    STATUS_CANCELLED,
    STATUS_COMPLETED,
)
from handlers.admin import admin_cancel_order, admin_confirm_complete_order


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

    async def edit_text(self, text, reply_markup=None):
        self.edits.append({"text": text, "reply_markup": reply_markup})


class FakeCallback:
    def __init__(self, data):
        self.data = data
        self.from_user = SimpleNamespace(id=999)
        self.bot = FakeBot()
        self.message = FakeMessage()
        self.answers = []

    async def answer(self, text=None, show_alert=None):
        self.answers.append({"text": text, "show_alert": show_alert})


def test_admin_completed_order_message_has_main_menu_and_orders(monkeypatch):
    monkeypatch.setattr("handlers.admin.OrderRepository", FakeRepository)
    callback = FakeCallback("admin:confirm_complete:7")
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(admin_confirm_complete_order(callback, settings))

    sent = callback.bot.messages[0]
    buttons = sent["reply_markup"].inline_keyboard

    assert sent["chat_id"] == 123
    assert sent["text"].startswith("✅ Заказ выполнен")
    assert buttons[0][0].text == "🏠 Главное меню"
    assert buttons[1][0].text == "📦 Мои заказы"
    assert callback.answers[-1]["text"] == "Готово."


def test_admin_cancelled_order_message_has_main_menu_and_support(monkeypatch):
    monkeypatch.setattr("handlers.admin.OrderRepository", FakeRepository)
    callback = FakeCallback("admin:cancel:7")
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(admin_cancel_order(callback, settings))

    sent = callback.bot.messages[0]
    buttons = sent["reply_markup"].inline_keyboard

    assert sent["chat_id"] == 123
    assert sent["text"] == "Заказ отменен.\nОбратитесь в поддержку."
    assert buttons[0][0].text == "🏠 Главное меню"
    assert buttons[1][0].text == "💬 Поддержка"
    assert callback.answers[-1]["text"] == "Отменено."
