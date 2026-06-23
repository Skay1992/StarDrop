from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from handlers.callbacks import answer_callback, log_callback
from keyboards.callbacks import LEGACY_MAIN_MENU, MAIN_MENU
from keyboards.main import main_menu_keyboard


router = Router()


MAIN_MENU_TEXT = "StarDrop\n\nВыберите раздел:"


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())


@router.callback_query(F.data.in_({MAIN_MENU, LEGACY_MAIN_MENU}))
async def show_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await answer_callback(callback)
    log_callback(callback)
    await state.clear()
    await callback.message.edit_text(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())


@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        f"Действие отменено.\n\n{MAIN_MENU_TEXT}",
        reply_markup=main_menu_keyboard(),
    )
