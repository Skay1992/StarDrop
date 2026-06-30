from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config.settings import Settings
from content.legal import PRIVACY_POLICY, USER_AGREEMENT, split_document
from handlers.callbacks import answer_callback, log_callback
from keyboards.callbacks import INFO, INFO_PRIVACY, INFO_TERMS
from keyboards.info import document_keyboard, info_keyboard


router = Router()

INFO_TEXT = (
    "ℹ️ Информация\n\n"
    "⭐ StarDrop\n\n"
    "Быстрая и безопасная покупка\n"
    "Telegram Stars и Telegram Premium.\n\n"
    "🛡️ Ваши данные защищены.\n"
    "💬 Поддержка доступна прямо в боте.\n"
    "❤️ Реальные отзывы клиентов.\n\n"
    "━━━━━━━━━━━━━━\n\n"
    "Выберите раздел:"
)


def _document_page(callback_data: str, total_pages: int) -> int:
    try:
        requested_page = int(callback_data.rsplit(":", 1)[-1])
    except ValueError:
        requested_page = 0
    return min(max(requested_page, 0), total_pages - 1)


async def _show_document(
    callback: CallbackQuery,
    document: str,
    callback_base: str,
) -> None:
    await answer_callback(callback)
    log_callback(callback)
    pages = split_document(document)
    page = _document_page(callback.data, len(pages))
    text = (
        f"{pages[page]}\n\n"
        "━━━━━━━━━━━━━━\n"
        f"Страница {page + 1} из {len(pages)}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=document_keyboard(callback_base, page, len(pages)),
    )


@router.message(Command("info"))
async def info_command(
    message: Message,
    state: FSMContext,
    settings: Settings,
) -> None:
    await state.clear()
    await message.answer(
        INFO_TEXT,
        reply_markup=info_keyboard(settings.reviews_url),
    )


@router.callback_query(F.data == INFO)
async def show_info(
    callback: CallbackQuery,
    state: FSMContext,
    settings: Settings,
) -> None:
    await answer_callback(callback)
    log_callback(callback)
    await state.clear()
    await callback.message.edit_text(
        INFO_TEXT,
        reply_markup=info_keyboard(settings.reviews_url),
    )


@router.callback_query(F.data.startswith(INFO_TERMS))
async def show_user_agreement(callback: CallbackQuery) -> None:
    await _show_document(callback, USER_AGREEMENT, INFO_TERMS)


@router.callback_query(F.data.startswith(INFO_PRIVACY))
async def show_privacy_policy(callback: CallbackQuery) -> None:
    await _show_document(callback, PRIVACY_POLICY, INFO_PRIVACY)
