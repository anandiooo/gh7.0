import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from src.config import DB_PATH, SQLITE_BUSY_TIMEOUT_MS
from src.errors import DatabaseError

DatabasePath = str | Path


def resolve_database_path(database_path: DatabasePath | None = None) -> Path:
    """Return the configured database path without opening or creating it."""
    return Path(database_path) if database_path is not None else DB_PATH


@contextmanager
def connection_context(
    database_path: DatabasePath | None = None, *, create_parent: bool = False
) -> Iterator[sqlite3.Connection]:
    """Open one configured SQLite connection and always close it after use."""
    path = resolve_database_path(database_path)
    try:
        if create_parent:
            path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            path,
            timeout=SQLITE_BUSY_TIMEOUT_MS / 1000,
            isolation_level=None,
        )
    except (OSError, sqlite3.Error) as exc:
        raise DatabaseError("Unable to open the SQLite database") from exc
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        yield connection
    finally:
        connection.close()


@contextmanager
def transaction(connection: sqlite3.Connection, *, immediate: bool = False) -> Iterator[None]:
    """Run a transaction that commits on success and rolls back on every error."""
    if connection.in_transaction:
        yield
        return
    try:
        connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
        yield
        connection.commit()
    except Exception:
        if connection.in_transaction:
            connection.rollback()
        raise
