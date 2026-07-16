from __future__ import annotations

import hashlib
import json

from src.analysis_models import (
    AnalysisDemand,
    AnalysisInput,
    DailyCapacity,
    DailyCompatibleDemand,
    ScenarioComparison,
    ScenarioOverrides,
    ScenarioResult,
)
from src.errors import ValidationError
from src.services.allocation_optimizer import optimize_allocations
from src.services.analysis_service import AnalysisOutcome
from src.services.risk_engine import calculate_risk


class ScenarioService:
    def run(self, base: AnalysisOutcome, overrides: ScenarioOverrides) -> ScenarioResult:
        """Apply temporary overrides to a copied base input without canonical writes."""
        scenario_input = self._apply(base.analysis, overrides)
        risk = calculate_risk(scenario_input)
        optimization = optimize_allocations(scenario_input)
        base_optimization = base.optimization
        return ScenarioResult(
            overrides=overrides,
            analysis=scenario_input,
            risk=risk,
            optimization=optimization,
            comparison=ScenarioComparison(
                risk_score_delta=(risk.score or 0) - (base.risk.score or 0),
                allocated_kg_delta=optimization.allocated_kg - base_optimization.allocated_kg,
                unallocated_kg_delta=(
                    optimization.unallocated_kg - base_optimization.unallocated_kg
                ),
                unallocated_supply_rate_delta=(
                    optimization.unallocated_supply_rate - base_optimization.unallocated_supply_rate
                ),
                demand_fulfillment_rate_delta=(
                    optimization.demand_fulfillment_rate - base_optimization.demand_fulfillment_rate
                ),
                unmet_demand_kg_delta=(
                    optimization.unmet_demand_kg - base_optimization.unmet_demand_kg
                ),
            ),
        )

    def _apply(self, base: AnalysisInput, overrides: ScenarioOverrides) -> AnalysisInput:
        if overrides.buyer_demand is None and not overrides.capacities:
            raise ValidationError("Scenario has no override")
        demands = list(base.demands)
        compatible_demand = base.compatible_demand_kg
        daily_demand = {item.date: item.quantity_kg for item in base.daily_compatible_demand}
        effective_change = False
        if override := overrides.buyer_demand:
            if not base.horizon_start <= override.deadline <= base.horizon_end:
                raise ValidationError("Scenario demand deadline is outside the base horizon")
            demand = AnalysisDemand(
                demand_id=self._temporary_demand_id(overrides),
                buyer_id=override.buyer_id,
                buyer_name=override.buyer_name,
                channel=override.channel,
                deadline=override.deadline,
                quantity_kg=override.quantity_kg,
                accepted_grades=tuple(
                    sorted(override.accepted_grades, key=lambda item: item.value)
                ),
                priority=override.priority,
                distance_km=override.distance_km,
            )
            demands.append(demand)
            if self._is_compatible(base, demand):
                compatible_demand += demand.quantity_kg
                daily_demand[demand.deadline] += demand.quantity_kg
            effective_change = True
        capacity_overrides = {item.date: item for item in overrides.capacities}
        if any(
            not base.horizon_start <= current <= base.horizon_end for current in capacity_overrides
        ):
            raise ValidationError("Scenario capacity date is outside the base horizon")
        capacities = []
        for item in base.daily_capacity:
            override = capacity_overrides.get(item.date)
            if override and override.effective_capacity_kg != item.quantity_kg:
                effective_change = True
            capacities.append(
                DailyCapacity(
                    date=item.date,
                    quantity_kg=(override.effective_capacity_kg if override else item.quantity_kg),
                    missing=False if override else item.missing,
                )
            )
        if not effective_change:
            raise ValidationError("Scenario does not change the base input")
        return AnalysisInput(
            horizon_start=base.horizon_start,
            horizon_end=base.horizon_end,
            data_version=base.data_version,
            harvests=base.harvests,
            demands=tuple(demands),
            daily_supply=base.daily_supply,
            daily_compatible_demand=tuple(
                DailyCompatibleDemand(date=item.date, quantity_kg=daily_demand[item.date])
                for item in base.daily_compatible_demand
            ),
            daily_capacity=tuple(capacities),
            compatible_demand_kg=compatible_demand,
            weather=base.weather,
        )

    @staticmethod
    def _is_compatible(base: AnalysisInput, demand: AnalysisDemand) -> bool:
        return any(
            harvest.grade in demand.accepted_grades and harvest.harvest_date <= demand.deadline
            for harvest in base.harvests
        )

    @staticmethod
    def _temporary_demand_id(overrides: ScenarioOverrides) -> str:
        canonical = json.dumps(
            overrides.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
        )
        return f"scenario-demand-{hashlib.sha256(canonical.encode()).hexdigest()[:16]}"


__all__ = ["ScenarioService"]
