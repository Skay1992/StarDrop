import pytest

from config.pricing import get_premium_price, get_stars_price


def test_fixed_stars_prices():
    assert get_stars_price(50) == 65
    assert get_stars_price(100) == 130
    assert get_stars_price(250) == 325
    assert get_stars_price(500) == 650
    assert get_stars_price(1000) == 1300
    assert get_stars_price(2500) == 3250


def test_custom_stars_price_is_rounded_up():
    assert get_stars_price(777) == 1011
    assert get_stars_price(1001) == 1302


def test_custom_stars_amount_limits():
    assert get_stars_price(50) == 65
    assert get_stars_price(100000) == 130000

    with pytest.raises(ValueError):
        get_stars_price(49)

    with pytest.raises(ValueError):
        get_stars_price(100001)


def test_premium_prices():
    assert get_premium_price(3) == 990
    assert get_premium_price(6) == 1690
    assert get_premium_price(12) == 2990

    with pytest.raises(ValueError):
        get_premium_price(1)
