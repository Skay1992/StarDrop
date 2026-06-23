from database.orders import (
    Order,
    PRODUCT_PREMIUM,
    PRODUCT_STARS,
    STATUS_AWAITING_PAYMENT,
    STATUS_COMPLETED,
    STATUS_PENDING_REVIEW,
)
from handlers.formatters import (
    format_admin_completion_confirmation,
    format_admin_order,
    format_completed_message,
    format_order_summary,
    format_payment_requisites,
)
from handlers.support import SUPPORT_TEXT
from handlers.validators import is_valid_telegram_username


def test_username_validation():
    assert is_valid_telegram_username("@username")
    assert not is_valid_telegram_username("username")
    assert not is_valid_telegram_username("@")


def test_user_order_summary_contains_russian_service_details_and_price():
    order = Order(
        id=7,
        user_id=123,
        username="client",
        product_type=PRODUCT_STARS,
        stars_amount=777,
        premium_months=None,
        telegram_username="@receiver",
        price_rub=1011,
        status=STATUS_AWAITING_PAYMENT,
        created_at="2026-06-24 00:00:00",
    )

    text = format_order_summary(order, "+79990000000", "Антон")

    assert "⭐ Заказ Telegram Stars" in text
    assert "Количество: 777 Stars" in text
    assert "Получатель: @receiver" in text
    assert "Сумма к оплате: 1011 ₽" in text
    assert "СБП:\n+79990000000" in text
    assert "Получатель:\nАнтон" in text
    assert "После перевода нажмите:\n✅ Я оплатил" in text


def test_user_order_summary_shows_unavailable_payment_requisites_when_env_is_empty():
    order = Order(
        id=7,
        user_id=123,
        username="client",
        product_type=PRODUCT_STARS,
        stars_amount=777,
        premium_months=None,
        telegram_username="@receiver",
        price_rub=1011,
        status=STATUS_AWAITING_PAYMENT,
        created_at="2026-06-24 00:00:00",
    )

    text = format_order_summary(order)

    assert "Реквизиты временно недоступны. Обратитесь в поддержку." in text
    assert "После перевода нажмите:\n✅ Я оплатил" in text


def test_user_order_summary_hides_payment_instructions_after_paid():
    order = Order(
        id=7,
        user_id=123,
        username="client",
        product_type=PRODUCT_STARS,
        stars_amount=777,
        premium_months=None,
        telegram_username="@receiver",
        price_rub=1011,
        status=STATUS_PENDING_REVIEW,
        created_at="2026-06-24 00:00:00",
    )

    text = format_order_summary(order)

    assert "Реквизиты для оплаты:" not in text
    assert "Статус: 🟠 Проверяем оплату" in text


def test_admin_order_contains_russian_service_details_price_and_status():
    order = Order(
        id=7,
        user_id=123,
        username="client",
        product_type=PRODUCT_STARS,
        stars_amount=777,
        premium_months=None,
        telegram_username="@receiver",
        price_rub=1011,
        status=STATUS_PENDING_REVIEW,
        created_at="2026-06-24 00:00:00",
    )

    text = format_admin_order(order)

    assert "🆕 Новый заказ" in text
    assert "Номер: #7" in text
    assert "Услуга: Telegram Stars" in text
    assert "Количество: 777 Stars" in text
    assert "Получатель: @receiver" in text
    assert "Сумма: 1011 ₽" in text
    assert "Клиент ID: 123" in text
    assert "Статус: 🟠 Проверяем оплату" in text


def test_premium_order_summary_contains_duration_and_price():
    order = Order(
        id=8,
        user_id=123,
        username="client",
        product_type=PRODUCT_PREMIUM,
        stars_amount=None,
        premium_months=12,
        telegram_username="@receiver",
        price_rub=2990,
        status=STATUS_AWAITING_PAYMENT,
        created_at="2026-06-24 00:00:00",
    )

    text = format_order_summary(order, "+79990000000", "Антон")

    assert "Срок: 12 месяцев" in text
    assert "Сумма к оплате: 2990 ₽" in text


def test_payment_requisites_are_formatted_from_env_values():
    assert format_payment_requisites("+79990000000", "Антон") == (
        "Реквизиты для оплаты:\n\n"
        "СБП:\n"
        "+79990000000\n\n"
        "Получатель:\n"
        "Антон"
    )


def test_admin_completion_confirmation_text():
    assert format_admin_completion_confirmation(7) == "Подтвердить выполнение заказа #7?"


def test_completed_stars_message_mentions_amount_and_recipient():
    order = Order(
        id=7,
        user_id=123,
        username="client",
        product_type=PRODUCT_STARS,
        stars_amount=50,
        premium_months=None,
        telegram_username="@receiver",
        price_rub=65,
        status=STATUS_COMPLETED,
        created_at="2026-06-24 00:00:00",
    )

    assert format_completed_message(order) == (
        "✅ Заказ выполнен\n\n"
        "50 Stars отправлены на @receiver.\n"
        "Спасибо за покупку в StarDrop."
    )


def test_completed_premium_message_mentions_duration_and_recipient():
    order = Order(
        id=8,
        user_id=123,
        username="client",
        product_type=PRODUCT_PREMIUM,
        stars_amount=None,
        premium_months=12,
        telegram_username="@receiver",
        price_rub=2990,
        status=STATUS_COMPLETED,
        created_at="2026-06-24 00:00:00",
    )

    assert format_completed_message(order) == (
        "✅ Заказ выполнен\n\n"
        "Telegram Premium на 12 месяцев оформлен для @receiver.\n"
        "Спасибо за покупку в StarDrop."
    )


def test_support_text_is_friendly_and_russian():
    assert SUPPORT_TEXT == (
        "💬 Поддержка StarDrop\n\n"
        "Если возник вопрос по заказу — напишите:\n"
        "@StarDropSupport\n\n"
        "⏱ Обычно отвечаем в течение 5–15 минут."
    )
