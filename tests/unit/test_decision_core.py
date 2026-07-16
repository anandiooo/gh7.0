from datetime import date, timedelta
from time import perf_counter

import pytest

from src.analysis_models import (
    AnalysisDemand,
    AnalysisHarvest,
    AnalysisInput,
    DailyCapacity,
    DailyCompatibleDemand,
    DailySupply,
    WeatherDisruptionInput,
)
from src.db.repositories import BuyerRepository, HarvestRepository
from src.enums import (
    EstimateConfidence,
    QualityGrade,
    RiskFactorCode,
    RiskLevel,
    SolverStatus,
    WeatherSourceStatus,
    WorkspaceMode,
)
from src.services.allocation_optimizer import optimize_allocations
from src.services.analysis_input_service import AnalysisInputService
from src.services.risk_engine import _risk_level, calculate_risk
from src.services.workspace_service import reset_workspace


def test_risk_engine_calculates_exact_weighted_factors_and_order() -> None:
    analysis = _analysis(
        harvests=(_harvest("h1", quantity=100, confidence=EstimateConfidence.MEDIUM),),
        demands=(_demand("d1", quantity=40),),
        compatible_demand=40,
        capacities=(50, 100, 100, 100, 100, 100, 100),
        weather_score=0.5,
    )
    result = calculate_risk(analysis)
    factor = {item.code: item for item in result.factors}

    assert result.score == pytest.approx(64.5)
    assert result.level is RiskLevel.HIGH
    assert factor[RiskFactorCode.SUPPLY_DEMAND_GAP].raw_value == pytest.approx(0.6)
    assert factor[RiskFactorCode.HARVEST_CONCENTRATION].raw_value == pytest.approx(1)
    assert factor[RiskFactorCode.TRANSPORT_CAPACITY_GAP].raw_value == pytest.approx(0.5)
    assert factor[RiskFactorCode.WEATHER_DISRUPTION].raw_value == pytest.approx(0.5)
    assert factor[RiskFactorCode.ESTIMATE_UNCERTAINTY].raw_value == pytest.approx(0.5)
    assert sum(item.weighted_points for item in result.factors) == pytest.approx(result.score)
    assert result.top_factors == (
        RiskFactorCode.SUPPLY_DEMAND_GAP,
        RiskFactorCode.HARVEST_CONCENTRATION,
        RiskFactorCode.TRANSPORT_CAPACITY_GAP,
    )


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0, RiskLevel.LOW),
        (24.99, RiskLevel.LOW),
        (25, RiskLevel.MEDIUM),
        (49.99, RiskLevel.MEDIUM),
        (50, RiskLevel.HIGH),
        (74.99, RiskLevel.HIGH),
        (75, RiskLevel.CRITICAL),
        (100, RiskLevel.CRITICAL),
    ],
)
def test_risk_threshold_boundaries(score, expected) -> None:
    assert _risk_level(score) is expected


def test_risk_no_harvest_is_no_data_and_weather_unavailable_warns() -> None:
    empty = calculate_risk(_analysis(harvests=(), demands=(), compatible_demand=0))
    assert empty.has_data is False
    assert empty.score is None
    assert empty.level is None
    assert empty.warnings == ("NO_HARVEST_DATA",)

    unavailable = calculate_risk(
        _analysis(harvests=(_harvest("h1"),), demands=(), compatible_demand=0)
    )
    assert "WEATHER_UNAVAILABLE" in unavailable.warnings
    assert "NO_OPEN_DEMAND" in unavailable.warnings


def test_risk_critical_date_tie_prefers_earliest() -> None:
    result = calculate_risk(
        _analysis(
            harvests=(
                _harvest("h1", day=0, quantity=100),
                _harvest("h2", day=1, quantity=100),
            ),
            demands=(),
            compatible_demand=0,
            capacities=(0, 0, 0, 0, 0, 0, 0),
        )
    )
    assert result.critical_date == date(2026, 7, 16)


def test_optimizer_splits_supply_and_respects_all_constraints() -> None:
    analysis = _analysis(
        harvests=(_harvest("h1", quantity=100),),
        demands=(
            _demand("d1", quantity=60, priority=3, deadline_day=1),
            _demand("d2", quantity=60, priority=1, deadline_day=2),
        ),
        compatible_demand=120,
        capacities=(50, 50, 0, 0, 0, 0, 0),
    )
    result = optimize_allocations(analysis)

    assert result.status is SolverStatus.OPTIMAL
    assert result.allocated_kg == pytest.approx(100)
    assert result.unallocated_kg == pytest.approx(0)
    assert result.unmet_demand_kg == pytest.approx(20)
    assert sum(item.quantity_kg for item in result.allocations) <= 100
    for current in (date(2026, 7, 16), date(2026, 7, 17)):
        assert (
            sum(item.quantity_kg for item in result.allocations if item.delivery_date == current)
            <= 50
        )
    assert all(item.delivery_date >= date(2026, 7, 16) for item in result.allocations)
    assert all(
        item.delivery_date
        <= next(d.deadline for d in analysis.demands if d.demand_id == item.buyer_demand_id)
        for item in result.allocations
    )


def test_optimizer_excludes_incompatible_grade_and_zero_capacity() -> None:
    incompatible = _analysis(
        harvests=(_harvest("h1", grade=QualityGrade.C),),
        demands=(_demand("d1", accepted=(QualityGrade.A,)),),
        compatible_demand=0,
    )
    assert optimize_allocations(incompatible).status is SolverStatus.NO_DATA

    zero_capacity = _analysis(
        harvests=(_harvest("h1"),),
        demands=(_demand("d1"),),
        compatible_demand=100,
        capacities=(0, 0, 0, 0, 0, 0, 0),
    )
    result = optimize_allocations(zero_capacity)
    assert result.status is SolverStatus.NO_DATA
    assert result.allocated_kg == 0
    assert result.unallocated_kg == 100


