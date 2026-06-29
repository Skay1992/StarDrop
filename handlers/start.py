from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.filters.command import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config.settings import Settings
from database.users import UserRepository
from handlers.callbacks import answer_callback, log_callback
from keyboards.callbacks import LEGACY_MAIN_MENU, MAIN_MENU
from keyboards.main import main_menu_keyboard


router = Router()


MAIN_MENU_TEXT = (
    "🚀 Добро пожаловать в StarDrop!\n\n"
    "Здесь можно быстро приобрести:\n\n"
    "⭐ Telegram Stars\n"
    "💎 Telegram Premium\n\n"
    "✔️ Быстро\n"
    "✔️ Просто\n"
    "✔️ Поддержка рядом\n\n"
    "👇 Выберите нужный раздел."
)


@router.message(CommandStart())
async def start_command(
    message: Message,
    state: FSMContext,
    settings: Settings,
    command: Optional[CommandObject] = None,
) -> None:
    await state.clear()
    referral_code = command.args.strip() if command and command.args else None
    UserRepository().register_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        invited_by_code=referral_code,
    )
    await message.answer(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard(settings.reviews_url))


@router.callback_query(F.data.in_({MAIN_MENU, LEGACY_MAIN_MENU}))
async def show_main_menu(callback: CallbackQuery, state: FSMContext, settings: Settings) -> None:
    await answer_callback(callback)
    log_callback(callback)
    await state.clear()
    await callback.message.edit_text(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard(settings.reviews_url))


@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext, settings: Settings) -> None:
    await state.clear()
    await message.answer(
        f"Действие отменено.\n\n{MAIN_MENU_TEXT}",
        reply_markup=main_menu_keyboard(settings.reviews_url),
    )
