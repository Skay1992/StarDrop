import asyncio

import pytest

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


class FakeMessage:
    def __init__(self, text=None):
        self.text = text
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
        "Введите username получателя.\n\n"
        "Например:\n"
        "@username\n\n"
        "👇 Отправьте username сообщением."
    )
    assert edit["reply_markup"].inline_keyboard[0][0].text == "🏠 Главное меню"


def test_username_without_at_sign_shows_clear_error_with_home_navigation():
    message = FakeMessage("receiver")
    state = FakeState()

    asyncio.run(stars_username_entered(message, state, object()))

    answer = message.answers[0]
    assert answer["text"] == (
        "❌ Username должен начинаться с @\n\n"
        "Пример:\n"
        "@username"
    )
    assert answer["reply_markup"].inline_keyboard[0][0].text == "🏠 Главное меню"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("text", "Введите количество цифрами."),
        ("49", "Минимальное количество — 50 Stars."),
        ("100001", "Максимальное количество — 100000 Stars."),
    ],
)
def test_custom_stars_validation_explains_each_error(value, expected):
    message = FakeMessage(value)
    state = FakeState()

    asyncio.run(stars_custom_amount_entered(message, state))

    answer = message.answers[0]
    assert answer["text"] == expected
    assert answer["reply_markup"].inline_keyboard[0][0].text == "🏠 Главное меню"
