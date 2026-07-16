from __future__ import annotations

from datetime import date

from src.analysis_models import RadarResult
from src.db.connection import DatabasePath
from src.services.allocation_optimizer import optimize_allocations
from src.services.analysis_input_service import AnalysisInputService
from src.services.risk_engine import calculate_risk


class RadarService:
    def __init__(self, database_path: DatabasePath | None = None) -> None:
        self.inputs = AnalysisInputService(database_path)

    def calculate(self, horizon_start: date) -> RadarResult:
        """Build current Radar metrics without persisting an analysis run."""
        analysis = self.inputs.build(horizon_start)
        risk = calculate_risk(analysis)
        optimization = optimize_allocations(analysis)
        return RadarResult(
            analysis=analysis,
            risk=risk,
            optimization=optimization,
            potential_surplus_kg=max(0.0, analysis.total_supply_kg - analysis.compatible_demand_kg),
            operationally_constrained_surplus_kg=max(
                0.0, analysis.total_supply_kg - optimization.allocated_kg
            ),
        )


__all__ = ["RadarService"]
