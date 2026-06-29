from aiogram.fsm.state import State, StatesGroup


class StarsOrderState(StatesGroup):
    custom_amount = State()
    telegram_username = State()


class PremiumOrderState(StatesGroup):
    telegram_username = State()


class SupportUserState(StatesGroup):
    message = State()


class SupportAdminState(StatesGroup):
    reply = State()
