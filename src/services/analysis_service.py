from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from uuid import uuid4

from src.analysis_models import AnalysisInput, OptimizationResult, RiskResult
from src.config import APP_TIMEZONE
from src.db.connection import DatabasePath, connection_context, transaction
from src.db.repositories import AnalysisRepository
from src.enums import AnalysisRunType, SolverStatus
from src.errors import NotFoundError
from src.models import Allocation, AnalysisRun
from src.services.allocation_optimizer import optimize_allocations
from src.services.analysis_input_service import AnalysisInputService
from src.services.data_version_service import compute_data_version
from src.services.risk_engine import calculate_risk


@dataclass(frozen=True)
class AnalysisOutcome:
    run: AnalysisRun
    analysis: AnalysisInput
    risk: RiskResult
    optimization: OptimizationResult


class AnalysisService:
    def __init__(self, database_path: DatabasePath | None = None) -> None:
        self.database_path = database_path
        self.inputs = AnalysisInputService(database_path)
        self.repository = AnalysisRepository(database_path)

    def run_base(self, horizon_start: date) -> AnalysisOutcome:
        """Calculate and atomically persist one immutable canonical base analysis."""
        analysis = self.inputs.build(horizon_start)
        risk = calculate_risk(analysis)
        optimization = optimize_allocations(analysis)
        run = self._build_run(analysis, risk, optimization)
        allocations = self._build_allocations(run, analysis, optimization)
        with connection_context(self.database_path) as connection, transaction(connection):
            repository = AnalysisRepository(connection=connection)
            repository.create_run(run)
            repository.create_allocations(allocations)
        return AnalysisOutcome(run, analysis, risk, optimization)

    def get_outcome(self, run_id: str) -> AnalysisOutcome:
        """Rehydrate one immutable analysis outcome from canonical snapshots."""
        run = self.repository.get_run_by_id(run_id)
        if run.risk_snapshot_json is None or run.result_snapshot_json is None:
            raise NotFoundError("Analysis run does not contain a successful result")
        return AnalysisOutcome(
            run=run,
            analysis=AnalysisInput.model_validate_json(run.input_snapshot_json),
            risk=RiskResult.model_validate_json(run.risk_snapshot_json),
            optimization=OptimizationResult.model_validate_json(run.result_snapshot_json),
        )

    def latest_successful_base(self) -> AnalysisOutcome | None:
        """Return the latest successful base run without replacing it on later failure."""
        run = next(
            (
                item
                for item in self.repository.list_runs()
                if item.run_type is AnalysisRunType.BASE
                and item.error_message is None
                and item.risk_snapshot_json is not None
                and item.result_snapshot_json is not None
            ),
            None,
        )
        return self.get_outcome(run.id) if run else None

    def is_stale(self, outcome: AnalysisOutcome) -> bool:
        """Return whether canonical operational data changed since the run."""
        return compute_data_version(self.database_path) != outcome.run.data_version

    def list_recent_runs(self, limit: int = 5) -> list[AnalysisRun]:
        """Return a small immutable recent-run list for technical inspection."""
        return self.repository.list_runs()[:limit]

    @staticmethod
    def _build_run(
        analysis: AnalysisInput,
        risk: RiskResult,
        optimization: OptimizationResult,
    ) -> AnalysisRun:
        return AnalysisRun(
            id=str(uuid4()),
            parent_run_id=None,
            scenario_name=None,
            run_type=AnalysisRunType.BASE,
            created_at=datetime.now(APP_TIMEZONE),
            horizon_start=analysis.horizon_start,
            horizon_end=analysis.horizon_end,
            data_version=analysis.data_version,
            risk_score=risk.score,
            risk_level=risk.level,
            total_supply_kg=analysis.total_supply_kg,
            compatible_demand_kg=analysis.compatible_demand_kg,
            allocated_kg=optimization.allocated_kg,
            unallocated_kg=optimization.unallocated_kg,
            unallocated_supply_rate=optimization.unallocated_supply_rate,
            demand_fulfillment_rate=optimization.demand_fulfillment_rate,
            solver_status=optimization.status,
            weather_status=risk.weather_status,
            input_snapshot_json=_canonical_json(analysis),
            override_snapshot_json=None,
            risk_snapshot_json=_canonical_json(risk),
            result_snapshot_json=_canonical_json(optimization),
            error_message=None,
        )

    @staticmethod
    def _build_allocations(
        run: AnalysisRun,
        analysis: AnalysisInput,
        optimization: OptimizationResult,
    ) -> list[Allocation]:
        if optimization.status not in {
            SolverStatus.OPTIMAL,
            SolverStatus.FEASIBLE_FALLBACK,
        }:
            return []
        created_at = run.created_at
        return [
            Allocation(
                id=str(uuid4()),
                analysis_run_id=run.id,
                harvest_batch_id=item.harvest_batch_id,
                buyer_demand_id=item.buyer_demand_id,
                delivery_date=item.delivery_date,
                quantity_kg=item.quantity_kg,
                distance_km_snapshot=item.distance_km,
                reason_json=json.dumps(
                    [code.value for code in item.reason_codes], separators=(",", ":")
                ),
                created_at=created_at,
            )
            for item in optimization.allocations
            if item.harvest_batch_id in {batch.batch_id for batch in analysis.harvests}
            and item.buyer_demand_id in {demand.demand_id for demand in analysis.demands}
        ]


def _canonical_json(model) -> str:
    return json.dumps(
        model.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


__all__ = ["AnalysisOutcome", "AnalysisService"]
