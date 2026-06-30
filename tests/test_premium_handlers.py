import asyncio
from types import SimpleNamespace

import pytest

from database.orders import (
    Order,
    PRODUCT_PREMIUM,
    STATUS_AWAITING_PAYMENT,
)
from handlers.premium import (
    premium_month_unavailable,
    premium_months_selected,
    premium_username_entered,
)
from handlers.states import PremiumOrderState
from keyboards.callbacks import BUY_PREMIUM, MAIN_MENU


class FakeState:
    def __init__(self):
        self.data = {}
        self.current_state = "old-state"
        self.cleared = False

    async def update_data(self, **kwargs):
        self.data.update(kwargs)

    async def set_state(self, state):
        self.current_state = state

    async def get_data(self):
        return self.data

    async def clear(self):
        self.cleared = True
        self.data = {}
        self.current_state = None


class FakeMessage:
    def __init__(self, text=None):
        self.text = text
        self.from_user = SimpleNamespace(id=123, username="client")
        self.edits = []
        self.answers = []

    async def edit_text(self, text, reply_markup=None):
        self.edits.append({"text": text, "reply_markup": reply_markup})

    async def answer(self, text, reply_markup=None):
        self.answers.append({"text": text, "reply_markup": reply_markup})


class FakeCallback:
    def __init__(self, data):
        self.data = data
        self.message = FakeMessage()
        self.answers = []

    async def answer(self, text=None, show_alert=None):
        self.answers.append({"text": text, "show_alert": show_alert})


def assert_unavailable_screen(callback, state):
    assert callback.answers
    assert state.cleared
    assert callback.message.edits[0]["text"] == (
        "💎 Telegram Premium — 1 месяц\n\n"
        "Этот тариф пока недоступен.\n\n"
        "Сейчас можно оформить:\n\n"
        "🟢 3 месяца\n"
        "🟣 6 месяцев\n"
        "🟡 12 месяцев\n\n"
        "Мы работаем над добавлением Premium на 1 месяц ❤️"
    )
    buttons = [row[0] for row in callback.message.edits[0]["reply_markup"].inline_keyboard]
    assert [(button.text, button.callback_data) for button in buttons] == [
        ("💎 Выбрать другой срок", BUY_PREMIUM),
        ("🏠 Главное меню", MAIN_MENU),
    ]


def test_one_month_button_shows_coming_soon_without_starting_order():
    callback = FakeCallback("premium:soon:1")
    state = FakeState()

    asyncio.run(premium_month_unavailable(callback, state))

    assert_unavailable_screen(callback, state)


def test_old_one_month_callback_cannot_start_order():
    callback = FakeCallback("premium:months:1")
    state = FakeState()

    asyncio.run(premium_months_selected(callback, state))

    assert_unavailable_screen(callback, state)
    assert state.data == {}


@pytest.mark.parametrize(
    ("months", "price_rub"),
    [(3, 990), (6, 1690), (12, 2990)],
)
def test_available_premium_plan_creates_order(monkeypatch, months, price_rub):
    created_orders = []

    class FakeOrderRepository:
        def create_order_if_allowed(self, **kwargs):
            created_orders.append(kwargs)
            return (
                Order(
                    id=10,
                    user_id=kwargs["user_id"],
                    username=kwargs["username"],
                    product_type=kwargs["product_type"],
                    stars_amount=None,
                    premium_months=kwargs["premium_months"],
                    telegram_username=kwargs["telegram_username"],
                    price_rub=kwargs["price_rub"],
                    status=STATUS_AWAITING_PAYMENT,
                    created_at="2026-06-30 13:00:00",
                ),
                True,
            )

    monkeypatch.setattr("handlers.premium.OrderRepository", FakeOrderRepository)
    state = FakeState()
    callback = FakeCallback(f"premium:months:{months}")

    asyncio.run(premium_months_selected(callback, state))

    assert state.current_state == PremiumOrderState.telegram_username
    assert state.data == {"premium_months": months, "price_rub": price_rub}

    message = FakeMessage("@receiver")
    settings = SimpleNamespace(sbp_phone="+79990000000", sbp_name="Антон")
    asyncio.run(premium_username_entered(message, state, settings))

    assert len(created_orders) == 1
    assert created_orders[0] == {
        "user_id": 123,
        "username": "client",
        "product_type": PRODUCT_PREMIUM,
        "premium_months": months,
        "telegram_username": "@receiver",
        "price_rub": price_rub,
    }
    assert f"Срок:\n{months} мес." in message.answers[0]["text"]
    assert f"💰 К оплате:\n{price_rub} ₽" in message.answers[0]["text"]
