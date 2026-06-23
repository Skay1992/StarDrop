from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config.pricing import get_premium_price
from config.settings import Settings
from database.orders import OrderRepository, PRODUCT_PREMIUM
from handlers.callbacks import answer_callback, log_callback
from handlers.formatters import format_order_summary
from handlers.states import PremiumOrderState
from handlers.validators import is_valid_telegram_username
from keyboards.callbacks import BUY_PREMIUM, LEGACY_BUY_PREMIUM
from keyboards.main import back_to_menu_keyboard
from keyboards.orders import payment_keyboard
from keyboards.premium import premium_keyboard


router = Router()


@router.callback_query(F.data.in_({BUY_PREMIUM, LEGACY_BUY_PREMIUM}))
async def premium_start(callback: CallbackQuery, state: FSMContext) -> None:
    await answer_callback(callback)
    log_callback(callback)
    await state.clear()
    await callback.message.edit_text("💎 Telegram Premium\n\nВыберите срок:", reply_markup=premium_keyboard())


@router.callback_query(F.data.startswith("premium:months:"))
async def premium_months_selected(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    months = int(callback.data.split(":")[-1])
    price_rub = get_premium_price(months)
    await state.update_data(premium_months=months, price_rub=price_rub)
    await state.set_state(PremiumOrderState.telegram_username)
    await callback.message.edit_text(
        "Введите username получателя:\n@username",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(PremiumOrderState.telegram_username)
async def premium_username_entered(message: Message, state: FSMContext, settings: Settings) -> None:
    telegram_username = message.text.strip() if message.text else ""
    if not is_valid_telegram_username(telegram_username):
        await message.answer("Username должен начинаться с @.", reply_markup=back_to_menu_keyboard())
        return

    data = await state.get_data()
    repository = OrderRepository()
    order = repository.create_order(
        user_id=message.from_user.id,
        username=message.from_user.username,
        product_type=PRODUCT_PREMIUM,
        premium_months=data["premium_months"],
        telegram_username=telegram_username,
        price_rub=data["price_rub"],
    )

    await state.clear()
    await message.answer(
        format_order_summary(order, settings.sbp_phone, settings.sbp_name),
        reply_markup=payment_keyboard(order.id),
    )
