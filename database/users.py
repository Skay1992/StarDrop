from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from database.db import DEFAULT_DB_PATH, get_connection, init_db
from database.orders import (
    Order,
    PRODUCT_PREMIUM,
    PRODUCT_STARS,
    STATUS_COMPLETED,
)


@dataclass(frozen=True)
class User:
    user_id: int
    username: Optional[str]
    registered_at: str
    orders_count: int
    stars_bought: int
    premium_months: int
    referral_code: str
    invited_by: Optional[int]
    referrals_count: int


class UserRepository:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        init_db(self.db_path)

    def register_user(
        self,
        user_id: int,
        username: Optional[str],
        invited_by_code: Optional[str] = None,
    ) -> Tuple[User, bool]:
        registered_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        referral_code = f"SD{user_id}"

        with get_connection(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if existing:
                return _user_from_row(existing), False

            invited_by = None
            if invited_by_code:
                referrer = connection.execute(
                    "SELECT user_id FROM users WHERE referral_code = ?",
                    (invited_by_code,),
                ).fetchone()
                if referrer:
                    invited_by = referrer["user_id"]

            purchase_totals = connection.execute(
                """
                SELECT
                    COUNT(*),
                    COALESCE(SUM(CASE WHEN product_type = ? THEN stars_amount ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN product_type = ? THEN premium_months ELSE 0 END), 0)
                FROM orders
                WHERE user_id = ? AND status = ?
                """,
                (PRODUCT_STARS, PRODUCT_PREMIUM, user_id, STATUS_COMPLETED),
            ).fetchone()

            connection.execute(
                """
                INSERT INTO users (
                    user_id,
                    username,
                    registered_at,
                    orders_count,
                    stars_bought,
                    premium_months,
                    referral_code,
                    invited_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    username,
                    registered_at,
                    purchase_totals[0],
                    purchase_totals[1],
                    purchase_totals[2],
                    referral_code,
                    invited_by,
                ),
            )
            if invited_by is not None:
                connection.execute(
                    """
                    UPDATE users
                    SET referrals_count = referrals_count + 1
                    WHERE user_id = ?
                    """,
                    (invited_by,),
                )
            row = connection.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()

        if row is None:
            raise RuntimeError("Созданный пользователь не найден")
        return _user_from_row(row), True

    def get_user(self, user_id: int) -> Optional[User]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()

        return _user_from_row(row) if row else None

    def list_recent_users(self, limit: int = 5) -> List[User]:
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT * FROM users
                ORDER BY registered_at DESC, user_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [_user_from_row(row) for row in rows]

    def record_completed_order(self, order: Order) -> Optional[User]:
        registered_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stars = order.stars_amount if order.product_type == PRODUCT_STARS else 0
        premium = (
            order.premium_months if order.product_type == PRODUCT_PREMIUM else 0
        )
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO users (
                    user_id,
                    username,
                    registered_at,
                    referral_code
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    order.user_id,
                    order.username,
                    registered_at,
                    f"SD{order.user_id}",
                ),
            )
            connection.execute(
                """
                UPDATE users
                SET
                    orders_count = orders_count + 1,
                    stars_bought = stars_bought + ?,
                    premium_months = premium_months + ?
                WHERE user_id = ?
                """,
                (stars or 0, premium or 0, order.user_id),
            )

        return self.get_user(order.user_id)


def _user_from_row(row) -> User:
    return User(
        user_id=row["user_id"],
        username=row["username"],
        registered_at=row["registered_at"],
        orders_count=row["orders_count"],
        stars_bought=row["stars_bought"],
        premium_months=row["premium_months"],
        referral_code=row["referral_code"],
        invited_by=row["invited_by"],
        referrals_count=row["referrals_count"],
    )
