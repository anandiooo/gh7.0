from __future__ import annotations

import sqlite3
from datetime import date

from src.db.connection import DatabasePath
from src.db.repositories._utils import RepositoryContext, row_values
from src.errors import DatabaseError
from src.models import DistributionCapacity


class CapacityRepository:
    def __init__(
        self,
        database_path: DatabasePath | None = None,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self._context = RepositoryContext(database_path, connection=connection)

    def upsert_by_date(self, capacity: DistributionCapacity) -> DistributionCapacity:
        with self._context.open(write=True) as connection:
            connection.execute(
                """
                INSERT INTO distribution_capacities (
                    id, date, available_capacity_kg, source, note, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    available_capacity_kg = excluded.available_capacity_kg,
                    source = excluded.source,
                    note = excluded.note,
                    updated_at = excluded.updated_at
                """,
                (
                    capacity.id,
                    capacity.date.isoformat(),
                    capacity.available_capacity_kg,
                    capacity.source.value,
                    capacity.note,
                    capacity.created_at.isoformat(),
                    capacity.updated_at.isoformat(),
                ),
            )
        stored = self.get_by_date(capacity.date)
        if stored is None:
            raise DatabaseError("Capacity upsert completed without a readable record")
        return stored

    def get_by_date(self, capacity_date: date) -> DistributionCapacity | None:
        with self._context.open() as connection:
            row = connection.execute(
                "SELECT * FROM distribution_capacities WHERE date = ?",
                (capacity_date.isoformat(),),
            ).fetchone()
        return DistributionCapacity.model_validate(row_values(row)) if row else None

    def list_date_range(self, start_date: date, end_date: date) -> list[DistributionCapacity]:
        with self._context.open() as connection:
            rows = connection.execute(
                """
                SELECT * FROM distribution_capacities
                WHERE date BETWEEN ? AND ? ORDER BY date, id
                """,
                (start_date.isoformat(), end_date.isoformat()),
            ).fetchall()
        return [DistributionCapacity.model_validate(row_values(row)) for row in rows]

    def list_all(self) -> list[DistributionCapacity]:
        with self._context.open() as connection:
            rows = connection.execute(
                "SELECT * FROM distribution_capacities ORDER BY date, id"
            ).fetchall()
        return [DistributionCapacity.model_validate(row_values(row)) for row in rows]

    def count(self) -> int:
        with self._context.open() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM distribution_capacities"
            ).fetchone()
        return int(row["count"])


__all__ = ["CapacityRepository"]
