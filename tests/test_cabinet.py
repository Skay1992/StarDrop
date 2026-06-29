import asyncio
from types import SimpleNamespace

from database.orders import Order, PRODUCT_PREMIUM, PRODUCT_STARS, STATUS_COMPLETED
from database.support import STATUS_ANSWERED, STATUS_OPEN, SupportTicket
from database.statistics import StatisticsSnapshot
from database.users import User
from handlers.cabinet import (
    show_about,
    show_cabinet,
    show_order_history,
    show_referral,
    show_ticket_details,
    show_ticket_history,
)


def make_user():
    return User(
        user_id=123,
        username="client",
        registered_at="2026-06-29 12:00:00",
        orders_count=0,
        stars_bought=0,
        premium_months=0,
        referral_code="SD123",
        invited_by=None,
        referrals_count=0,
    )


class FakeUserRepository:
    def get_user(self, user_id):
        assert user_id == 123
        return make_user()


class FakeOrderRepository:
    def list_user_orders(self, user_id, limit=5):
        assert user_id == 123
        assert limit == 15
        return [
            Order(
                id=25,
                user_id=123,
                username="client",
                product_type=PRODUCT_STARS,
                stars_amount=1000,
                premium_months=None,
                telegram_username="@receiver",
                price_rub=1300,
                status=STATUS_COMPLETED,
                created_at="2026-06-29 12:00:00",
            ),
            Order(
                id=24,
                user_id=123,
                username="client",
                product_type=PRODUCT_PREMIUM,
                stars_amount=None,
                premium_months=1,
                telegram_username="@receiver",
                price_rub=349,
                status=STATUS_COMPLETED,
                created_at="2026-06-28 12:00:00",
            ),
        ]


class FakeSupportRepository:
    def get_ticket(self, ticket_id):
        assert ticket_id == 7
        return self.list_user_tickets(123)[0]

    def list_user_tickets(self, user_id, limit=15):
        assert user_id == 123
        assert limit == 15
        return [
            SupportTicket(
                id=7,
                user_id=123,
                username="client",
                message="Когда придут звезды?",
                related_order_id=25,
                status=STATUS_OPEN,
                admin_reply=None,
                created_at="2026-06-29 12:00:00",
                answered_at=None,
            ),
            SupportTicket(
                id=6,
                user_id=123,
                username="client",
                message="Спасибо",
                related_order_id=None,
                status=STATUS_ANSWERED,
                admin_reply="Пожалуйста",
                created_at="2026-06-28 12:00:00",
                answered_at="2026-06-28 12:05:00",
            ),
        ]


class FakeStatisticsRepository:
    def get_snapshot(self):
        return StatisticsSnapshot(
            today_orders=2,
            today_revenue=1430,
            today_stars=1000,
            today_premium_months=1,
            today_tickets=1,
            total_orders=12,
            completed_orders=10,
            total_users=8,
            total_stars=5000,
            total_premium_months=7,
            total_revenue=9990,
            today_users=2,
            week_users=5,
        )


class FakeMessage:
    def __init__(self):
        self.edits = []

    async def edit_text(self, text, reply_markup=None):
        self.edits.append({"text": text, "reply_markup": reply_markup})


class FakeCallback:
    def __init__(self, data="cabinet", user_id=123):
        self.data = data
        self.from_user = SimpleNamespace(id=user_id, username="client")
        self.message = FakeMessage()
        self.answers = []

    async def answer(self, text=None, show_alert=None):
        self.answers.append({"text": text, "show_alert": show_alert})


def test_user_can_open_personal_cabinet(monkeypatch):
    monkeypatch.setattr("handlers.cabinet.UserRepository", FakeUserRepository)
    callback = FakeCallback()

    asyncio.run(show_cabinet(callback))

    assert callback.answers
    edit = callback.message.edits[0]
    assert edit["text"] == (
        "👤 Личный кабинет\n\n"
        "🆔 Ваш ID:\n"
        "123\n\n"
        "📅 Регистрация:\n"
        "29.06.2026\n\n"
        "🏆 Статус:\n"
        "Новичок\n\n"
        "━━━━━━━━━━━━━━"
    )
    assert [row[0].text for row in edit["reply_markup"].inline_keyboard] == [
        "📦 История заказов",
        "💬 Мои обращения",
        "👥 Пригласить друга",
        "ℹ️ О StarDrop",
        "🏠 Главное меню",
    ]


