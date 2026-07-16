from __future__ import annotations

import sqlite3

from src.db.connection import DatabasePath
from src.db.repositories._utils import RepositoryContext


class WorkspaceRepository:
    def __init__(
        self,
        database_path: DatabasePath | None = None,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self._context = RepositoryContext(database_path, connection=connection)

    def clear_operational_data(self) -> None:
        with self._context.open(write=True) as connection:
            for statement in (
                "DELETE FROM allocations",
                "DELETE FROM analysis_runs",
                "DELETE FROM weather_snapshots",
                "DELETE FROM distribution_capacities",
                "DELETE FROM buyer_demands",
                "DELETE FROM buyers",
                "DELETE FROM harvest_batches",
                "DELETE FROM farmers",
                "DELETE FROM cooperative_profiles",
            ):
                connection.execute(statement)


__all__ = ["WorkspaceRepository"]
