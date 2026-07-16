from __future__ import annotations

from src.analysis_models import AllocationDecision, AnalysisInput
from src.config import KG_TOLERANCE
from src.enums import AllocationReasonCode, EstimateConfidence

_CONFIDENCE_ORDER = {
    EstimateConfidence.LOW: 0,
    EstimateConfidence.MEDIUM: 1,
    EstimateConfidence.HIGH: 2,
}


def greedy_allocations(analysis: AnalysisInput) -> tuple[AllocationDecision, ...]:
    """Return deterministic, constraint-safe allocations after solver failure."""
    remaining_capacity = {item.date: item.quantity_kg for item in analysis.daily_capacity}
    remaining_demand = {item.demand_id: item.quantity_kg for item in analysis.demands}
    allocations: list[AllocationDecision] = []
    harvests = sorted(
        analysis.harvests,
        key=lambda item: (
            item.harvest_date,
            _CONFIDENCE_ORDER[item.confidence],
            item.batch_id,
        ),
    )
    demands = sorted(
        analysis.demands,
        key=lambda item: (item.deadline, -item.priority, item.distance_km, item.demand_id),
    )
    for harvest in harvests:
        remaining_harvest = harvest.quantity_kg
        for demand in demands:
            if remaining_harvest <= KG_TOLERANCE:
                break
            if harvest.grade not in demand.accepted_grades:
                continue
            start = max(harvest.harvest_date, analysis.horizon_start)
            end = min(demand.deadline, analysis.horizon_end)
            for delivery_date in sorted(remaining_capacity):
                if delivery_date < start or delivery_date > end:
                    continue
                quantity = min(
                    remaining_harvest,
                    remaining_demand[demand.demand_id],
                    remaining_capacity[delivery_date],
                )
                if quantity <= KG_TOLERANCE:
                    continue
                allocations.append(
                    AllocationDecision(
                        harvest_batch_id=harvest.batch_id,
                        buyer_demand_id=demand.demand_id,
                        delivery_date=delivery_date,
                        quantity_kg=quantity,
                        distance_km=demand.distance_km,
                        reason_codes=_reason_codes(harvest.harvest_date, demand, delivery_date),
                    )
                )
                remaining_harvest -= quantity
                remaining_demand[demand.demand_id] -= quantity
                remaining_capacity[delivery_date] -= quantity
    return tuple(
        sorted(
            allocations,
            key=lambda item: (
                item.delivery_date,
                item.harvest_batch_id,
                item.buyer_demand_id,
            ),
        )
    )


def _reason_codes(harvest_date, demand, delivery_date) -> tuple[AllocationReasonCode, ...]:
    codes = [
        AllocationReasonCode.GRADE_COMPATIBLE,
        AllocationReasonCode.DEADLINE_FEASIBLE,
        AllocationReasonCode.CAPACITY_AVAILABLE,
    ]
    if demand.priority == 3:
        codes.append(AllocationReasonCode.HIGH_PRIORITY)
    if delivery_date == harvest_date:
        codes.append(AllocationReasonCode.EARLY_DELIVERY)
    if demand.distance_km <= 30:
        codes.append(AllocationReasonCode.SHORT_DISTANCE)
    return tuple(codes)


__all__ = ["greedy_allocations"]
