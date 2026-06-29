from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from database.db import DEFAULT_DB_PATH, get_connection, init_db
from database.orders import PRODUCT_PREMIUM, PRODUCT_STARS, STATUS_COMPLETED


@dataclass(frozen=True)
class StatisticsSnapshot:
    today_orders: int
    today_revenue: int
    today_stars: int
    today_premium_months: int
    today_tickets: int
    total_orders: int
    completed_orders: int
    total_users: int
    total_stars: int
    total_premium_months: int
    total_revenue: int
    today_users: int
    week_users: int


class StatisticsRepository:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        init_db(self.db_path)

    def get_snapshot(self, today: Optional[date] = None) -> StatisticsSnapshot:
        current_date = today or date.today()
        date_prefix = f"{current_date.isoformat()}%"
        week_start = (current_date - timedelta(days=6)).isoformat()

        with get_connection(self.db_path) as connection:
            today_orders = connection.execute(
                "SELECT COUNT(*) FROM orders WHERE created_at LIKE ?",
                (date_prefix,),
            ).fetchone()[0]
            today_sales = connection.execute(
                """
                SELECT
                    COALESCE(SUM(price_rub), 0),
                    COALESCE(SUM(CASE WHEN product_type = ? THEN stars_amount ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN product_type = ? THEN premium_months ELSE 0 END), 0)
                FROM orders
                WHERE status = ? AND created_at LIKE ?
                """,
                (
                    PRODUCT_STARS,
                    PRODUCT_PREMIUM,
                    STATUS_COMPLETED,
                    date_prefix,
                ),
            ).fetchone()
            today_tickets = connection.execute(
                "SELECT COUNT(*) FROM support_tickets WHERE created_at LIKE ?",
                (date_prefix,),
            ).fetchone()[0]
            total_orders = connection.execute(
                "SELECT COUNT(*) FROM orders"
            ).fetchone()[0]
            total_sales = connection.execute(
                """
                SELECT
                    COUNT(*),
                    COALESCE(SUM(price_rub), 0),
                    COALESCE(SUM(CASE WHEN product_type = ? THEN stars_amount ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN product_type = ? THEN premium_months ELSE 0 END), 0)
                FROM orders
                WHERE status = ?
                """,
                (PRODUCT_STARS, PRODUCT_PREMIUM, STATUS_COMPLETED),
            ).fetchone()
            total_users = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            today_users = connection.execute(
                "SELECT COUNT(*) FROM users WHERE registered_at LIKE ?",
                (date_prefix,),
            ).fetchone()[0]
            week_users = connection.execute(
                """
                SELECT COUNT(*) FROM users
                WHERE substr(registered_at, 1, 10) >= ?
                """,
                (week_start,),
            ).fetchone()[0]

        return StatisticsSnapshot(
            today_orders=today_orders,
            today_revenue=today_sales[0],
            today_stars=today_sales[1],
            today_premium_months=today_sales[2],
            today_tickets=today_tickets,
            total_orders=total_orders,
            completed_orders=total_sales[0],
            total_users=total_users,
            total_stars=total_sales[2],
            total_premium_months=total_sales[3],
            total_revenue=total_sales[1],
            today_users=today_users,
            week_users=week_users,
        )
