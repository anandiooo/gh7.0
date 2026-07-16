import sqlite3
from datetime import datetime
from pathlib import Path

from src.config import APP_TIMEZONE, SCHEMA_VERSION
from src.db.connection import DatabasePath, connection_context, transaction
from src.errors import DatabaseError

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def initialize_schema(database_path: DatabasePath | None = None) -> None:
    """Create the versioned schema idempotently at an explicitly requested path."""
    try:
        statements = _read_schema_statements()
        with (
            connection_context(database_path, create_parent=True) as connection,
            transaction(connection, immediate=True),
        ):
            for statement in statements:
                connection.execute(statement)
            connection.execute(
                """
                INSERT INTO schema_metadata (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (
                    "schema_version",
                    str(SCHEMA_VERSION),
                    datetime.now(APP_TIMEZONE).isoformat(),
                ),
            )
    except (OSError, sqlite3.Error) as exc:
        raise DatabaseError("Unable to initialize the SQLite schema") from exc


def _read_schema_statements() -> list[str]:
    schema = _SCHEMA_PATH.read_text(encoding="utf-8")
    return [statement.strip() for statement in schema.split(";") if statement.strip()]
