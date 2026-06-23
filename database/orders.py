from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from database.db import DEFAULT_DB_PATH, get_connection, init_db


PRODUCT_STARS = "stars"
PRODUCT_PREMIUM = "premium"

STATUS_AWAITING_PAYMENT = "awaiting_payment"
STATUS_PENDING_REVIEW = "pending_review"
STATUS_COMPLETED = "completed"
STATUS_CANCELLED = "cancelled"


@dataclass(frozen=True)
class Order:
    id: int
    user_id: int
    username: Optional[str]
    product_type: str
    stars_amount: Optional[int]
    premium_months: Optional[int]
    telegram_username: str
    price_rub: int
    status: str
    created_at: str


class OrderRepository:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        init_db(self.db_path)

    def create_order(
        self,
        user_id: int,
        username: Optional[str],
        product_type: str,
        telegram_username: str,
        price_rub: int,
        stars_amount: Optional[int] = None,
        premium_months: Optional[int] = None,
        status: str = STATUS_AWAITING_PAYMENT,
    ) -> Order:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO orders (
                    user_id,
                    username,
                    product_type,
                    stars_amount,
                    premium_months,
                    telegram_username,
                    price_rub,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    username,
                    product_type,
                    stars_amount,
                    premium_months,
                    telegram_username,
                    price_rub,
                    status,
                    created_at,
                ),
            )
            order_id = cursor.lastrowid

        order = self.get_order(order_id)
        if order is None:
            raise RuntimeError("Created order was not found")
        return order

    def get_order(self, order_id: int) -> Optional[Order]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                "SELECT * FROM orders WHERE id = ?",
                (order_id,),
            ).fetchone()

        return _order_from_row(row) if row else None

    def update_status(self, order_id: int, status: str) -> Optional[Order]:
        with get_connection(self.db_path) as connection:
            connection.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (status, order_id),
            )

        return self.get_order(order_id)

    def list_user_orders(self, user_id: int, limit: int = 5) -> List[Order]:
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT * FROM orders
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()

        return [_order_from_row(row) for row in rows]


def _order_from_row(row) -> Order:
    return Order(
        id=row["id"],
        user_id=row["user_id"],
        username=row["username"],
        product_type=row["product_type"],
        stars_amount=row["stars_amount"],
        premium_months=row["premium_months"],
        telegram_username=row["telegram_username"],
        price_rub=row["price_rub"],
        status=row["status"],
        created_at=row["created_at"],
    )
