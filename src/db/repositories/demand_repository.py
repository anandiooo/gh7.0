from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime

from src.db.connection import DatabasePath
from src.db.repositories._utils import RepositoryContext, row_values
from src.enums import DemandStatus
from src.errors import NotFoundError
from src.models import BuyerDemand


class DemandRepository:
    def __init__(
        self,
        database_path: DatabasePath | None = None,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self._context = RepositoryContext(database_path, connection=connection)

    def create(self, demand: BuyerDemand) -> BuyerDemand:
        with self._context.open(write=True) as connection:
            self._insert(connection, demand)
        return demand

    def create_many(self, demands: list[BuyerDemand]) -> list[BuyerDemand]:
        with self._context.open(write=True) as connection:
            for demand in demands:
                self._insert(connection, demand)
        return demands

    def get_by_id(self, demand_id: str) -> BuyerDemand:
        with self._context.open() as connection:
            row = connection.execute(
                "SELECT * FROM buyer_demands WHERE id = ?", (demand_id,)
            ).fetchone()
        if row is None:
            raise NotFoundError(f"Buyer demand {demand_id!r} was not found")
        return self._map(row)

    def list(self, *, status: DemandStatus | None = None) -> list[BuyerDemand]:
        with self._context.open() as connection:
            if status is None:
                rows = connection.execute(
                    "SELECT * FROM buyer_demands ORDER BY deadline, id"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM buyer_demands WHERE status = ? ORDER BY deadline, id",
                    (status.value,),
                ).fetchall()
        return [self._map(row) for row in rows]

    def list_open_within(self, start_date: date, end_date: date) -> list[BuyerDemand]:
        with self._context.open() as connection:
            rows = connection.execute(
                """
                SELECT * FROM buyer_demands
                WHERE status = ? AND deadline BETWEEN ? AND ?
                ORDER BY deadline, id
                """,
                (DemandStatus.OPEN.value, start_date.isoformat(), end_date.isoformat()),
            ).fetchall()
        return [self._map(row) for row in rows]

    def update(self, demand: BuyerDemand) -> BuyerDemand:
        with self._context.open(write=True) as connection:
            cursor = connection.execute(
                """
                UPDATE buyer_demands SET
                    buyer_id = ?, commodity_code = ?, quantity_kg = ?,
                    accepted_grades_json = ?, deadline = ?, priority = ?, status = ?,
                    source = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    demand.buyer_id,
                    demand.commodity_code,
                    demand.quantity_kg,
                    self._serialize_grades(demand),
                    demand.deadline.isoformat(),
                    demand.priority,
                    demand.status.value,
                    demand.source.value,
                    demand.updated_at.isoformat(),
                    demand.id,
                ),
            )
            self._ensure_found(cursor.rowcount, demand.id)
        return self.get_by_id(demand.id)

    def close(self, demand_id: str, updated_at: datetime) -> BuyerDemand:
        with self._context.open(write=True) as connection:
            cursor = connection.execute(
                "UPDATE buyer_demands SET status = ?, updated_at = ? WHERE id = ?",
                (DemandStatus.CLOSED.value, updated_at.isoformat(), demand_id),
            )
            self._ensure_found(cursor.rowcount, demand_id)
        return self.get_by_id(demand_id)

    def count(self, *, status: DemandStatus | None = None) -> int:
        with self._context.open() as connection:
            if status is None:
                row = connection.execute("SELECT COUNT(*) AS count FROM buyer_demands").fetchone()
            else:
                row = connection.execute(
                    "SELECT COUNT(*) AS count FROM buyer_demands WHERE status = ?",
                    (status.value,),
                ).fetchone()
        return int(row["count"])

    @classmethod
    def _insert(cls, connection: sqlite3.Connection, demand: BuyerDemand) -> None:
        connection.execute(
            """
            INSERT INTO buyer_demands (
                id, buyer_id, commodity_code, quantity_kg, accepted_grades_json,
                deadline, priority, status, source, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                demand.id,
                demand.buyer_id,
                demand.commodity_code,
                demand.quantity_kg,
                cls._serialize_grades(demand),
                demand.deadline.isoformat(),
                demand.priority,
                demand.status.value,
                demand.source.value,
                demand.created_at.isoformat(),
                demand.updated_at.isoformat(),
            ),
        )

    @staticmethod
    def _serialize_grades(demand: BuyerDemand) -> str:
        return json.dumps([grade.value for grade in demand.accepted_grades], separators=(",", ":"))

    @staticmethod
    def _map(row: sqlite3.Row) -> BuyerDemand:
        values = row_values(row)
        values["accepted_grades"] = json.loads(str(values.pop("accepted_grades_json")))
        return BuyerDemand.model_validate(values)

    @staticmethod
    def _ensure_found(row_count: int, demand_id: str) -> None:
        if row_count == 0:
            raise NotFoundError(f"Buyer demand {demand_id!r} was not found")


__all__ = ["DemandRepository"]
