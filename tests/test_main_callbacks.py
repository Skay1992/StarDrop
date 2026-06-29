import asyncio

from handlers.orders import list_orders
from handlers.premium import premium_start
from handlers.stars import stars_start
from handlers.support import SUPPORT_TEXT, support
from handlers.states import SupportUserState
from keyboards.callbacks import BUY_PREMIUM, BUY_STARS, MY_ORDERS, SUPPORT


class FakeState:
    def __init__(self):
        self.cleared = False
        self.current_state = None

    async def clear(self):
        self.cleared = True

    async def set_state(self, state):
        self.current_state = state


class FakeMessage:
    def __init__(self):
        self.edits = []

    async def edit_text(self, text, reply_markup=None):
        self.edits.append({"text": text, "reply_markup": reply_markup})


class FakeUser:
    id = 123


class FakeCallback:
    def __init__(self, data):
        self.data = data
        self.message = FakeMessage()
        self.from_user = FakeUser()
        self.answers = []

    async def answer(self, text=None, show_alert=None):
        self.answers.append({"text": text, "show_alert": show_alert})


class FakeOrderRepository:
    def list_user_orders(self, user_id):
        assert user_id == 123
        return []


def test_buy_stars_callback_answers_and_opens_stars_menu():
    callback = FakeCallback(BUY_STARS)
    state = FakeState()

    asyncio.run(stars_start(callback, state))

    assert callback.answers
    assert state.cleared
    assert callback.message.edits[0]["text"] == "⭐ Telegram Stars\n\nВыберите количество:"
    assert callback.message.edits[0]["reply_markup"] is not None


def test_buy_premium_callback_answers_and_opens_premium_menu():
    callback = FakeCallback(BUY_PREMIUM)
    state = FakeState()

    asyncio.run(premium_start(callback, state))

    assert callback.answers
    assert state.cleared
    assert callback.message.edits[0]["text"] == "💎 Telegram Premium\n\nВыберите срок:"
    assert callback.message.edits[0]["reply_markup"] is not None


def test_support_callback_answers_and_opens_support(monkeypatch):
    callback = FakeCallback(SUPPORT)
    state = FakeState()

    asyncio.run(support(callback, state))

    assert callback.answers
    assert callback.message.edits[0]["text"] == (
        "💬 Поддержка StarDrop\n\n"
        "Напишите ваш вопрос одним сообщением.\n"
        "Мы ответим как можно быстрее."
    )
    assert callback.message.edits[0]["text"] == SUPPORT_TEXT
    assert callback.message.edits[0]["reply_markup"] is not None
    assert state.current_state == SupportUserState.message


def test_my_orders_callback_answers_and_opens_orders(monkeypatch):
    monkeypatch.setattr("handlers.orders.OrderRepository", FakeOrderRepository)
    callback = FakeCallback(MY_ORDERS)

    asyncio.run(list_orders(callback))

    assert callback.answers
    assert callback.message.edits[0]["text"] == "📦 Мои заказы\n\nУ вас пока нет заказов."
    assert callback.message.edits[0]["reply_markup"] is not None
