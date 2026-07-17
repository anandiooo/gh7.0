from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from src.db.connection import DatabasePath, connection_context, transaction
from src.errors import ConflictError, DatabaseError, TetaniError


class RepositoryContext:
    def __init__(
        self,
        database_path: DatabasePath | None = None,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self.database_path = database_path
        self.connection = connection

    @contextmanager
    def open(self, *, write: bool = False) -> Iterator[sqlite3.Connection]:
        try:
            if self.connection is not None:
                if write:
                    with transaction(self.connection):
                        yield self.connection
                else:
                    yield self.connection
                return
            with connection_context(self.database_path) as connection:
                if write:
                    with transaction(connection):
                        yield connection
                else:
                    yield connection
        except TetaniError:
            raise
        except sqlite3.IntegrityError as exc:
            raise ConflictError(
                "A database integrity rule rejected the operation",
                user_message=(
                    "Data bertentangan dengan data yang ada. / "
                    "Data conflicts with existing records."
                ),
            ) from exc
        except sqlite3.Error as exc:
            raise DatabaseError(
                "A SQLite repository operation failed",
                user_message="Database tidak dapat diakses. / The database could not be accessed.",
            ) from exc


def row_values(row: sqlite3.Row) -> dict[str, object]:
    return dict(row)
