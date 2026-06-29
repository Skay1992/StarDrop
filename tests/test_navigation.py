import asyncio
from types import SimpleNamespace

from handlers.start import MAIN_MENU_TEXT, cancel_command, show_main_menu, start_command
from keyboards.callbacks import MAIN_MENU
from keyboards.main import back_to_menu_keyboard


class FakeState:
    def __init__(self):
        self.cleared = False

    async def clear(self):
        self.cleared = True


class FakeMessage:
    def __init__(self):
        self.answers = []
        self.from_user = SimpleNamespace(id=123, username="client")

    async def answer(self, text, reply_markup=None):
        self.answers.append({"text": text, "reply_markup": reply_markup})


class FakeEditableMessage:
    def __init__(self):
        self.edits = []

    async def edit_text(self, text, reply_markup=None):
        self.edits.append({"text": text, "reply_markup": reply_markup})


class FakeCallback:
    def __init__(self):
        self.data = MAIN_MENU
        self.message = FakeEditableMessage()
        self.answered = False

    async def answer(self):
        self.answered = True


def test_start_command_clears_fsm_state_and_shows_main_menu(monkeypatch):
    class FakeUserRepository:
        def register_user(self, user_id, username, invited_by_code=None):
            return object(), True

    monkeypatch.setattr("handlers.start.UserRepository", FakeUserRepository)
    state = FakeState()
    message = FakeMessage()
    settings = SimpleNamespace(reviews_url="https://t.me/stardrop_reviews")

    asyncio.run(start_command(message, state, settings))

    assert state.cleared
    assert message.answers[0]["text"] == (
        "🚀 Добро пожаловать в StarDrop!\n\n"
        "Здесь можно быстро приобрести:\n\n"
        "⭐ Telegram Stars\n"
        "💎 Telegram Premium\n\n"
        "✔️ Быстро\n"
        "✔️ Просто\n"
        "✔️ Поддержка рядом\n\n"
        "👇 Выберите нужный раздел."
    )
    assert message.answers[0]["text"] == MAIN_MENU_TEXT
    assert message.answers[0]["reply_markup"] is not None
    assert message.answers[0]["reply_markup"].inline_keyboard[2][0].url == "https://t.me/stardrop_reviews"


def test_start_registers_user_with_referral_code(monkeypatch):
    registered = []

    class FakeUserRepository:
        def register_user(self, user_id, username, invited_by_code=None):
            registered.append((user_id, username, invited_by_code))
            return object(), True

    monkeypatch.setattr("handlers.start.UserRepository", FakeUserRepository)
    state = FakeState()
    message = FakeMessage()
    settings = SimpleNamespace(reviews_url="https://t.me/stardrop_reviews")
    command = SimpleNamespace(args="SD100")

    asyncio.run(start_command(message, state, settings, command))

    assert registered == [(123, "client", "SD100")]
    assert state.cleared


def test_back_to_menu_callback_clears_fsm_state_and_shows_main_menu():
    state = FakeState()
    callback = FakeCallback()
    settings = SimpleNamespace(reviews_url="https://t.me/stardrop_reviews")

    asyncio.run(show_main_menu(callback, state, settings))

    assert state.cleared
    assert callback.message.edits[0]["text"] == MAIN_MENU_TEXT
    assert callback.message.edits[0]["reply_markup"] is not None
    assert callback.message.edits[0]["reply_markup"].inline_keyboard[2][0].url == "https://t.me/stardrop_reviews"
    assert callback.answered


def test_cancel_command_clears_fsm_state_and_shows_main_menu():
    state = FakeState()
    message = FakeMessage()
    settings = SimpleNamespace(reviews_url="https://t.me/stardrop_reviews")

    asyncio.run(cancel_command(message, state, settings))

    assert state.cleared
    assert message.answers[0]["text"] == f"Действие отменено.\n\n{MAIN_MENU_TEXT}"
    assert message.answers[0]["reply_markup"] is not None
    assert message.answers[0]["reply_markup"].inline_keyboard[2][0].url == "https://t.me/stardrop_reviews"


def test_back_to_menu_button_text():
    keyboard = back_to_menu_keyboard()

    assert keyboard.inline_keyboard[0][0].text == "🏠 Главное меню"
    assert keyboard.inline_keyboard[0][0].callback_data == MAIN_MENU
