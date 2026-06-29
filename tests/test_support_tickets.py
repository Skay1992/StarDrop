from database.support import STATUS_ANSWERED, STATUS_CLOSED, STATUS_OPEN, SupportTicketRepository


def test_user_can_create_support_ticket(tmp_path):
    repository = SupportTicketRepository(tmp_path / "support.sqlite3")

    ticket = repository.create_ticket(
        user_id=123,
        username="client",
        message="Когда придут звезды?",
    )

    assert ticket.id == 1
    assert ticket.user_id == 123
    assert ticket.username == "client"
    assert ticket.message == "Когда придут звезды?"
    assert ticket.status == STATUS_OPEN
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