def test_cabinet_shows_last_fifteen_orders(monkeypatch):
    monkeypatch.setattr("handlers.cabinet.OrderRepository", FakeOrderRepository)
    callback = FakeCallback(data="cabinet:orders")

    asyncio.run(show_order_history(callback))

    edit = callback.message.edits[0]
    assert edit["text"] == (
        "📦 История заказов\n\n"
        "━━━━━━━━━━━━━━\n\n"
        "#25\n\n"
        "⭐ 1000 Stars\n\n"
        "1300 ₽\n\n"
        "🟢 Выполнен\n\n"
        "━━━━━━━━━━━━━━\n\n"
        "#24\n\n"
        "💎 Premium\n\n"
        "1 месяц\n\n"
        "349 ₽\n\n"
        "🟢 Выполнен\n\n"
        "━━━━━━━━━━━━━━"
    )
    assert [row[0].text for row in edit["reply_markup"].inline_keyboard] == [
        "⬅ Назад",
        "🏠 Главное меню",
    ]


def test_cabinet_shows_ticket_history_with_open_buttons(monkeypatch):
    monkeypatch.setattr("handlers.cabinet.SupportTicketRepository", FakeSupportRepository)
    callback = FakeCallback(data="cabinet:tickets")

    asyncio.run(show_ticket_history(callback))

    edit = callback.message.edits[0]
    assert "💬 Мои обращения" in edit["text"]
    assert "#7\n🟠 Открыто" in edit["text"]
    assert "#6\n🟢 Ответ получен" in edit["text"]
    assert edit["reply_markup"].inline_keyboard[0][0].text == "👀 Обращение #7"
    assert edit["reply_markup"].inline_keyboard[0][0].callback_data == "cabinet:ticket:7"
    assert [row[0].text for row in edit["reply_markup"].inline_keyboard[-2:]] == [
        "⬅ Назад",
        "🏠 Главное меню",
    ]


def test_user_can_open_own_ticket_from_cabinet(monkeypatch):
    monkeypatch.setattr("handlers.cabinet.SupportTicketRepository", FakeSupportRepository)
    callback = FakeCallback(data="cabinet:ticket:7")

    asyncio.run(show_ticket_details(callback))

    edit = callback.message.edits[0]
    assert edit["text"] == (
        "💬 Обращение #7\n\n"
        "Статус: 🟠 Открыто\n\n"
        "Сообщение:\n"
        "Когда придут звезды?"
    )
    assert [row[0].text for row in edit["reply_markup"].inline_keyboard] == [
        "⬅ Назад",
        "🏠 Главное меню",
    ]


def test_referral_screen_shows_personal_link_and_share_button(monkeypatch):
    monkeypatch.setattr("handlers.cabinet.UserRepository", FakeUserRepository)
    callback = FakeCallback(data="cabinet:referral")

    asyncio.run(show_referral(callback))

    link = "https://t.me/stardropstars_bot?start=SD123"
    edit = callback.message.edits[0]
    assert edit["text"] == (
        "👥 Пригласите друзей\n\n"
        "За каждого приглашенного пользователя\n"
        "вы получите бонус.\n\n"
        "Ваша ссылка\n\n"
        f"{link}"
    )
    assert edit["reply_markup"].inline_keyboard[0][0].text == "📤 Поделиться"
    assert edit["reply_markup"].inline_keyboard[0][0].url.startswith(
        "https://t.me/share/url?"
    )


def test_about_screen_uses_live_service_totals(monkeypatch):
    monkeypatch.setattr("handlers.cabinet.StatisticsRepository", FakeStatisticsRepository)
    callback = FakeCallback(data="cabinet:about")

    asyncio.run(show_about(callback))

    assert callback.message.edits[0]["text"] == (
        "🚀 StarDrop\n\n"
        "Версия\n\n"
        "v1.2\n\n"
        "Продано Stars:\n"
        "5000\n\n"
        "Выполнено заказов:\n"
        "10\n\n"
        "Поддержка:\n"
        "24/7\n\n"
        "Отзывы:\n"
        "@stardrop_reviews"
    )
