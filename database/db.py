import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path("stardrop.sqlite3")


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    with get_connection(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                product_type TEXT NOT NULL,
                stars_amount INTEGER,
                premium_months INTEGER,
                telegram_username TEXT NOT NULL,
                price_rub INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                message TEXT NOT NULL,
                related_order_id INTEGER,
                status TEXT NOT NULL,
                admin_reply TEXT,
                created_at TEXT NOT NULL,
                answered_at TEXT
            )
            """
        )
        _ensure_support_ticket_columns(connection)


def _ensure_support_ticket_columns(connection: sqlite3.Connection) -> None:
    existing = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(support_tickets)").fetchall()
    }
    columns = {
        "related_order_id": "INTEGER",
        "admin_reply": "TEXT",
        "answered_at": "TEXT",
    }
    for name, column_type in columns.items():
        if name not in existing:
            connection.execute(
                f"ALTER TABLE support_tickets ADD COLUMN {name} {column_type}"
            )
