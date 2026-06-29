from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from database.db import DEFAULT_DB_PATH, get_connection, init_db


PRODUCT_STARS = "stars"
PRODUCT_PREMIUM = "premium"

STATUS_AWAITING_PAYMENT = "awaiting_payment"
STATUS_PENDING_REVIEW = "pending_review"
STATUS_COMPLETED = "completed"
STATUS_CANCELLED = "cancelled"
ORDER_COOLDOWN_SECONDS = 5


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

    def create_order_if_allowed(
        self,
        user_id: int,
        username: Optional[str],
        product_type: str,
        telegram_username: str,
        price_rub: int,
        stars_amount: Optional[int] = None,
        premium_months: Optional[int] = None,
        status: str = STATUS_AWAITING_PAYMENT,
        cooldown_seconds: int = ORDER_COOLDOWN_SECONDS,
    ) -> Tuple[Order, bool]:
        created_at = datetime.now()
        with get_connection(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            latest = connection.execute(
                """
                SELECT * FROM orders
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
            if latest is not None:
                latest_created_at = datetime.strptime(
                    latest["created_at"],
                    "%Y-%m-%d %H:%M:%S",
                )
                if (created_at - latest_created_at).total_seconds() < cooldown_seconds:
                    return _order_from_row(latest), False

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
                    created_at.strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            row = connection.execute(
                "SELECT * FROM orders WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()

        if row is None:
            raise RuntimeError("Созданный заказ не найден")
        return _order_from_row(row), True

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

    def transition_status(
        self,
        order_id: int,
        expected_status: str,
        new_status: str,
    ) -> Optional[Order]:
        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                """
                UPDATE orders
                SET status = ?
                WHERE id = ? AND status = ?
                """,
                (new_status, order_id, expected_status),
            )
            if cursor.rowcount != 1:
                return None

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

    def list_orders(self, status: Optional[str] = None, limit: int = 10) -> List[Order]:
        with get_connection(self.db_path) as connection:
            if status is None:
                rows = connection.execute(
                    """
                    SELECT * FROM orders
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT * FROM orders
                    WHERE status = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (status, limit),
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
