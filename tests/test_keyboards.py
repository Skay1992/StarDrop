from database.orders import Order, PRODUCT_STARS, STATUS_COMPLETED, STATUS_PENDING_REVIEW
from keyboards.admin import (
    admin_complete_confirmation_keyboard,
    admin_orders_menu_keyboard,
    admin_orders_list_keyboard,
    admin_panel_keyboard,
)
from keyboards.callbacks import (
    BUY_PREMIUM,
    BUY_STARS,
    CABINET,
    INFO,
    MAIN_MENU,
    MY_ORDERS,
    SUPPORT,
)
from keyboards.main import home_menu_keyboard, main_menu_keyboard
from keyboards.orders import order_cancelled_keyboard, order_completed_keyboard, payment_keyboard
from keyboards.premium import premium_keyboard
from keyboards.stars import stars_keyboard
from keyboards.support import admin_support_menu_keyboard


def test_main_menu_callback_data():
    keyboard = main_menu_keyboard("https://t.me/stardrop_reviews")
    buttons = [row[0] for row in keyboard.inline_keyboard]

    assert [(button.text, button.callback_data, button.url) for button in buttons] == [
        ("🌟 Купить Telegram Stars", BUY_STARS, None),
        ("💎 Купить Telegram Premium", BUY_PREMIUM, None),
        ("👤 Личный кабинет", CABINET, None),
        ("ℹ️ Информация", INFO, None),
        ("❤️ Отзывы клиентов", None, "https://t.me/stardrop_reviews"),
        ("💬 Поддержка", SUPPORT, None),
    ]


def test_stars_keyboard_contains_amounts_custom_amount_and_home_button():
    keyboard = stars_keyboard()
    rows = keyboard.inline_keyboard

    assert [row[0].text for row in rows] == [
        "50 ⭐",
        "100 ⭐",
        "250 ⭐",
        "500 ⭐",
        "1000 ⭐",
        "2500 ⭐",
        "✏️ Своё количество",
        "🏠 Главное меню",
    ]
    assert rows[-1][0].callback_data == MAIN_MENU


def test_premium_keyboard_contains_durations_and_back_button():
    keyboard = premium_keyboard()
    rows = keyboard.inline_keyboard

    assert [row[0].text for row in rows] == [
        "🟢 3 месяца ⭐ Рекомендуем",
        "🟣 6 месяцев",
        "🟡 12 месяцев",
        "⚪ 1 месяц 🚧 Скоро",
        "🏠 Главное меню",
    ]
    assert [row[0].callback_data for row in rows[:-1]] == [
        "premium:months:3",
        "premium:months:6",
        "premium:months:12",
        "premium:soon:1",
    ]
    assert rows[-1][0].callback_data == MAIN_MENU


def test_admin_complete_confirmation_keyboard():
    keyboard = admin_complete_confirmation_keyboard(7)
    buttons = keyboard.inline_keyboard[0]

    assert buttons[0].text == "✅ Да, выполнить"
    assert buttons[0].callback_data == "admin:confirm_complete:7"
    assert buttons[1].text == "↩️ Назад"
    assert buttons[1].callback_data == "admin:back:7"


def test_admin_panel_keyboard_contains_order_filters_and_main_menu():
    keyboard = admin_panel_keyboard()

    assert [(row[0].text, row[0].callback_data) for row in keyboard.inline_keyboard] == [
        ("📦 Заказы", "admin:orders"),
        ("💬 Поддержка", "admin:support"),
        ("👥 Пользователи", "admin:users"),
        ("📈 Статистика", "admin:statistics"),
        ("🎟 Промокоды", "admin:promocodes"),
        ("⚙ Настройки", "admin:settings"),
        ("🏠 Главное меню", MAIN_MENU),
    ]


