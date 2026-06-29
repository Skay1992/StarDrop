from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

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
    status: str
    created_at: str


class SupportTicketRepository:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        init_db(self.db_path)

    def create_ticket(
        self,
        user_id: int,
        username: Optional[str],
        message: str,
    ) -> SupportTicket:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO support_tickets (
                    user_id,
                    username,
                    message,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, username, message, STATUS_OPEN, created_at),
            )
            ticket_id = cursor.lastrowid

        ticket = self.get_ticket(ticket_id)
        if ticket is None:
            raise RuntimeError("Созданное обращение не найдено")
        return ticket

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

    def list_tickets(self, limit: int = 10) -> List[SupportTicket]:
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT * FROM support_tickets
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [_ticket_from_row(row) for row in rows]


def _ticket_from_row(row) -> SupportTicket:
    return SupportTicket(
        id=row["id"],
        user_id=row["user_id"],
        username=row["username"],
        message=row["message"],
        status=row["status"],
        created_at=row["created_at"],
    )
