from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from database.db import DEFAULT_DB_PATH, get_connection, init_db


STATUS_OPEN = "open"
STATUS_ANSWERED = "answered"
STATUS_CLOSED = "closed"


@dataclass(frozen=True)
class SupportTicket:
    id: int
    user_id: int
    username: Optional[str]
    message: str
    related_order_id: Optional[int]
    status: str
    admin_reply: Optional[str]
    created_at: str
    answered_at: Optional[str]


class SupportTicketRepository:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        init_db(self.db_path)

    def create_ticket(
        self,
        user_id: int,
        username: Optional[str],
        message: str,
        related_order_id: Optional[int] = None,
    ) -> SupportTicket:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_connection(self.db_path) as connection:
            ticket_id = _insert_ticket(
                connection,
                user_id,
                username,
                message,
                related_order_id,
                created_at,
            )

        ticket = self.get_ticket(ticket_id)
        if ticket is None:
            raise RuntimeError("Созданное обращение не найдено")
        return ticket

    def create_ticket_if_no_open(
        self,
        user_id: int,
        username: Optional[str],
        message: str,
        related_order_id: Optional[int] = None,
    ) -> Tuple[SupportTicket, bool]:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_connection(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                """
                SELECT * FROM support_tickets
                WHERE user_id = ? AND status = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (user_id, STATUS_OPEN),
            ).fetchone()
            if existing:
                return _ticket_from_row(existing), False

            ticket_id = _insert_ticket(
                connection,
                user_id,
                username,
                message,
                related_order_id,
                created_at,
            )
            row = connection.execute(
                "SELECT * FROM support_tickets WHERE id = ?",
                (ticket_id,),
            ).fetchone()

        if row is None:
            raise RuntimeError("Созданное обращение не найдено")
        return _ticket_from_row(row), True

    def get_ticket(self, ticket_id: int) -> Optional[SupportTicket]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                "SELECT * FROM support_tickets WHERE id = ?",
                (ticket_id,),
            ).fetchone()

        return _ticket_from_row(row) if row else None

    def update_status(self, ticket_id: int, status: str) -> Optional[SupportTicket]:
        with get_connection(self.db_path) as connection:
            connection.execute(
                "UPDATE support_tickets SET status = ? WHERE id = ?",
                (status, ticket_id),
            )

        return self.get_ticket(ticket_id)

    def answer_ticket(
        self,
        ticket_id: int,
        admin_reply: str,
    ) -> Optional[SupportTicket]:
        answered_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                UPDATE support_tickets
                SET status = ?, admin_reply = ?, answered_at = ?
                WHERE id = ?
                """,
                (STATUS_ANSWERED, admin_reply, answered_at, ticket_id),
            )

        return self.get_ticket(ticket_id)

    def list_tickets(
        self,
        status: Optional[str] = None,
        statuses: Optional[Sequence[str]] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[SupportTicket]:
        with get_connection(self.db_path) as connection:
            selected_statuses = tuple(statuses or ())
            if status is not None:
                selected_statuses = (status,)

            if not selected_statuses:
                rows = connection.execute(
                    """
                    SELECT * FROM support_tickets
                    ORDER BY id DESC
                    LIMIT ? OFFSET ?
                    """,
                    (limit, offset),
                ).fetchall()
            else:
                placeholders = ", ".join("?" for _ in selected_statuses)
                rows = connection.execute(
                    f"""
                    SELECT * FROM support_tickets
                    WHERE status IN ({placeholders})
                    ORDER BY id DESC
                    LIMIT ? OFFSET ?
                    """,
                    (*selected_statuses, limit, offset),
                ).fetchall()

        return [_ticket_from_row(row) for row in rows]

    def list_user_tickets(
        self,
        user_id: int,
        limit: int = 15,
    ) -> List[SupportTicket]:
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT * FROM support_tickets
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()

        return [_ticket_from_row(row) for row in rows]


def _insert_ticket(
    connection,
    user_id: int,
    username: Optional[str],
    message: str,
    related_order_id: Optional[int],
    created_at: str,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO support_tickets (
            user_id,
            username,
            message,
            related_order_id,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            username,
            message,
            related_order_id,
            STATUS_OPEN,
            created_at,
        ),
    )
    return cursor.lastrowid


def _ticket_from_row(row) -> SupportTicket:
    return SupportTicket(
        id=row["id"],
        user_id=row["user_id"],
        username=row["username"],
        message=row["message"],
        related_order_id=row["related_order_id"],
        status=row["status"],
        admin_reply=row["admin_reply"],
        created_at=row["created_at"],
        answered_at=row["answered_at"],
    )
