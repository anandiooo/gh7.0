from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Protocol

import numpy as np
from scipy.optimize import linprog

from src.analysis_models import (
    AllocationDecision,
    AnalysisDemand,
    AnalysisHarvest,
    AnalysisInput,
    OptimizationResult,
    UnallocatedBatch,
    UnmetDemand,
)
from src.config import DISTANCE_PENALTY, KG_TOLERANCE, LATE_DELIVERY_PENALTY
from src.config import UNALLOCATED_SUPPLY_PENALTY as SUPPLY_PRIORITY
from src.enums import AllocationReasonCode, SolverStatus
from src.services.greedy_fallback import greedy_allocations


class SolverResult(Protocol):
    success: bool
    x: np.ndarray
    fun: float
    message: str


class LinearSolver(Protocol):
    def __call__(
        self,
        c: np.ndarray,
        *,
        A_ub: np.ndarray,
        b_ub: np.ndarray,
        bounds: list[tuple[float, None]],
        method: str,
    ) -> SolverResult: ...


@dataclass(frozen=True)
class FeasibleVariable:
    harvest: AnalysisHarvest
    demand: AnalysisDemand
    delivery_date_ordinal: int

    @property
    def delivery_date(self):
        return self.harvest.harvest_date.fromordinal(self.delivery_date_ordinal)


def optimize_allocations(
    analysis: AnalysisInput,
    *,
    solver: LinearSolver = linprog,
) -> OptimizationResult:
    """Solve continuous kilogram allocations or use the deterministic fallback."""
    started = perf_counter()
    variables = _build_variables(analysis)
    if not variables:
        warning = _no_variable_warning(analysis)
        return _build_result(
            analysis,
            status=SolverStatus.NO_DATA,
            allocations=(),
            objective_value=None,
            warnings=(warning,),
            runtime_ms=(perf_counter() - started) * 1000,
        )
    objective, constraints, limits = _build_linear_problem(analysis, variables)
    try:
        solved = solver(
            objective,
            A_ub=constraints,
            b_ub=limits,
            bounds=[(0.0, None)] * len(variables),
            method="highs",
        )
    except Exception:
        return _fallback_result(analysis, started, "SOLVER_EXCEPTION")
    if not solved.success:
        return _fallback_result(analysis, started, "SOLVER_UNSUCCESSFUL")
    allocations = _normalize_solver_allocations(analysis, variables, solved.x)
    return _build_result(
        analysis,
        status=SolverStatus.OPTIMAL,
        allocations=allocations,
        objective_value=float(solved.fun),
        warnings=(),
        runtime_ms=(perf_counter() - started) * 1000,
    )


def _build_variables(analysis: AnalysisInput) -> tuple[FeasibleVariable, ...]:
    capacity_dates = {
        item.date for item in analysis.daily_capacity if item.quantity_kg > KG_TOLERANCE
    }
    return tuple(
        FeasibleVariable(
            harvest=harvest,
            demand=demand,
            delivery_date_ordinal=delivery_date.toordinal(),
        )
        for harvest in sorted(
            analysis.harvests, key=lambda item: (item.harvest_date, item.batch_id)
        )
        for demand in sorted(analysis.demands, key=lambda item: (item.deadline, item.demand_id))
        if harvest.grade in demand.accepted_grades
        for delivery_date in sorted(capacity_dates)
        if harvest.harvest_date <= delivery_date <= demand.deadline
        and analysis.horizon_start <= delivery_date <= analysis.horizon_end
    )


