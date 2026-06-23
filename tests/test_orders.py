from database.orders import (
    OrderRepository,
    PRODUCT_STARS,
    STATUS_AWAITING_PAYMENT,
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_PENDING_REVIEW,
)


def test_order_creation_stores_price(tmp_path):
    repository = OrderRepository(tmp_path / "orders.sqlite3")

    order = repository.create_order(
        user_id=123,
        username="client",
        product_type=PRODUCT_STARS,
        stars_amount=777,
        telegram_username="@receiver",
        price_rub=1011,
    )

    assert order.id == 1
    assert order.price_rub == 1011
    assert order.status == STATUS_AWAITING_PAYMENT


def test_order_status_transitions(tmp_path):
    repository = OrderRepository(tmp_path / "orders.sqlite3")
    order = repository.create_order(
        user_id=123,
        username="client",
        product_type=PRODUCT_STARS,
        stars_amount=50,
        telegram_username="@receiver",
        price_rub=65,
    )

    order = repository.update_status(order.id, STATUS_PENDING_REVIEW)
    assert order.status == STATUS_PENDING_REVIEW

    order = repository.update_status(order.id, STATUS_COMPLETED)
    assert order.status == STATUS_COMPLETED

    order = repository.update_status(order.id, STATUS_CANCELLED)
    assert order.status == STATUS_CANCELLED


def test_user_order_listing_returns_latest_first(tmp_path):
    repository = OrderRepository(tmp_path / "orders.sqlite3")
    first = repository.create_order(
        user_id=123,
        username="client",
        product_type=PRODUCT_STARS,
        stars_amount=50,
        telegram_username="@first",
        price_rub=65,
    )
    second = repository.create_order(
        user_id=123,
        username="client",
        product_type=PRODUCT_STARS,
        stars_amount=100,
        telegram_username="@second",
        price_rub=130,
    )

    orders = repository.list_user_orders(123)

    assert [order.id for order in orders] == [second.id, first.id]
