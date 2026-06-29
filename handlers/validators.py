import re


TELEGRAM_USERNAME_PATTERN = re.compile(r"^@[A-Za-z][A-Za-z0-9_]{4,31}$")


def is_valid_telegram_username(value: str) -> bool:
    return TELEGRAM_USERNAME_PATTERN.fullmatch(value) is not None
