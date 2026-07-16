from __future__ import annotations

import sqlite3

from src.db.connection import DatabasePath
from src.db.repositories._utils import RepositoryContext, row_values
from src.errors import ConflictError, NotFoundError
from src.models import CooperativeProfile


class CooperativeRepository:
    def __init__(
        self,
        database_path: DatabasePath | None = None,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self._context = RepositoryContext(database_path, connection=connection)

    def get_profile(self) -> CooperativeProfile | None:
        with self._context.open() as connection:
            rows = connection.execute(
                "SELECT * FROM cooperative_profiles ORDER BY id LIMIT 2"
            ).fetchall()
        if len(rows) > 1:
            raise ConflictError("More than one cooperative profile exists")
        if not rows:
            return None
        values = row_values(rows[0])
        values.pop("singleton_key")
        return CooperativeProfile.model_validate(values)

    def require_profile(self) -> CooperativeProfile:
        profile = self.get_profile()
        if profile is None:
            raise NotFoundError("Cooperative profile was not found")
        return profile

    def create(self, profile: CooperativeProfile) -> CooperativeProfile:
        with self._context.open(write=True) as connection:
            connection.execute(
                """
                INSERT INTO cooperative_profiles (
                    id, name, pilot_region, commodity_code, adm4_code, workspace_mode,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile.id,
                    profile.name,
                    profile.pilot_region,
                    profile.commodity_code,
                    profile.adm4_code,
                    profile.workspace_mode.value,
                    profile.created_at.isoformat(),
                    profile.updated_at.isoformat(),
                ),
            )
        return profile

    def replace_for_initialization(self, profile: CooperativeProfile) -> CooperativeProfile:
        with self._context.open(write=True) as connection:
            connection.execute("DELETE FROM cooperative_profiles")
            connection.execute(
                """
                INSERT INTO cooperative_profiles (
                    id, name, pilot_region, commodity_code, adm4_code, workspace_mode,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile.id,
                    profile.name,
                    profile.pilot_region,
                    profile.commodity_code,
                    profile.adm4_code,
                    profile.workspace_mode.value,
                    profile.created_at.isoformat(),
                    profile.updated_at.isoformat(),
                ),
            )
        return profile


__all__ = ["CooperativeRepository"]
