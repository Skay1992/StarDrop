from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config.pricing import MAX_CUSTOM_STARS, MIN_CUSTOM_STARS, get_stars_price
from config.settings import Settings
from database.orders import OrderRepository, PRODUCT_STARS
from handlers.callbacks import answer_callback, log_callback
from handlers.formatters import format_order_summary
from handlers.states import StarsOrderState
from handlers.validators import is_valid_telegram_username
from keyboards.callbacks import BUY_STARS, LEGACY_BUY_STARS
from keyboards.main import back_to_menu_keyboard
from keyboards.orders import payment_keyboard
from keyboards.stars import stars_keyboard


router = Router()


@router.callback_query(F.data.in_({BUY_STARS, LEGACY_BUY_STARS}))
async def stars_start(callback: CallbackQuery, state: FSMContext) -> None:
    await answer_callback(callback)
    log_callback(callback)
    await state.clear()
    await callback.message.edit_text(
        "⭐ Telegram Stars\n\nВыберите количество:",
        reply_markup=stars_keyboard(),
    )


@router.callback_query(F.data.startswith("stars:amount:"))
async def stars_amount_selected(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    amount = int(callback.data.split(":")[-1])
    price_rub = get_stars_price(amount)
    await state.update_data(stars_amount=amount, price_rub=price_rub)
    await state.set_state(StarsOrderState.telegram_username)
    await callback.message.edit_text(
        "Введите username получателя:\n@username",
        reply_markup=back_to_menu_keyboard(),
    )


@router.callback_query(F.data == "stars:custom")
async def stars_custom_amount(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(StarsOrderState.custom_amount)
    await callback.message.edit_text(
        f"Введите количество звезд:\nот {MIN_CUSTOM_STARS} до {MAX_CUSTOM_STARS}",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(StarsOrderState.custom_amount)
async def stars_custom_amount_entered(message: Message, state: FSMContext) -> None:
    try:
        amount = int(message.text.strip())
        price_rub = get_stars_price(amount)
    except (AttributeError, ValueError):
        await message.answer(
            f"Введите число от {MIN_CUSTOM_STARS} до {MAX_CUSTOM_STARS}.",
            reply_markup=back_to_menu_keyboard(),
        )
        return

    await state.update_data(stars_amount=amount, price_rub=price_rub)
    await state.set_state(StarsOrderState.telegram_username)
    await message.answer("Введите username получателя:\n@username", reply_markup=back_to_menu_keyboard())


@router.message(StarsOrderState.telegram_username)
async def stars_username_entered(message: Message, state: FSMContext, settings: Settings) -> None:
    telegram_username = message.text.strip() if message.text else ""
    if not is_valid_telegram_username(telegram_username):
        await message.answer("Username должен начинаться с @.", reply_markup=back_to_menu_keyboard())
        return

    data = await state.get_data()
    repository = OrderRepository()
    order = repository.create_order(
        user_id=message.from_user.id,
        username=message.from_user.username,
        product_type=PRODUCT_STARS,
        stars_amount=data["stars_amount"],
        telegram_username=telegram_username,
        price_rub=data["price_rub"],
    )

    await state.clear()
    await message.answer(
        format_order_summary(order, settings.sbp_phone, settings.sbp_name),
        reply_markup=payment_keyboard(order.id),
    )
