STARS_PRICES = {
    50: 65,
    100: 130,
    250: 325,
    500: 650,
    1000: 1300,
    2500: 3250,
}

PREMIUM_PRICES = {
    1: 349,
    3: 990,
    6: 1690,
    12: 2990,
}
AVAILABLE_PREMIUM_MONTHS = (3, 6, 12)

MIN_CUSTOM_STARS = 50
MAX_CUSTOM_STARS = 100000


def get_stars_price(stars_amount: int) -> int:
    if stars_amount < MIN_CUSTOM_STARS or stars_amount > MAX_CUSTOM_STARS:
        raise ValueError("Количество звезд должно быть от 50 до 100000")

    if stars_amount in STARS_PRICES:
        return STARS_PRICES[stars_amount]

    return (stars_amount * 13 + 9) // 10


def get_premium_price(months: int) -> int:
    try:
        return PREMIUM_PRICES[months]
    except KeyError as exc:
        raise ValueError("Срок Premium должен быть 1, 3, 6 или 12 месяцев") from exc


def premium_duration_label(months: int) -> str:
    if months == 1:
        return "1 месяц"
    if months == 3:
        return "3 месяца"
    return f"{months} месяцев"