def test_solver_failure_invokes_deterministic_constraint_safe_fallback() -> None:
    analysis = _analysis(
        harvests=(_harvest("h1", quantity=100),),
        demands=(_demand("d1", quantity=80),),
        compatible_demand=80,
        capacities=(40, 40, 0, 0, 0, 0, 0),
    )

    def fail_solver(*args, **kwargs):
        raise RuntimeError("controlled failure")

    first = optimize_allocations(analysis, solver=fail_solver)
    second = optimize_allocations(analysis, solver=fail_solver)
    assert first.status is SolverStatus.FEASIBLE_FALLBACK
    assert first.allocations == second.allocations
    assert first.allocated_kg == 80
    assert all(item.quantity_kg > 0 for item in first.allocations)
    assert sum(item.quantity_kg for item in first.allocations) <= 100


def test_seed_input_builder_filters_inactive_and_cancelled_records(
    database_path, reference_date, aware_timestamp
) -> None:
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    initial = AnalysisInputService(database_path).build(reference_date)
    cancelled_id = initial.harvests[0].batch_id
    inactive_buyer_id = initial.demands[0].buyer_id
    HarvestRepository(database_path).cancel(cancelled_id, aware_timestamp)
    BuyerRepository(database_path).deactivate(inactive_buyer_id, aware_timestamp)

    filtered = AnalysisInputService(database_path).build(reference_date)
    assert cancelled_id not in {item.batch_id for item in filtered.harvests}
    assert inactive_buyer_id not in {item.buyer_id for item in filtered.demands}
    assert all(len(filtered.daily_capacity) == 7 for _ in [0])


def test_seeded_risk_and_optimizer_meet_performance_targets(database_path, reference_date) -> None:
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    analysis = AnalysisInputService(database_path).build(reference_date)
    started = perf_counter()
    risk = calculate_risk(analysis)
    risk_elapsed = perf_counter() - started
    started = perf_counter()
    optimized = optimize_allocations(analysis)
    optimizer_elapsed = perf_counter() - started

    assert analysis.total_supply_kg == 12600
    assert risk.has_data
    assert optimized.status is SolverStatus.OPTIMAL
    assert risk_elapsed < 0.5
    assert optimizer_elapsed < 3


def _analysis(
    *,
    harvests: tuple[AnalysisHarvest, ...],
    demands: tuple[AnalysisDemand, ...],
    compatible_demand: float,
    capacities: tuple[float, ...] = (100, 100, 100, 100, 100, 100, 100),
    weather_score: float | None = None,
) -> AnalysisInput:
    start = date(2026, 7, 16)
    dates = tuple(start + timedelta(days=offset) for offset in range(7))
    weather = (
        WeatherDisruptionInput(
            status=WeatherSourceStatus.LIVE,
            daily_scores=tuple((current, weather_score) for current in dates),
        )
        if weather_score is not None
        else WeatherDisruptionInput(status=WeatherSourceStatus.UNAVAILABLE)
    )
    compatible = tuple(
        demand
        for demand in demands
        if any(
            harvest.grade in demand.accepted_grades and harvest.harvest_date <= demand.deadline
            for harvest in harvests
        )
    )
    return AnalysisInput(
        horizon_start=start,
        horizon_end=dates[-1],
        data_version="test-version",
        harvests=harvests,
        demands=demands,
        daily_supply=tuple(
            DailySupply(
                date=current,
                quantity_kg=sum(
                    item.quantity_kg for item in harvests if item.harvest_date == current
                ),
            )
            for current in dates
        ),
        daily_compatible_demand=tuple(
            DailyCompatibleDemand(
                date=current,
                quantity_kg=sum(
                    item.quantity_kg for item in compatible if item.deadline == current
                ),
            )
            for current in dates
        ),
        daily_capacity=tuple(
            DailyCapacity(date=current, quantity_kg=quantity)
            for current, quantity in zip(dates, capacities, strict=True)
        ),
        compatible_demand_kg=compatible_demand,
        weather=weather,
    )


def _harvest(
    batch_id: str,
    *,
    day: int = 0,
    quantity: float = 100,
    grade: QualityGrade = QualityGrade.A,
    confidence: EstimateConfidence = EstimateConfidence.HIGH,
) -> AnalysisHarvest:
    return AnalysisHarvest(
        batch_id=batch_id,
        farmer_id="farmer-1",
        farmer_name="Farmer",
        harvest_date=date(2026, 7, 16) + timedelta(days=day),
        quantity_kg=quantity,
        grade=grade,
        confidence=confidence,
    )


def _demand(
    demand_id: str,
    *,
    quantity: float = 100,
    accepted: tuple[QualityGrade, ...] = (QualityGrade.A,),
    priority: int = 1,
    deadline_day: int = 2,
) -> AnalysisDemand:
    return AnalysisDemand(
        demand_id=demand_id,
        buyer_id=f"buyer-{demand_id}",
        buyer_name="Buyer",
        channel="PROCESSOR",
        deadline=date(2026, 7, 16) + timedelta(days=deadline_day),
        quantity_kg=quantity,
        accepted_grades=accepted,
        priority=priority,
        distance_km=20,
    )
