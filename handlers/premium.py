import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config.pricing import AVAILABLE_PREMIUM_MONTHS, get_premium_price
from config.settings import Settings
from database.orders import OrderRepository, PRODUCT_PREMIUM
from handlers.callbacks import answer_callback, log_callback
from handlers.formatters import format_order_summary
from handlers.states import PremiumOrderState
from handlers.texts import ORDER_COOLDOWN_TEXT, RECIPIENT_PROMPT, USERNAME_ERROR
from handlers.validators import is_valid_telegram_username
from keyboards.callbacks import BUY_PREMIUM, LEGACY_BUY_PREMIUM
from keyboards.main import back_to_menu_keyboard
from keyboards.orders import payment_keyboard
from keyboards.premium import premium_keyboard, premium_unavailable_keyboard


router = Router()
logger = logging.getLogger(__name__)

PREMIUM_MENU_TEXT = (
    "💎 Telegram Premium\n\n"
    "Выберите срок подписки:\n\n"
    "🟢 3 месяца ⭐ Рекомендуем\n"
    "🎁 Небольшая скидка\n\n"
    "🟣 6 месяцев\n"
    "💰 Еще выгоднее\n\n"
    "🟡 12 месяцев\n"
    "🏆 Максимальная выгода\n\n"
    "────────────\n\n"
    "⚪ 1 месяц\n"
    "🚧 Скоро появится"
)
PREMIUM_UNAVAILABLE_TEXT = (
    "💎 Telegram Premium — 1 месяц\n\n"
    "Этот тариф пока недоступен.\n\n"
    "Сейчас можно оформить:\n\n"
    "🟢 3 месяца\n"
    "🟣 6 месяцев\n"
    "🟡 12 месяцев\n\n"
    "Мы работаем над добавлением Premium на 1 месяц ❤️"
)


async def _show_premium_unavailable(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await answer_callback(callback)
    await state.clear()
    await callback.message.edit_text(
        PREMIUM_UNAVAILABLE_TEXT,
        reply_markup=premium_unavailable_keyboard(),
    )


@router.callback_query(F.data.in_({BUY_PREMIUM, LEGACY_BUY_PREMIUM}))
async def premium_start(callback: CallbackQuery, state: FSMContext) -> None:
    await answer_callback(callback)
    log_callback(callback)
    await state.clear()
    await callback.message.edit_text(
        PREMIUM_MENU_TEXT,
        reply_markup=premium_keyboard(),
    )


@router.callback_query(F.data.startswith("premium:months:"))
async def premium_months_selected(callback: CallbackQuery, state: FSMContext) -> None:
    months = int(callback.data.split(":")[-1])
    if months not in AVAILABLE_PREMIUM_MONTHS:
        await _show_premium_unavailable(callback, state)
        return

    await callback.answer()
    price_rub = get_premium_price(months)
    await state.update_data(premium_months=months, price_rub=price_rub)
    await state.set_state(PremiumOrderState.telegram_username)
    await callback.message.edit_text(
        RECIPIENT_PROMPT,
        reply_markup=back_to_menu_keyboard(),
    )


@router.callback_query(F.data == "premium:soon:1")
async def premium_month_unavailable(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await _show_premium_unavailable(callback, state)


@router.message(PremiumOrderState.telegram_username)
async def premium_username_entered(message: Message, state: FSMContext, settings: Settings) -> None:
    telegram_username = message.text if message.text else ""
    if not is_valid_telegram_username(telegram_username):
        await message.answer(USERNAME_ERROR, reply_markup=back_to_menu_keyboard())
        return

    data = await state.get_data()
    repository = OrderRepository()
    order, created = repository.create_order_if_allowed(
        user_id=message.from_user.id,
        username=message.from_user.username,
        product_type=PRODUCT_PREMIUM,
        premium_months=data["premium_months"],
        telegram_username=telegram_username,
        price_rub=data["price_rub"],
    )
    if not created:
        await message.answer(
            ORDER_COOLDOWN_TEXT,
            reply_markup=back_to_menu_keyboard(),
        )
        return

    await state.clear()
    logger.info("Создан заказ №%s пользователя %s", order.id, order.user_id)
    await message.answer(
        format_order_summary(order, settings.sbp_phone, settings.sbp_name),
        reply_markup=payment_keyboard(order.id),
    )
