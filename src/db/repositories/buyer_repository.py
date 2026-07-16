from __future__ import annotations

import sqlite3
from datetime import datetime

from src.db.connection import DatabasePath
from src.db.repositories._utils import RepositoryContext, row_values
from src.errors import NotFoundError
from src.models import Buyer


class BuyerRepository:
    def __init__(
        self,
        database_path: DatabasePath | None = None,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self._context = RepositoryContext(database_path, connection=connection)

    def create(self, buyer: Buyer) -> Buyer:
        with self._context.open(write=True) as connection:
            self._insert(connection, buyer)
        return buyer

    def create_many(self, buyers: list[Buyer]) -> list[Buyer]:
        with self._context.open(write=True) as connection:
            for buyer in buyers:
                self._insert(connection, buyer)
        return buyers

    def get_by_id(self, buyer_id: str) -> Buyer:
        with self._context.open() as connection:
            row = connection.execute("SELECT * FROM buyers WHERE id = ?", (buyer_id,)).fetchone()
        if row is None:
            raise NotFoundError(f"Buyer {buyer_id!r} was not found")
        return Buyer.model_validate(row_values(row))

    def list(self, *, active: bool | None = None) -> list[Buyer]:
        with self._context.open() as connection:
            if active is None:
                rows = connection.execute("SELECT * FROM buyers ORDER BY name, id").fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM buyers WHERE active = ? ORDER BY name, id", (int(active),)
                ).fetchall()
        return [Buyer.model_validate(row_values(row)) for row in rows]

    def update(self, buyer: Buyer) -> Buyer:
        with self._context.open(write=True) as connection:
            cursor = connection.execute(
                """
                UPDATE buyers SET
                    name = ?, channel = ?, location = ?, distance_km = ?, active = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    buyer.name,
                    buyer.channel.value,
                    buyer.location,
                    buyer.distance_km,
                    int(buyer.active),
                    buyer.updated_at.isoformat(),
                    buyer.id,
                ),
            )
            self._ensure_found(cursor.rowcount, buyer.id)
        return self.get_by_id(buyer.id)

    def deactivate(self, buyer_id: str, updated_at: datetime) -> Buyer:
        with self._context.open(write=True) as connection:
            cursor = connection.execute(
                "UPDATE buyers SET active = ?, updated_at = ? WHERE id = ?",
                (0, updated_at.isoformat(), buyer_id),
            )
            self._ensure_found(cursor.rowcount, buyer_id)
        return self.get_by_id(buyer_id)

    def count(self, *, active: bool | None = None) -> int:
        with self._context.open() as connection:
            if active is None:
                row = connection.execute("SELECT COUNT(*) AS count FROM buyers").fetchone()
            else:
                row = connection.execute(
                    "SELECT COUNT(*) AS count FROM buyers WHERE active = ?", (int(active),)
                ).fetchone()
        return int(row["count"])

    @staticmethod
    def _insert(connection: sqlite3.Connection, buyer: Buyer) -> None:
        connection.execute(
            """
            INSERT INTO buyers (
                id, name, channel, location, distance_km, active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                buyer.id,
                buyer.name,
                buyer.channel.value,
                buyer.location,
                buyer.distance_km,
                int(buyer.active),
                buyer.created_at.isoformat(),
                buyer.updated_at.isoformat(),
            ),
        )

    @staticmethod
    def _ensure_found(row_count: int, buyer_id: str) -> None:
        if row_count == 0:
            raise NotFoundError(f"Buyer {buyer_id!r} was not found")


__all__ = ["BuyerRepository"]
