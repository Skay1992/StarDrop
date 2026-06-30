import asyncio
from types import SimpleNamespace

from content.legal import PRIVACY_POLICY, USER_AGREEMENT, split_document
from handlers.info import (
    INFO_TEXT,
    info_command,
    show_info,
    show_privacy_policy,
    show_user_agreement,
)
from keyboards.callbacks import INFO, INFO_PRIVACY, INFO_TERMS, MAIN_MENU, SUPPORT


class FakeState:
    def __init__(self):
        self.cleared = False

    async def clear(self):
        self.cleared = True


class FakeMessage:
    def __init__(self):
        self.answers = []
        self.edits = []

    async def answer(self, text, reply_markup=None):
        self.answers.append({"text": text, "reply_markup": reply_markup})

    async def edit_text(self, text, reply_markup=None):
        self.edits.append({"text": text, "reply_markup": reply_markup})


class FakeCallback:
    def __init__(self, data=INFO):
        self.data = data
        self.message = FakeMessage()
        self.answers = []

    async def answer(self, text=None, show_alert=None):
        self.answers.append({"text": text, "show_alert": show_alert})


def expected_buttons(markup):
    return [
        (button.text, button.callback_data, button.url)
        for row in markup.inline_keyboard
        for button in row
    ]


def test_info_callback_opens_information_center_and_clears_fsm():
    callback = FakeCallback()
    state = FakeState()
    settings = SimpleNamespace(reviews_url="https://t.me/stardrop_reviews")

    asyncio.run(show_info(callback, state, settings))

    assert callback.answers
    assert state.cleared
    assert callback.message.edits[0]["text"] == INFO_TEXT
    assert expected_buttons(callback.message.edits[0]["reply_markup"]) == [
        ("📜 Пользовательское соглашение", INFO_TERMS, None),
        ("🛡️ Политика конфиденциальности", INFO_PRIVACY, None),
        ("❤️ Отзывы клиентов", None, "https://t.me/stardrop_reviews"),
        ("💬 Поддержка", SUPPORT, None),
        ("🏠 Главное меню", MAIN_MENU, None),
    ]


def test_info_command_opens_information_center_and_clears_fsm():
    message = FakeMessage()
    state = FakeState()
    settings = SimpleNamespace(reviews_url="https://t.me/stardrop_reviews")

    asyncio.run(info_command(message, state, settings))

    assert state.cleared
    assert message.answers[0]["text"] == INFO_TEXT
    assert message.answers[0]["reply_markup"] is not None


def test_information_center_text_matches_stardrop_style():
    assert INFO_TEXT == (
        "ℹ️ Информация\n\n"
        "⭐ StarDrop\n\n"
        "Быстрая и безопасная покупка\n"
        "Telegram Stars и Telegram Premium.\n\n"
        "🛡️ Ваши данные защищены.\n"
        "💬 Поддержка доступна прямо в боте.\n"
        "❤️ Реальные отзывы клиентов.\n\n"
        "━━━━━━━━━━━━━━\n\n"
        "Выберите раздел:"
    )


def test_user_agreement_is_shown_inside_telegram_with_page_navigation():
    callback = FakeCallback(INFO_TERMS)

    asyncio.run(show_user_agreement(callback))

    pages = split_document(USER_AGREEMENT)
    edit = callback.message.edits[0]
    assert edit["text"].startswith(pages[0])
    assert edit["text"].endswith(f"Страница 1 из {len(pages)}")
    assert len(edit["text"]) < 4096
    assert expected_buttons(edit["reply_markup"]) == [
        ("➡️ Далее", f"{INFO_TERMS}:1", None),
        ("↩️ Информация", INFO, None),
        ("🏠 Главное меню", MAIN_MENU, None),
    ]


def test_next_agreement_page_has_back_and_forward_navigation():
    callback = FakeCallback(f"{INFO_TERMS}:1")

    asyncio.run(show_user_agreement(callback))

    pages = split_document(USER_AGREEMENT)
    edit = callback.message.edits[0]
    assert edit["text"].startswith(pages[1])
    buttons = expected_buttons(edit["reply_markup"])
    assert ("⬅️ Назад", f"{INFO_TERMS}:0", None) in buttons
    if len(pages) > 2:
        assert ("➡️ Далее", f"{INFO_TERMS}:2", None) in buttons


def test_privacy_policy_is_shown_inside_telegram():
    callback = FakeCallback(INFO_PRIVACY)

    asyncio.run(show_privacy_policy(callback))

    pages = split_document(PRIVACY_POLICY)
    edit = callback.message.edits[0]
    assert edit["text"].startswith(pages[0])
    assert "Политика конфиденциальности StarDrop" in edit["text"]
    assert edit["text"].endswith(f"Страница 1 из {len(pages)}")
    assert len(edit["text"]) < 4096
