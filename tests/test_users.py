from database.orders import (
    Order,
    OrderRepository,
    PRODUCT_PREMIUM,
    PRODUCT_STARS,
    STATUS_COMPLETED,
)
from database.users import UserRepository


def test_first_registration_creates_user_with_referral_code(tmp_path):
    repository = UserRepository(tmp_path / "users.sqlite3")

    user, created = repository.register_user(123456789, "client")

    assert created is True
    assert user.user_id == 123456789
    assert user.username == "client"
    assert user.registered_at
    assert user.orders_count == 0
    assert user.stars_bought == 0
    assert user.premium_months == 0
    assert user.referral_code == "SD123456789"
    assert user.invited_by is None
    assert user.referrals_count == 0


def test_existing_user_is_not_changed_on_repeated_start(tmp_path):
    repository = UserRepository(tmp_path / "users.sqlite3")
    first, _ = repository.register_user(123, "original")

    repeated, created = repository.register_user(123, "renamed", "SD999")

    assert created is False
    assert repeated == first


def test_referral_is_saved_only_on_first_registration(tmp_path):
    repository = UserRepository(tmp_path / "users.sqlite3")
    referrer, _ = repository.register_user(100, "referrer")

    invited, created = repository.register_user(
        200,
        "invited",
        referrer.referral_code,
    )
    repeated, repeated_created = repository.register_user(
        200,
        "invited_changed",
        referrer.referral_code,
    )

    assert created is True
    assert invited.invited_by == referrer.user_id
    assert repeated_created is False
    assert repeated.invited_by == referrer.user_id
    assert repository.get_user(referrer.user_id).referrals_count == 1


def test_recent_users_are_returned_latest_first(tmp_path):
    repository = UserRepository(tmp_path / "users.sqlite3")
    repository.register_user(100, "first")
    repository.register_user(200, "second")

    users = repository.list_recent_users(limit=5)

    assert [user.user_id for user in users] == [200, 100]


def test_completed_orders_update_user_purchase_counters(tmp_path):
    repository = UserRepository(tmp_path / "users.sqlite3")
    repository.register_user(123, "client")
    repository.record_completed_order(
        Order(
            id=1,
            user_id=123,
            username="client",
            product_type=PRODUCT_STARS,
            stars_amount=100,
            premium_months=None,
            telegram_username="@client",
            price_rub=130,
            status=STATUS_COMPLETED,
            created_at="2026-06-29 12:00:00",
        )
    )
    repository.record_completed_order(
        Order(
            id=2,
            user_id=123,
            username="client",
            product_type=PRODUCT_PREMIUM,
            stars_amount=None,
            premium_months=3,
            telegram_username="@client",
            price_rub=990,
            status=STATUS_COMPLETED,
            created_at="2026-06-29 12:00:00",
        )
    )

    user = repository.get_user(123)

    assert user.orders_count == 2
    assert user.stars_bought == 100
    assert user.premium_months == 3


def test_first_registration_imports_existing_completed_order_totals(tmp_path):
    db_path = tmp_path / "users.sqlite3"
    orders = OrderRepository(db_path)
    orders.create_order(
        user_id=123,
        username="client",
        product_type=PRODUCT_STARS,
        stars_amount=250,
        telegram_username="@client",
        price_rub=325,
        status=STATUS_COMPLETED,
    )

    user, _ = UserRepository(db_path).register_user(123, "client")

    assert user.orders_count == 1
    assert user.stars_bought == 250
    assert user.premium_months == 0
