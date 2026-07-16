from __future__ import annotations

import sqlite3

from src.db.connection import DatabasePath
from src.db.repositories._utils import RepositoryContext, row_values
from src.errors import NotFoundError
from src.models import Allocation, AnalysisRun


class AnalysisRepository:
    def __init__(
        self,
        database_path: DatabasePath | None = None,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self._context = RepositoryContext(database_path, connection=connection)

    def create_run(self, run: AnalysisRun) -> AnalysisRun:
        with self._context.open(write=True) as connection:
            connection.execute(
                """
                INSERT INTO analysis_runs (
                    id, parent_run_id, scenario_name, run_type, created_at,
                    horizon_start, horizon_end, data_version, risk_score, risk_level,
                    total_supply_kg, compatible_demand_kg, allocated_kg, unallocated_kg,
                    unallocated_supply_rate, demand_fulfillment_rate, solver_status,
                    weather_status, input_snapshot_json, override_snapshot_json,
                    risk_snapshot_json, result_snapshot_json, error_message
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                self._run_values(run),
            )
        return run

    def get_run_by_id(self, run_id: str) -> AnalysisRun:
        with self._context.open() as connection:
            row = connection.execute(
                "SELECT * FROM analysis_runs WHERE id = ?", (run_id,)
            ).fetchone()
        if row is None:
            raise NotFoundError(f"Analysis run {run_id!r} was not found")
        return AnalysisRun.model_validate(row_values(row))

    def list_runs(self) -> list[AnalysisRun]:
        with self._context.open() as connection:
            rows = connection.execute(
                "SELECT * FROM analysis_runs ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return [AnalysisRun.model_validate(row_values(row)) for row in rows]

    def create_allocation(self, allocation: Allocation) -> Allocation:
        with self._context.open(write=True) as connection:
            self._insert_allocation(connection, allocation)
        return allocation

    def create_allocations(self, allocations: list[Allocation]) -> list[Allocation]:
        with self._context.open(write=True) as connection:
            for allocation in allocations:
                self._insert_allocation(connection, allocation)
        return allocations

    def list_allocations_for_run(self, run_id: str) -> list[Allocation]:
        with self._context.open() as connection:
            rows = connection.execute(
                """
                SELECT * FROM allocations
                WHERE analysis_run_id = ? ORDER BY delivery_date, id
                """,
                (run_id,),
            ).fetchall()
        return [Allocation.model_validate(row_values(row)) for row in rows]

    def count_runs(self) -> int:
        with self._context.open() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM analysis_runs").fetchone()
        return int(row["count"])

    def count_allocations(self) -> int:
        with self._context.open() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM allocations").fetchone()
        return int(row["count"])

    @staticmethod
    def _run_values(run: AnalysisRun) -> tuple[object, ...]:
        return (
            run.id,
            run.parent_run_id,
            run.scenario_name,
            run.run_type.value,
            run.created_at.isoformat(),
            run.horizon_start.isoformat(),
            run.horizon_end.isoformat(),
            run.data_version,
            run.risk_score,
            run.risk_level.value if run.risk_level else None,
            run.total_supply_kg,
            run.compatible_demand_kg,
            run.allocated_kg,
            run.unallocated_kg,
            run.unallocated_supply_rate,
            run.demand_fulfillment_rate,
            run.solver_status.value if run.solver_status else None,
            run.weather_status.value if run.weather_status else None,
            run.input_snapshot_json,
            run.override_snapshot_json,
            run.risk_snapshot_json,
            run.result_snapshot_json,
            run.error_message,
        )

    @staticmethod
    def _insert_allocation(connection: sqlite3.Connection, allocation: Allocation) -> None:
        connection.execute(
            """
            INSERT INTO allocations (
                id, analysis_run_id, harvest_batch_id, buyer_demand_id, delivery_date,
                quantity_kg, distance_km_snapshot, reason_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                allocation.id,
                allocation.analysis_run_id,
                allocation.harvest_batch_id,
                allocation.buyer_demand_id,
                allocation.delivery_date.isoformat(),
                allocation.quantity_kg,
                allocation.distance_km_snapshot,
                allocation.reason_json,
                allocation.created_at.isoformat(),
            ),
        )


__all__ = ["AnalysisRepository"]
