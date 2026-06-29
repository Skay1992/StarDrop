import sqlite3

from database.db import init_db
from database.support import STATUS_ANSWERED, STATUS_CLOSED, STATUS_OPEN, SupportTicketRepository


def test_user_can_create_support_ticket(tmp_path):
    repository = SupportTicketRepository(tmp_path / "support.sqlite3")

    ticket = repository.create_ticket(
        user_id=123,
        username="client",
        message="Когда придут звезды?",
        related_order_id=42,
    )

    assert ticket.id == 1
    assert ticket.user_id == 123
    assert ticket.username == "client"
    assert ticket.message == "Когда придут звезды?"
    assert ticket.related_order_id == 42
    assert ticket.status == STATUS_OPEN
    assert ticket.admin_reply is None
    assert ticket.answered_at is None
    assert ticket.created_at


def test_support_ticket_status_can_be_answered_and_closed(tmp_path):
    repository = SupportTicketRepository(tmp_path / "support.sqlite3")
    ticket = repository.create_ticket(123, "client", "Нужна помощь")

    answered = repository.update_status(ticket.id, STATUS_ANSWERED)
    closed = repository.update_status(ticket.id, STATUS_CLOSED)

    assert answered.status == STATUS_ANSWERED
    assert closed.status == STATUS_CLOSED


def test_support_ticket_list_returns_latest_ten(tmp_path):
    repository = SupportTicketRepository(tmp_path / "support.sqlite3")
    for number in range(1, 13):
        repository.create_ticket(123, "client", f"Вопрос {number}")

    tickets = repository.list_tickets(limit=10)

    assert [ticket.id for ticket in tickets] == list(range(12, 2, -1))


def test_second_open_ticket_is_not_created(tmp_path):
    repository = SupportTicketRepository(tmp_path / "support.sqlite3")

    first, first_created = repository.create_ticket_if_no_open(
        123,
        "client",
        "Первый вопрос",
        related_order_id=7,
    )
    second, second_created = repository.create_ticket_if_no_open(
        123,
        "client",
        "Второй вопрос",
        related_order_id=8,
    )

    assert first_created is True
    assert second_created is False
    assert second.id == first.id
    assert second.message == "Первый вопрос"
    assert [ticket.id for ticket in repository.list_tickets()] == [first.id]


def test_answer_is_saved_with_timestamp(tmp_path):
    repository = SupportTicketRepository(tmp_path / "support.sqlite3")
    ticket = repository.create_ticket(123, "client", "Нужна помощь")

    answered = repository.answer_ticket(ticket.id, "Все готово.")

    assert answered.status == STATUS_ANSWERED
    assert answered.admin_reply == "Все готово."
    assert answered.answered_at


def test_existing_support_table_is_migrated_without_losing_tickets(tmp_path):
    db_path = tmp_path / "support.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                message TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO support_tickets (
                user_id, username, message, status, created_at
            )
            VALUES (123, 'client', 'Старое обращение', 'open', '2026-06-29 12:00:00')
            """
        )

    init_db(db_path)
    ticket = SupportTicketRepository(db_path).get_ticket(1)

    assert ticket.message == "Старое обращение"
    assert ticket.related_order_id is None
    assert ticket.admin_reply is None
    assert ticket.answered_at is None


def test_support_ticket_list_can_filter_by_status(tmp_path):
    repository = SupportTicketRepository(tmp_path / "support.sqlite3")
    open_ticket = repository.create_ticket(1, "open_user", "Открыто")
    answered_ticket = repository.create_ticket(2, "answered_user", "Отвечено")
    closed_ticket = repository.create_ticket(3, "closed_user", "Закрыто")
    repository.answer_ticket(answered_ticket.id, "Ответ")
    repository.update_status(closed_ticket.id, STATUS_CLOSED)

    open_tickets = repository.list_tickets(status=STATUS_OPEN, limit=10)
    answered_tickets = repository.list_tickets(status=STATUS_ANSWERED, limit=10)
    closed_tickets = repository.list_tickets(status=STATUS_CLOSED, limit=10)

    assert [ticket.id for ticket in open_tickets] == [open_ticket.id]
    assert [ticket.id for ticket in answered_tickets] == [answered_ticket.id]
    assert [ticket.id for ticket in closed_tickets] == [closed_ticket.id]


def test_user_ticket_history_contains_only_own_latest_tickets(tmp_path):
    repository = SupportTicketRepository(tmp_path / "support.sqlite3")
    first = repository.create_ticket(123, "client", "Первое")
    repository.create_ticket(999, "other", "Чужое")
    latest = repository.create_ticket(123, "client", "Последнее")

    tickets = repository.list_user_tickets(123, limit=15)

    assert [ticket.id for ticket in tickets] == [latest.id, first.id]
