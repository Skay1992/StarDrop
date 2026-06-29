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
    format_admin_orders_list,
    format_completed_message,
    format_order_summary,
    format_orders_list,
    format_payment_review_message,
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

    assert text == (
        "📦 Заказ №7\n\n"
        "⭐ Telegram Stars\n\n"
        "Количество:\n"
        "777 ⭐\n\n"
        "👤 Получатель:\n"
        "@receiver\n\n"
        "💰 К оплате:\n"
        "1011 ₽\n\n"
        "Статус:\n"
        "🟡 Ожидает оплаты\n\n"
        "Реквизиты для оплаты:\n\n"
        "СБП:\n"
        "+79990000000\n\n"
        "Получатель:\n"
        "Антон\n\n"
        "После оплаты нажмите:\n"
        "✅ Я оплатил"
    )


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
    assert "После оплаты нажмите:\n✅ Я оплатил" in text


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
    assert "Статус:\n🟠 Проверяем оплату" in text


def test_payment_review_message_is_short_and_reassuring():
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

    assert format_payment_review_message(order) == (
        "✅ Спасибо!\n\n"
        "Заказ №7 отправлен на проверку.\n"
        "Мы уведомим вас после выполнения."
    )


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

    assert text == (
        "🆕 Заказ №7\n\n"
        "Услуга:\n"
        "⭐ Telegram Stars\n\n"
        "Количество:\n"
        "777 ⭐\n\n"
        "👤 Получатель:\n"
        "@receiver\n\n"
        "💰 Сумма:\n"
        "1011 ₽\n\n"
        "👤 Клиент:\n"
        "123\n\n"
        "Статус:\n"
        "🟠 Проверяем оплату"
    )


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

    assert "Срок:\n12 мес." in text
    assert "💰 К оплате:\n2990 ₽" in text


def test_one_month_premium_order_summary_and_admin_notification():
    order = Order(
        id=9,
        user_id=123,
        username="client",
        product_type=PRODUCT_PREMIUM,
        stars_amount=None,
        premium_months=1,
        telegram_username="@receiver",
        price_rub=349,
        status=STATUS_AWAITING_PAYMENT,
        created_at="2026-06-24 00:00:00",
    )

    user_text = format_order_summary(order, "+79990000000", "Антон")
    admin_text = format_admin_order(order)

    assert "Срок:\n1 мес." in user_text
    assert "💰 К оплате:\n349 ₽" in user_text
    assert "Срок:\n1 мес." in admin_text
    assert "💰 Сумма:\n349 ₽" in admin_text


def test_payment_requisites_are_formatted_from_env_values():
    assert format_payment_requisites("+79990000000", "Антон") == (
        "Реквизиты для оплаты:\n\n"
        "СБП:\n"
        "+79990000000\n\n"
        "Получатель:\n"
        "Антон"
    )


def test_admin_completion_confirmation_text():
    assert format_admin_completion_confirmation(7) == "Подтвердить выполнение заказа №7?"


def test_admin_orders_list_contains_service_recipient_price_status_and_date():
    order = Order(
        id=7,
        user_id=123,
        username="client",
        product_type=PRODUCT_STARS,
        stars_amount=50,
        premium_months=None,
        telegram_username="@receiver",
        price_rub=65,
        status=STATUS_PENDING_REVIEW,
        created_at="2026-06-24 00:00:00",
    )

    text = format_admin_orders_list([order], "🟠 Заказы на проверке")

    assert "🟠 Заказы на проверке" in text
    assert "#7 · Telegram Stars" in text
    assert "Количество: 50 Stars" in text
    assert "Получатель: @receiver" in text
    assert "Сумма: 65 ₽" in text
    assert "Статус: 🟠 Проверяем оплату" in text
    assert "Дата: 2026-06-24 00:00:00" in text


def test_admin_orders_list_empty_state():
    assert format_admin_orders_list([], "🟠 Заказы на проверке") == (
        "🟠 Заказы на проверке\n\n"
        "Заказов нет."
    )


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
        "50 ⭐ отправлены на @receiver.\n\n"
        "Спасибо за покупку в StarDrop!"
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
        "Telegram Premium на 12 мес. оформлен для @receiver.\n\n"
        "Спасибо за покупку в StarDrop!"
    )


def test_support_text_is_friendly_and_russian():
    assert SUPPORT_TEXT == (
        "💬 Поддержка StarDrop\n\n"
        "Если возник вопрос по заказу — напишите:\n"
        "@StarDropSupport\n\n"
        "⏱ Обычно отвечаем в течение 5–15 минут."
    )


def test_empty_orders_list_has_section_title():
    assert format_orders_list([]) == (
        "📦 Мои заказы\n\n"
        "У вас пока нет заказов."
    )


def test_orders_list_uses_compact_product_cards_without_technical_statuses():
    stars_order = Order(
        id=12,
        user_id=123,
        username="client",
        product_type=PRODUCT_STARS,
        stars_amount=500,
        premium_months=None,
        telegram_username="@stars_receiver",
        price_rub=650,
        status=STATUS_COMPLETED,
        created_at="2026-06-24 00:00:00",
    )
    premium_order = Order(
        id=11,
        user_id=123,
        username="client",
        product_type=PRODUCT_PREMIUM,
        stars_amount=None,
        premium_months=1,
        telegram_username="@premium_receiver",
        price_rub=349,
        status=STATUS_PENDING_REVIEW,
        created_at="2026-06-23 00:00:00",
    )

    assert format_orders_list([stars_order, premium_order]) == (
        "📦 Последние заказы\n\n"
        "#12 — ⭐ 500 Stars — 650 ₽\n"
        "Статус: 🟢 Выполнен\n"
        "Получатель: @stars_receiver\n\n"
        "#11 — 💎 Premium 1 мес. — 349 ₽\n"
        "Статус: 🟠 Проверяем оплату\n"
        "Получатель: @premium_receiver"
    )
