def is_valid_telegram_username(value: str) -> bool:
    value = value.strip()
    return value.startswith("@") and len(value) > 1 and " " not in value
