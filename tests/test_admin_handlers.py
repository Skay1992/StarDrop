import asyncio
from types import SimpleNamespace

from database.orders import (
    Order,
    PRODUCT_STARS,
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_PENDING_REVIEW,
)
from database.statistics import StatisticsSnapshot
from database.users import User
from handlers.admin import (
    admin_cancel_order,
    admin_command,
    admin_complete_order,
    admin_confirm_complete_order,
    admin_list_orders,
    admin_orders_menu,
    admin_statistics,
    admin_stub,
    admin_users,
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

    def get_order(self, order_id):
        assert order_id == 7
        return make_order(STATUS_PENDING_REVIEW)

    def update_status(self, order_id, status):
        assert order_id == 7
        return make_order(status)


class FakeCompletionUserRepository:
    recorded = None

    def record_completed_order(self, order):
        FakeCompletionUserRepository.recorded = order


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


class FakeStatisticsRepository:
    def get_snapshot(self):
        return StatisticsSnapshot(
            today_orders=3,
            today_revenue=1779,
            today_stars=1100,
            today_premium_months=1,
            today_tickets=2,
            total_orders=20,
            completed_orders=15,
            total_users=12,
            total_stars=9000,
            total_premium_months=24,
            total_revenue=25000,
            today_users=2,
            week_users=7,
        )


class FakeUserRepository:
    def list_recent_users(self, limit=5):
        assert limit == 5
        return [
            User(
                user_id=123,
                username="client",
                registered_at="2026-06-29 12:00:00",
                orders_count=2,
                stars_bought=100,
                premium_months=0,
                referral_code="SD123",
                invited_by=None,
                referrals_count=1,
            )
        ]


def test_admin_command_shows_owner_panel():
    message = FakeCommandMessage(user_id=999)
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(admin_command(message, settings))

    sent = message.answers[0]
    assert sent["text"] == (
        "━━━━━━━━━━━━━━\n\n"
        "📊 Панель StarDrop\n\n"
        "Выберите раздел.\n\n"
        "━━━━━━━━━━━━━━"
    )
    assert sent["reply_markup"].inline_keyboard[0][0].callback_data == "admin:orders"


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


def test_admin_orders_section_opens_existing_order_filters():
    callback = FakeCallback("admin:orders")
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(admin_orders_menu(callback, settings))

    edit = callback.message.edits[0]
    assert edit["text"] == "📦 Заказы\n\nВыберите список заказов."
    assert edit["reply_markup"].inline_keyboard[0][0].callback_data == (
        "admin:list:pending_review"
    )


def test_admin_statistics_screen_uses_live_snapshot(monkeypatch):
    monkeypatch.setattr("handlers.admin.StatisticsRepository", FakeStatisticsRepository)
    callback = FakeCallback("admin:statistics")
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(admin_statistics(callback, settings))

    text = callback.message.edits[0]["text"]
    assert "📈 Статистика" in text
    assert "Сегодня" in text
    assert "📦 Заказов: 3" in text
    assert "💰 Выручка: 1779 ₽" in text
    assert "⭐ Stars: 1100" in text
    assert "💎 Premium: 1 мес." in text
    assert "💬 Обращения: 2" in text
    assert "📦 Всего заказов: 20" in text
    assert "👥 Пользователей: 12" in text
    assert "💰 Общая выручка: 25000 ₽" in text
    assert [row[0].text for row in callback.message.edits[0]["reply_markup"].inline_keyboard] == [
        "↩️ Админ меню",
        "🏠 Главное меню",
    ]


def test_admin_users_screen_shows_counts_and_recent_registrations(monkeypatch):
    monkeypatch.setattr("handlers.admin.StatisticsRepository", FakeStatisticsRepository)
    monkeypatch.setattr("handlers.admin.UserRepository", FakeUserRepository)
    callback = FakeCallback("admin:users")
    settings = SimpleNamespace(admin_id=999)

    asyncio.run(admin_users(callback, settings))

    text = callback.message.edits[0]["text"]
    assert text == (
        "👥 Пользователи\n\n"
        "Всего: 12\n"
        "Сегодня: 2\n"
        "За неделю: 7\n\n"
        "Последние регистрации\n\n"
        "@client — 29.06.2026"
    )


def test_admin_promocodes_and_settings_show_placeholder():
    settings = SimpleNamespace(admin_id=999)
    for data in ("admin:promocodes", "admin:settings"):
        callback = FakeCallback(data)

        asyncio.run(admin_stub(callback, settings))

        assert callback.message.edits[0]["text"] == "🚧 Скоро появится"
        assert callback.message.edits[0]["reply_markup"] is not None


def test_new_admin_sections_are_denied_for_regular_user():
    settings = SimpleNamespace(admin_id=999)
    cases = [
        (admin_orders_menu, "admin:orders"),
        (admin_statistics, "admin:statistics"),
        (admin_users, "admin:users"),
        (admin_stub, "admin:settings"),
    ]

    for handler, data in cases:
        callback = FakeCallback(data)
        callback.from_user.id = 111

        asyncio.run(handler(callback, settings))

        assert callback.answers[0] == {
            "text": "⛔ Доступ запрещен.",
            "show_alert": True,
        }
        assert not callback.message.edits


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
    monkeypatch.setattr("handlers.admin.UserRepository", FakeCompletionUserRepository)
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
    assert FakeCompletionUserRepository.recorded.status == STATUS_COMPLETED


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
