from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.callbacks import INFO, INFO_PRIVACY, INFO_TERMS, MAIN_MENU, SUPPORT


def info_keyboard(reviews_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📜 Пользовательское соглашение",
                    callback_data=INFO_TERMS,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛡️ Политика конфиденциальности",
                    callback_data=INFO_PRIVACY,
                )
            ],
            [InlineKeyboardButton(text="❤️ Отзывы клиентов", url=reviews_url)],
            [InlineKeyboardButton(text="💬 Поддержка", callback_data=SUPPORT)],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)],
        ]
    )


def document_keyboard(
    callback_base: str,
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    navigation = []
    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"{callback_base}:{page - 1}",
            )
        )
    if page + 1 < total_pages:
        navigation.append(
            InlineKeyboardButton(
                text="➡️ Далее",
                callback_data=f"{callback_base}:{page + 1}",
            )
        )

    rows = []
    if navigation:
        rows.append(navigation)
    rows.extend(
        [
            [InlineKeyboardButton(text="↩️ Информация", callback_data=INFO)],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU)],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
