from keyboards.admin import admin_complete_confirmation_keyboard
from keyboards.callbacks import BUY_PREMIUM, BUY_STARS, MAIN_MENU, MY_ORDERS, SUPPORT
from keyboards.main import home_menu_keyboard, main_menu_keyboard
from keyboards.orders import order_completed_keyboard, payment_keyboard
from keyboards.premium import premium_keyboard
from keyboards.stars import stars_keyboard


def test_main_menu_callback_data():
    keyboard = main_menu_keyboard()
    buttons = [row[0] for row in keyboard.inline_keyboard]

    assert [(button.text, button.callback_data) for button in buttons] == [
        ("⭐ Купить звезды", BUY_STARS),
        ("💎 Telegram Premium", BUY_PREMIUM),
        ("📦 Мои заказы", MY_ORDERS),
        ("💬 Поддержка", SUPPORT),
    ]


def test_stars_keyboard_contains_prices_custom_amount_and_back_button():
    keyboard = stars_keyboard()
    rows = keyboard.inline_keyboard

    assert [row[0].text for row in rows] == [
        "50 · 65 ₽",
        "100 · 130 ₽",
        "250 · 325 ₽",
        "500 · 650 ₽",
        "1000 · 1300 ₽",
        "2500 · 3250 ₽",
        "Своё количество",
        "↩️ В меню",
    ]
    assert rows[-1][0].callback_data == MAIN_MENU


def test_premium_keyboard_contains_durations_and_back_button():
    keyboard = premium_keyboard()
    rows = keyboard.inline_keyboard

    assert [row[0].text for row in rows] == [
        "3 месяца · 990 ₽",
        "6 месяцев · 1690 ₽",
        "12 месяцев · 2990 ₽",
        "↩️ В меню",
    ]
    assert rows[-1][0].callback_data == MAIN_MENU


def test_admin_complete_confirmation_keyboard():
    keyboard = admin_complete_confirmation_keyboard(7)
    buttons = keyboard.inline_keyboard[0]

    assert buttons[0].text == "✅ Да, выполнить"
    assert buttons[0].callback_data == "admin:confirm_complete:7"
    assert buttons[1].text == "↩️ Нет, назад"
    assert buttons[1].callback_data == "admin:back:7"


def test_payment_keyboard_contains_paid_cancel_and_back_to_menu():
    keyboard = payment_keyboard(7)

    assert keyboard.inline_keyboard[0][0].text == "✅ Я оплатил"
    assert keyboard.inline_keyboard[0][0].callback_data == "order:paid:7"
    assert keyboard.inline_keyboard[0][1].text == "❌ Отмена"
    assert keyboard.inline_keyboard[0][1].callback_data == "order:cancel:7"
    assert keyboard.inline_keyboard[1][0].text == "↩️ В меню"
    assert keyboard.inline_keyboard[1][0].callback_data == MAIN_MENU


def test_home_menu_keyboard_contains_main_menu_button():
    keyboard = home_menu_keyboard()

    assert keyboard.inline_keyboard[0][0].text == "🏠 Главное меню"
    assert keyboard.inline_keyboard[0][0].callback_data == MAIN_MENU


def test_order_completed_keyboard_contains_main_menu_and_orders():
    keyboard = order_completed_keyboard()

    assert keyboard.inline_keyboard[0][0].text == "🏠 Главное меню"
    assert keyboard.inline_keyboard[0][0].callback_data == MAIN_MENU
    assert keyboard.inline_keyboard[1][0].text == "📦 Мои заказы"
    assert keyboard.inline_keyboard[1][0].callback_data == MY_ORDERS
