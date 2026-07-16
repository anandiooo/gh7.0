from __future__ import annotations

import sqlite3
from datetime import date, datetime

from src.db.connection import DatabasePath
from src.db.repositories._utils import RepositoryContext, row_values
from src.enums import BatchStatus
from src.errors import NotFoundError
from src.models import HarvestBatch


class HarvestRepository:
    def __init__(
        self,
        database_path: DatabasePath | None = None,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self._context = RepositoryContext(database_path, connection=connection)

    def create(self, batch: HarvestBatch) -> HarvestBatch:
        with self._context.open(write=True) as connection:
            self._insert(connection, batch)
        return batch

    def create_many(self, batches: list[HarvestBatch]) -> list[HarvestBatch]:
        with self._context.open(write=True) as connection:
            for batch in batches:
                self._insert(connection, batch)
        return batches

    def get_by_id(self, batch_id: str) -> HarvestBatch:
        with self._context.open() as connection:
            row = connection.execute(
                "SELECT * FROM harvest_batches WHERE id = ?", (batch_id,)
            ).fetchone()
        if row is None:
            raise NotFoundError(f"Harvest batch {batch_id!r} was not found")
        return HarvestBatch.model_validate(row_values(row))

    def list(self, *, status: BatchStatus | None = None) -> list[HarvestBatch]:
        with self._context.open() as connection:
            if status is None:
                rows = connection.execute(
                    "SELECT * FROM harvest_batches ORDER BY estimated_harvest_date, id"
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT * FROM harvest_batches
                    WHERE status = ? ORDER BY estimated_harvest_date, id
                    """,
                    (status.value,),
                ).fetchall()
        return [HarvestBatch.model_validate(row_values(row)) for row in rows]

    def list_planned_within(self, start_date: date, end_date: date) -> list[HarvestBatch]:
        with self._context.open() as connection:
            rows = connection.execute(
                """
                SELECT * FROM harvest_batches
                WHERE status = ? AND estimated_harvest_date BETWEEN ? AND ?
                ORDER BY estimated_harvest_date, id
                """,
                (BatchStatus.PLANNED.value, start_date.isoformat(), end_date.isoformat()),
            ).fetchall()
        return [HarvestBatch.model_validate(row_values(row)) for row in rows]

    def update(self, batch: HarvestBatch) -> HarvestBatch:
        with self._context.open(write=True) as connection:
            cursor = connection.execute(
                """
                UPDATE harvest_batches SET
                    farmer_id = ?, commodity_code = ?, estimated_harvest_date = ?,
                    estimated_quantity_kg = ?, grade = ?, confidence = ?, maturity_note = ?,
                    status = ?, source = ?, import_fingerprint = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    batch.farmer_id,
                    batch.commodity_code,
                    batch.estimated_harvest_date.isoformat(),
                    batch.estimated_quantity_kg,
                    batch.grade.value,
                    batch.confidence.value,
                    batch.maturity_note,
                    batch.status.value,
                    batch.source.value,
                    batch.import_fingerprint,
                    batch.updated_at.isoformat(),
                    batch.id,
                ),
            )
            self._ensure_found(cursor.rowcount, batch.id)
        return self.get_by_id(batch.id)

    def cancel(self, batch_id: str, updated_at: datetime) -> HarvestBatch:
        with self._context.open(write=True) as connection:
            cursor = connection.execute(
                "UPDATE harvest_batches SET status = ?, updated_at = ? WHERE id = ?",
                (BatchStatus.CANCELLED.value, updated_at.isoformat(), batch_id),
            )
            self._ensure_found(cursor.rowcount, batch_id)
        return self.get_by_id(batch_id)

    def count(self, *, status: BatchStatus | None = None) -> int:
        with self._context.open() as connection:
            if status is None:
                row = connection.execute("SELECT COUNT(*) AS count FROM harvest_batches").fetchone()
            else:
                row = connection.execute(
                    "SELECT COUNT(*) AS count FROM harvest_batches WHERE status = ?",
                    (status.value,),
                ).fetchone()
        return int(row["count"])

    def find_by_import_fingerprint(self, fingerprint: str) -> HarvestBatch | None:
        with self._context.open() as connection:
            row = connection.execute(
                "SELECT * FROM harvest_batches WHERE import_fingerprint = ?", (fingerprint,)
            ).fetchone()
        return HarvestBatch.model_validate(row_values(row)) if row else None

    @staticmethod
    def _insert(connection: sqlite3.Connection, batch: HarvestBatch) -> None:
        connection.execute(
            """
            INSERT INTO harvest_batches (
                id, farmer_id, commodity_code, estimated_harvest_date,
                estimated_quantity_kg, grade, confidence, maturity_note, status, source,
                import_fingerprint, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                batch.id,
                batch.farmer_id,
                batch.commodity_code,
                batch.estimated_harvest_date.isoformat(),
                batch.estimated_quantity_kg,
                batch.grade.value,
                batch.confidence.value,
                batch.maturity_note,
                batch.status.value,
                batch.source.value,
                batch.import_fingerprint,
                batch.created_at.isoformat(),
                batch.updated_at.isoformat(),
            ),
        )

    @staticmethod
    def _ensure_found(row_count: int, batch_id: str) -> None:
        if row_count == 0:
            raise NotFoundError(f"Harvest batch {batch_id!r} was not found")


__all__ = ["HarvestRepository"]
