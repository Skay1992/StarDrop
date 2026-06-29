import asyncio

import pytest

from database.orders import Order, PRODUCT_STARS, STATUS_AWAITING_PAYMENT
from handlers.stars import (
    stars_amount_selected,
    stars_custom_amount_entered,
    stars_username_entered,
)


class FakeState:
    def __init__(self):
        self.data = {}
        self.current_state = None

    async def update_data(self, **kwargs):
        self.data.update(kwargs)

    async def set_state(self, state):
        self.current_state = state

    async def get_data(self):
        return self.data

    async def clear(self):
        self.current_state = None


class FakeMessage:
    def __init__(self, text=None):
        self.text = text
        self.from_user = type("User", (), {"id": 123, "username": "client"})()
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


def test_stars_amount_opens_recipient_screen_with_home_navigation():
    callback = FakeCallback("stars:amount:50")
    state = FakeState()

    asyncio.run(stars_amount_selected(callback, state))

    edit = callback.message.edits[0]
    assert edit["text"] == (
        "👤 Получатель\n\n"
        "Введите имя пользователя получателя.\n\n"
        "Например:\n"
        "@username\n\n"
        "👇 Отправьте имя пользователя сообщением."
    )
    assert edit["reply_markup"].inline_keyboard[0][0].text == "🏠 Главное меню"


def test_username_without_at_sign_shows_clear_error_with_home_navigation():
    message = FakeMessage("receiver")
    state = FakeState()

    asyncio.run(stars_username_entered(message, state, object()))

    answer = message.answers[0]
    assert answer["text"] == (
        "❌ Некорректное имя пользователя\n\n"
        "Введите адрес от 5 до 32 символов без пробелов.\n\n"
        "Пример:\n"
        "@username"
    )
    assert answer["reply_markup"].inline_keyboard[0][0].text == "🏠 Главное меню"


def test_repeated_order_creation_shows_cooldown_message(monkeypatch):
    existing_order = Order(
        id=1,
        user_id=123,
        username="client",
        product_type=PRODUCT_STARS,
        stars_amount=50,
        premium_months=None,
        telegram_username="@receiver",
        price_rub=65,
        status=STATUS_AWAITING_PAYMENT,
        created_at="2026-06-29 12:00:00",
    )

    class LimitedRepository:
        def create_order_if_allowed(self, **kwargs):
            return existing_order, False

    monkeypatch.setattr("handlers.stars.OrderRepository", LimitedRepository)
    message = FakeMessage("@receiver")
    state = FakeState()
    state.data = {"stars_amount": 50, "price_rub": 65}
    settings = type("Settings", (), {"sbp_phone": None, "sbp_name": None})()

    asyncio.run(stars_username_entered(message, state, settings))

    assert message.answers[0]["text"] == "⏳ Подождите несколько секунд."
    assert message.answers[0]["reply_markup"].inline_keyboard[0][0].text == (
        "🏠 Главное меню"
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("abc", "❌ Введите количество цифрами."),
        ("0", "❌ Минимальное количество — 50 звезд."),
        ("-5", "❌ Минимальное количество — 50 звезд."),
        ("999999999", "❌ Максимальное количество — 100000 звезд."),
    ],
)
def test_custom_stars_validation_explains_each_error(value, expected):
    message = FakeMessage(value)
    state = FakeState()

    asyncio.run(stars_custom_amount_entered(message, state))

    answer = message.answers[0]
    assert answer["text"] == expected
    assert answer["reply_markup"].inline_keyboard[0][0].text == "🏠 Главное меню"
