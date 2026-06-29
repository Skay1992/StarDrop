from database.orders import (
    OrderRepository,
    PRODUCT_PREMIUM,
    PRODUCT_STARS,
    STATUS_COMPLETED,
)
from database.statistics import StatisticsRepository
from database.support import SupportTicketRepository
from database.users import UserRepository


def test_statistics_are_calculated_from_real_orders_users_and_tickets(tmp_path):
    db_path = tmp_path / "statistics.sqlite3"
    users = UserRepository(db_path)
    orders = OrderRepository(db_path)
    tickets = SupportTicketRepository(db_path)
    users.register_user(1, "first")
    users.register_user(2, "second")
    orders.create_order(
        user_id=1,
        username="first",
        product_type=PRODUCT_STARS,
        stars_amount=100,
        telegram_username="@first",
        price_rub=130,
        status=STATUS_COMPLETED,
    )
    orders.create_order(
        user_id=2,
        username="second",
        product_type=PRODUCT_PREMIUM,
        premium_months=3,
        telegram_username="@second",
        price_rub=990,
        status=STATUS_COMPLETED,
    )
    orders.create_order(
        user_id=2,
        username="second",
        product_type=PRODUCT_STARS,
        stars_amount=50,
        telegram_username="@second",
        price_rub=65,
    )
    tickets.create_ticket(1, "first", "Вопрос")

    stats = StatisticsRepository(db_path).get_snapshot()

    assert stats.today_orders == 3
    assert stats.today_revenue == 1120
    assert stats.today_stars == 100
    assert stats.today_premium_months == 3
    assert stats.today_tickets == 1
    assert stats.total_orders == 3
    assert stats.completed_orders == 2
    assert stats.total_users == 2
    assert stats.total_stars == 100
    assert stats.total_premium_months == 3
    assert stats.total_revenue == 1120
    assert stats.today_users == 2
    assert stats.week_users == 2
