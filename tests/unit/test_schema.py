import sqlite3

import pytest

from src.config import SCHEMA_VERSION
from src.db.connection import connection_context
from src.db.schema import initialize_schema

REQUIRED_TABLES = {
    "cooperative_profiles",
    "farmers",
    "harvest_batches",
    "buyers",
    "buyer_demands",
    "distribution_capacities",
    "weather_snapshots",
    "analysis_runs",
    "allocations",
    "schema_metadata",
}


def test_schema_initialization_is_idempotent_and_records_version(database_path) -> None:
    initialize_schema(database_path)
    initialize_schema(database_path)
    with connection_context(database_path) as connection:
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = ?", ("table",)
            ).fetchall()
        }
        version = connection.execute(
            "SELECT value FROM schema_metadata WHERE key = ?", ("schema_version",)
        ).fetchone()["value"]
    assert tables >= REQUIRED_TABLES
    assert version == str(SCHEMA_VERSION)


def test_foreign_keys_are_enabled_on_every_connection(database_path) -> None:
    with connection_context(database_path) as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    with connection_context(database_path) as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_one_profile_constraint_is_enforced(database_path, aware_timestamp) -> None:
    with connection_context(database_path) as connection:
        _insert_profile(connection, "profile-1", aware_timestamp.isoformat())
        with pytest.raises(sqlite3.IntegrityError):
            _insert_profile(connection, "profile-2", aware_timestamp.isoformat())


def test_unique_capacity_date_is_enforced(database_path, aware_timestamp) -> None:
    values = ("capacity-1", "2026-07-16", 100.0, "MANUAL", aware_timestamp.isoformat())
    with connection_context(database_path) as connection:
        connection.execute(
            """
            INSERT INTO distribution_capacities (
                id, date, available_capacity_kg, source, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (*values, values[-1]),
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO distribution_capacities (
                    id, date, available_capacity_kg, source, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("capacity-2", *values[1:], values[-1]),
            )


def test_foreign_key_violation_is_rejected(database_path, aware_timestamp) -> None:
    with connection_context(database_path) as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO harvest_batches (
                id, farmer_id, commodity_code, estimated_harvest_date,
                estimated_quantity_kg, grade, confidence, status, source,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "harvest-1",
                "missing-farmer",
                "CABAI_RAWIT_MERAH",
                "2026-07-16",
                10,
                "A",
                "HIGH",
                "PLANNED",
                "MANUAL",
                aware_timestamp.isoformat(),
                aware_timestamp.isoformat(),
            ),
        )


def _insert_profile(connection, profile_id: str, timestamp: str) -> None:
    connection.execute(
        """
        INSERT INTO cooperative_profiles (
            id, name, pilot_region, commodity_code, adm4_code, workspace_mode,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            profile_id,
            "Koperasi Uji",
            "Magelang",
            "CABAI_RAWIT_MERAH",
            "33.08.01.2001",
            "DEMO",
            timestamp,
            timestamp,
        ),
    )