def _build_linear_problem(
    analysis: AnalysisInput, variables: tuple[FeasibleVariable, ...]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    objective = np.array(
        [
            -SUPPLY_PRIORITY
            - variable.demand.priority * 10.0
            + (variable.delivery_date - analysis.horizon_start).days
            * (LATE_DELIVERY_PENALTY / 10.0)
            + variable.demand.distance_km * (DISTANCE_PENALTY / 1000.0)
            for variable in variables
        ],
        dtype=float,
    )
    rows: list[list[float]] = []
    limits: list[float] = []
    for harvest in analysis.harvests:
        rows.append([float(item.harvest.batch_id == harvest.batch_id) for item in variables])
        limits.append(harvest.quantity_kg)
    for demand in analysis.demands:
        rows.append([float(item.demand.demand_id == demand.demand_id) for item in variables])
        limits.append(demand.quantity_kg)
    for capacity in analysis.daily_capacity:
        rows.append([float(item.delivery_date == capacity.date) for item in variables])
        limits.append(capacity.quantity_kg)
    return objective, np.array(rows, dtype=float), np.array(limits, dtype=float)


def _normalize_solver_allocations(
    analysis: AnalysisInput,
    variables: tuple[FeasibleVariable, ...],
    values: np.ndarray,
) -> tuple[AllocationDecision, ...]:
    remaining_batch = {item.batch_id: item.quantity_kg for item in analysis.harvests}
    remaining_demand = {item.demand_id: item.quantity_kg for item in analysis.demands}
    remaining_capacity = {item.date: item.quantity_kg for item in analysis.daily_capacity}
    allocations = []
    for variable, raw_quantity in zip(variables, values, strict=True):
        quantity = min(
            max(float(raw_quantity), 0.0),
            remaining_batch[variable.harvest.batch_id],
            remaining_demand[variable.demand.demand_id],
            remaining_capacity[variable.delivery_date],
        )
        if quantity < KG_TOLERANCE:
            continue
        allocations.append(
            AllocationDecision(
                harvest_batch_id=variable.harvest.batch_id,
                buyer_demand_id=variable.demand.demand_id,
                delivery_date=variable.delivery_date,
                quantity_kg=quantity,
                distance_km=variable.demand.distance_km,
                reason_codes=_reason_codes(variable),
            )
        )
        remaining_batch[variable.harvest.batch_id] -= quantity
        remaining_demand[variable.demand.demand_id] -= quantity
        remaining_capacity[variable.delivery_date] -= quantity
    return tuple(allocations)


def _reason_codes(variable: FeasibleVariable) -> tuple[AllocationReasonCode, ...]:
    codes = [
        AllocationReasonCode.GRADE_COMPATIBLE,
        AllocationReasonCode.DEADLINE_FEASIBLE,
        AllocationReasonCode.CAPACITY_AVAILABLE,
    ]
    if variable.demand.priority == 3:
        codes.append(AllocationReasonCode.HIGH_PRIORITY)
    if variable.delivery_date == variable.harvest.harvest_date:
        codes.append(AllocationReasonCode.EARLY_DELIVERY)
    if variable.demand.distance_km <= 30:
        codes.append(AllocationReasonCode.SHORT_DISTANCE)
    return tuple(codes)


def _fallback_result(analysis: AnalysisInput, started: float, warning: str) -> OptimizationResult:
    return _build_result(
        analysis,
        status=SolverStatus.FEASIBLE_FALLBACK,
        allocations=greedy_allocations(analysis),
        objective_value=None,
        warnings=(warning,),
        runtime_ms=(perf_counter() - started) * 1000,
    )


def _build_result(
    analysis: AnalysisInput,
    *,
    status: SolverStatus,
    allocations: tuple[AllocationDecision, ...],
    objective_value: float | None,
    warnings: tuple[str, ...],
    runtime_ms: float,
) -> OptimizationResult:
    allocated_by_batch = {item.batch_id: 0.0 for item in analysis.harvests}
    allocated_by_demand = {item.demand_id: 0.0 for item in analysis.demands}
    for allocation in allocations:
        allocated_by_batch[allocation.harvest_batch_id] += allocation.quantity_kg
        allocated_by_demand[allocation.buyer_demand_id] += allocation.quantity_kg
    unallocated_batches = tuple(
        UnallocatedBatch(
            harvest_batch_id=item.batch_id,
            quantity_kg=_normalized(item.quantity_kg - allocated_by_batch[item.batch_id]),
            grade=item.grade,
            harvest_date=item.harvest_date,
        )
        for item in analysis.harvests
        if item.quantity_kg - allocated_by_batch[item.batch_id] >= KG_TOLERANCE
    )
    unmet_demands = tuple(
        UnmetDemand(
            buyer_demand_id=item.demand_id,
            quantity_kg=_normalized(item.quantity_kg - allocated_by_demand[item.demand_id]),
            deadline=item.deadline,
        )
        for item in analysis.demands
        if item.quantity_kg - allocated_by_demand[item.demand_id] >= KG_TOLERANCE
    )
    allocated_kg = sum(item.quantity_kg for item in allocations)
    total_supply = analysis.total_supply_kg
    total_demand = sum(item.quantity_kg for item in analysis.demands)
    unallocated_kg = _normalized(total_supply - allocated_kg)
    unmet_demand_kg = _normalized(total_demand - allocated_kg)
    return OptimizationResult(
        status=status,
        objective_value=objective_value,
        allocations=allocations,
        allocated_kg=allocated_kg,
        unallocated_kg=unallocated_kg,
        unmet_demand_kg=unmet_demand_kg,
        unallocated_supply_rate=unallocated_kg / total_supply if total_supply else 0,
        demand_fulfillment_rate=allocated_kg / total_demand if total_demand else 0,
        unallocated_batches=unallocated_batches,
        unmet_demands=unmet_demands,
        warnings=warnings,
        runtime_ms=runtime_ms,
    )


def _no_variable_warning(analysis: AnalysisInput) -> str:
    if not analysis.harvests:
        return "NO_SUPPLY"
    if not analysis.demands:
        return "NO_DEMAND"
    if not any(item.quantity_kg > KG_TOLERANCE for item in analysis.daily_capacity):
        return "ZERO_CAPACITY"
    return "NO_FEASIBLE_VARIABLES"


def _normalized(value: float) -> float:
    return 0.0 if abs(value) < KG_TOLERANCE else max(0.0, value)


__all__ = ["optimize_allocations"]