def test_admin_support_menu_contains_status_filters():
    keyboard = admin_support_menu_keyboard()

    assert [(row[0].text, row[0].callback_data) for row in keyboard.inline_keyboard] == [
        ("🟠 Открытые", "admin:support:list:open"),
        ("📂 Архив", "admin:support:list:archive"),
        ("📋 Все", "admin:support:list:all"),
        ("↩️ Админ меню", "admin:menu"),
        ("🏠 Главное меню", MAIN_MENU),
    ]


def test_admin_orders_menu_preserves_existing_filters():
    keyboard = admin_orders_menu_keyboard()

    assert [(row[0].text, row[0].callback_data) for row in keyboard.inline_keyboard] == [
        ("🟠 Проверяем оплату", "admin:list:pending_review"),
        ("🟢 Выполненные", "admin:list:completed"),
        ("🔴 Отмененные", "admin:list:cancelled"),
        ("📦 Все заказы", "admin:list:all"),
        ("↩️ Админ меню", "admin:menu"),
        ("🏠 Главное меню", MAIN_MENU),
    ]


def test_admin_orders_list_keyboard_shows_actions_only_for_pending_orders():
    pending_order = Order(
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
    completed_order = Order(
        id=8,
        user_id=456,
        username="other",
        product_type=PRODUCT_STARS,
        stars_amount=100,
        premium_months=None,
        telegram_username="@other",
        price_rub=130,
        status=STATUS_COMPLETED,
        created_at="2026-06-24 00:00:00",
    )

    keyboard = admin_orders_list_keyboard([pending_order, completed_order])

    assert keyboard.inline_keyboard[0][0].text == "✅ #7"
    assert keyboard.inline_keyboard[0][0].callback_data == "admin:complete:7"
    assert keyboard.inline_keyboard[0][1].text == "❌ #7"
    assert keyboard.inline_keyboard[0][1].callback_data == "admin:cancel:7"
    assert keyboard.inline_keyboard[1][0].text == "↩️ К заказам"
    assert keyboard.inline_keyboard[1][0].callback_data == "admin:orders"
    assert keyboard.inline_keyboard[2][0].text == "🏠 Главное меню"
    assert keyboard.inline_keyboard[2][0].callback_data == MAIN_MENU


def test_payment_keyboard_contains_paid_cancel_and_back_to_menu():
    keyboard = payment_keyboard(7)

    assert keyboard.inline_keyboard[0][0].text == "✅ Я оплатил"
    assert keyboard.inline_keyboard[0][0].callback_data == "order:paid:7"
    assert keyboard.inline_keyboard[0][1].text == "❌ Отменить"
    assert keyboard.inline_keyboard[0][1].callback_data == "order:cancel:7"
    assert keyboard.inline_keyboard[1][0].text == "🏠 Главное меню"
    assert keyboard.inline_keyboard[1][0].callback_data == MAIN_MENU


def test_home_menu_keyboard_contains_main_menu_button():
    keyboard = home_menu_keyboard()

    assert keyboard.inline_keyboard[0][0].text == "🏠 Главное меню"
    assert keyboard.inline_keyboard[0][0].callback_data == MAIN_MENU


def test_order_completed_keyboard_contains_main_menu_and_orders():
    keyboard = order_completed_keyboard()

    assert keyboard.inline_keyboard[0][0].text == "📦 Мои заказы"
    assert keyboard.inline_keyboard[0][0].callback_data == MY_ORDERS
    assert keyboard.inline_keyboard[1][0].text == "🏠 Главное меню"
    assert keyboard.inline_keyboard[1][0].callback_data == MAIN_MENU


def test_order_cancelled_keyboard_contains_main_menu_and_support():
    keyboard = order_cancelled_keyboard()

    assert keyboard.inline_keyboard[0][0].text == "💬 Поддержка"
    assert keyboard.inline_keyboard[0][0].callback_data == SUPPORT
    assert keyboard.inline_keyboard[1][0].text == "🏠 Главное меню"
    assert keyboard.inline_keyboard[1][0].callback_data == MAIN_MENU
