from __future__ import annotations

import sqlite3
from datetime import datetime

from src.db.connection import DatabasePath
from src.db.repositories._utils import RepositoryContext, row_values
from src.errors import NotFoundError
from src.models import Farmer


class FarmerRepository:
    def __init__(
        self,
        database_path: DatabasePath | None = None,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self._context = RepositoryContext(database_path, connection=connection)

    def create(self, farmer: Farmer) -> Farmer:
        with self._context.open(write=True) as connection:
            self._insert(connection, farmer)
        return farmer

    def create_many(self, farmers: list[Farmer]) -> list[Farmer]:
        with self._context.open(write=True) as connection:
            for farmer in farmers:
                self._insert(connection, farmer)
        return farmers

    def get_by_id(self, farmer_id: str) -> Farmer:
        with self._context.open() as connection:
            row = connection.execute("SELECT * FROM farmers WHERE id = ?", (farmer_id,)).fetchone()
        if row is None:
            raise NotFoundError(f"Farmer {farmer_id!r} was not found")
        return Farmer.model_validate(row_values(row))

    def list(self, *, active: bool | None = None) -> list[Farmer]:
        with self._context.open() as connection:
            if active is None:
                rows = connection.execute("SELECT * FROM farmers ORDER BY name, id").fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM farmers WHERE active = ? ORDER BY name, id", (int(active),)
                ).fetchall()
        return [Farmer.model_validate(row_values(row)) for row in rows]

    def update(self, farmer: Farmer) -> Farmer:
        with self._context.open(write=True) as connection:
            cursor = connection.execute(
                """
                UPDATE farmers SET
                    name = ?, village_name = ?, subdistrict_name = ?, active = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    farmer.name,
                    farmer.village_name,
                    farmer.subdistrict_name,
                    int(farmer.active),
                    farmer.updated_at.isoformat(),
                    farmer.id,
                ),
            )
            self._ensure_found(cursor.rowcount, farmer.id)
        return self.get_by_id(farmer.id)

    def deactivate(self, farmer_id: str, updated_at: datetime) -> Farmer:
        with self._context.open(write=True) as connection:
            cursor = connection.execute(
                "UPDATE farmers SET active = ?, updated_at = ? WHERE id = ?",
                (0, updated_at.isoformat(), farmer_id),
            )
            self._ensure_found(cursor.rowcount, farmer_id)
        return self.get_by_id(farmer_id)

    def count(self, *, active: bool | None = None) -> int:
        with self._context.open() as connection:
            if active is None:
                row = connection.execute("SELECT COUNT(*) AS count FROM farmers").fetchone()
            else:
                row = connection.execute(
                    "SELECT COUNT(*) AS count FROM farmers WHERE active = ?", (int(active),)
                ).fetchone()
        return int(row["count"])

    @staticmethod
    def _insert(connection: sqlite3.Connection, farmer: Farmer) -> None:
        connection.execute(
            """
            INSERT INTO farmers (
                id, name, village_name, subdistrict_name, active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                farmer.id,
                farmer.name,
                farmer.village_name,
                farmer.subdistrict_name,
                int(farmer.active),
                farmer.created_at.isoformat(),
                farmer.updated_at.isoformat(),
            ),
        )

    @staticmethod
    def _ensure_found(row_count: int, farmer_id: str) -> None:
        if row_count == 0:
            raise NotFoundError(f"Farmer {farmer_id!r} was not found")


__all__ = ["FarmerRepository"]
