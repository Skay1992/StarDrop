import asyncio
import sqlite3
from types import SimpleNamespace

from aiogram.exceptions import TelegramBadRequest

from handlers.errors import DATABASE_ERROR_TEXT, GENERAL_ERROR_TEXT, handle_error


class FakeMessage:
    def __init__(self):
        self.answers = []

    async def answer(self, text, reply_markup=None):
        self.answers.append({"text": text, "reply_markup": reply_markup})


def make_event(exception):
    message = FakeMessage()
    update = SimpleNamespace(message=message, callback_query=None)
    return SimpleNamespace(exception=exception, update=update), message


def test_unexpected_error_is_hidden_from_user(caplog):
    event, message = make_event(RuntimeError("секретная техническая ошибка"))

    handled = asyncio.run(handle_error(event))

    assert handled is True
    assert message.answers[0]["text"] == GENERAL_ERROR_TEXT
    assert "секретная техническая ошибка" not in message.answers[0]["text"]
    assert "секретная техническая ошибка" in caplog.text


def test_database_error_shows_service_unavailable_message():
    event, message = make_event(sqlite3.OperationalError("database is locked"))

    handled = asyncio.run(handle_error(event))

    assert handled is True
    assert message.answers[0]["text"] == DATABASE_ERROR_TEXT


def test_unchanged_telegram_message_is_ignored_without_warning_user(caplog):
    caplog.set_level("INFO")
    event, message = make_event(
        TelegramBadRequest(
            method=SimpleNamespace(),
            message="message is not modified",
        )
    )

    handled = asyncio.run(handle_error(event))

    assert handled is True
    assert not message.answers
    assert "Сообщение Telegram уже актуально" in caplog.text
