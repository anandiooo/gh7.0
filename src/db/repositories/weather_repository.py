from __future__ import annotations

import sqlite3
from datetime import datetime

from src.db.connection import DatabasePath
from src.db.repositories._utils import RepositoryContext, row_values
from src.models import WeatherSnapshot


class WeatherRepository:
    def __init__(
        self,
        database_path: DatabasePath | None = None,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self._context = RepositoryContext(database_path, connection=connection)

    def insert(self, snapshot: WeatherSnapshot) -> WeatherSnapshot:
        with self._context.open(write=True) as connection:
            connection.execute(
                """
                INSERT INTO weather_snapshots (
                    id, adm4_code, fetched_at, analysis_date, valid_from, valid_until,
                    source_status, normalized_json, raw_payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot.id,
                    snapshot.adm4_code,
                    snapshot.fetched_at.isoformat(),
                    snapshot.analysis_date.isoformat() if snapshot.analysis_date else None,
                    snapshot.valid_from.isoformat() if snapshot.valid_from else None,
                    snapshot.valid_until.isoformat() if snapshot.valid_until else None,
                    snapshot.source_status.value,
                    snapshot.normalized_json,
                    snapshot.raw_payload_json,
                ),
            )
        return snapshot

    def get_latest_compatible_snapshot(
        self,
        adm4_code: str,
        *,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
    ) -> WeatherSnapshot | None:
        with self._context.open() as connection:
            if valid_from is None or valid_until is None:
                row = connection.execute(
                    """
                    SELECT * FROM weather_snapshots
                    WHERE adm4_code = ? ORDER BY fetched_at DESC, id DESC LIMIT 1
                    """,
                    (adm4_code,),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT * FROM weather_snapshots
                    WHERE adm4_code = ?
                      AND (valid_until IS NULL OR valid_until >= ?)
                      AND (valid_from IS NULL OR valid_from <= ?)
                    ORDER BY fetched_at DESC, id DESC LIMIT 1
                    """,
                    (adm4_code, valid_from.isoformat(), valid_until.isoformat()),
                ).fetchone()
        return WeatherSnapshot.model_validate(row_values(row)) if row else None

    def list_compatible(self, adm4_code: str) -> list[WeatherSnapshot]:
        with self._context.open() as connection:
            rows = connection.execute(
                """
                SELECT * FROM weather_snapshots
                WHERE adm4_code = ? ORDER BY fetched_at, id
                """,
                (adm4_code,),
            ).fetchall()
        return [WeatherSnapshot.model_validate(row_values(row)) for row in rows]

    def count(self) -> int:
        with self._context.open() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM weather_snapshots").fetchone()
        return int(row["count"])


__all__ = ["WeatherRepository"]
