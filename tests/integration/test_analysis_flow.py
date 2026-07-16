from datetime import timedelta

import pytest

from src.analysis_models import (
    ScenarioOverrides,
    TemporaryBuyerDemandOverride,
    TemporaryCapacityOverride,
)
from src.db.repositories import AnalysisRepository
from src.enums import QualityGrade, SolverStatus, WorkspaceMode
from src.errors import ValidationError
from src.services.analysis_service import AnalysisService
from src.services.capacity_service import CapacityService
from src.services.data_version_service import compute_data_version
from src.services.radar_service import RadarService
from src.services.scenario_service import ScenarioService
from src.services.workspace_service import read_workspace_counts, reset_workspace


def test_base_analysis_persists_run_and_allocations_atomically(
    database_path, reference_date
) -> None:
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    initial_version = compute_data_version(database_path)
    service = AnalysisService(database_path)

    outcome = service.run_base(reference_date)
    repository = AnalysisRepository(database_path)
    assert repository.count_runs() == 1
    assert repository.count_allocations() == len(outcome.optimization.allocations)
    assert outcome.run.solver_status is SolverStatus.OPTIMAL
    assert service.get_outcome(outcome.run.id).analysis == outcome.analysis
    assert service.latest_successful_base().run.id == outcome.run.id
    assert compute_data_version(database_path) == initial_version


def test_failed_new_analysis_preserves_latest_success(
    database_path, reference_date, monkeypatch
) -> None:
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    service = AnalysisService(database_path)
    successful = service.run_base(reference_date)

    def fail_optimizer(*args, **kwargs):
        raise RuntimeError("controlled analysis failure")

    monkeypatch.setattr("src.services.analysis_service.optimize_allocations", fail_optimizer)
    with pytest.raises(RuntimeError):
        service.run_base(reference_date)
    assert AnalysisRepository(database_path).count_runs() == 1
    assert service.latest_successful_base().run.id == successful.run.id


def test_allocation_persistence_failure_rolls_back_run(
    database_path, reference_date, monkeypatch
) -> None:
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)

    def fail_allocations(*args, **kwargs):
        raise RuntimeError("controlled persistence failure")

    monkeypatch.setattr(AnalysisRepository, "create_allocations", fail_allocations)
    with pytest.raises(RuntimeError):
        AnalysisService(database_path).run_base(reference_date)
    repository = AnalysisRepository(database_path)
    assert repository.count_runs() == 0
    assert repository.count_allocations() == 0


def test_radar_totals_and_no_harvest_state(database_path, reference_date) -> None:
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    radar = RadarService(database_path).calculate(reference_date)
    assert radar.analysis.total_supply_kg == 12600
    assert radar.analysis.compatible_demand_kg == 2760
    assert radar.potential_surplus_kg == 9840
    assert radar.operationally_constrained_surplus_kg == 9840
    assert radar.risk.has_data

    reset_workspace(WorkspaceMode.EMPTY, database_path, reference_date=reference_date)
    empty = RadarService(database_path).calculate(reference_date)
    assert empty.risk.has_data is False
    assert empty.risk.score is None


def test_stale_detection_changes_only_after_canonical_mutation(
    database_path, reference_date
) -> None:
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    service = AnalysisService(database_path)
    outcome = service.run_base(reference_date)
    assert service.is_stale(outcome) is False

    CapacityService(database_path).upsert_capacity(
        capacity_date=reference_date,
        available_capacity_kg=999,
        note="stale test",
    )
    assert service.is_stale(outcome) is True


def test_scenario_improves_allocation_without_mutating_canonical_data(
    database_path, reference_date
) -> None:
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    analysis_service = AnalysisService(database_path)
    base = analysis_service.run_base(reference_date)
    version_before = compute_data_version(database_path)
    counts_before = read_workspace_counts(database_path)
    buyer_context = base.analysis.demands[0]
    overrides = ScenarioOverrides(
        scenario_name="Additional processor absorption",
        buyer_demand=TemporaryBuyerDemandOverride(
            buyer_id=buyer_context.buyer_id,
            buyer_name=buyer_context.buyer_name,
            channel=buyer_context.channel,
            distance_km=buyer_context.distance_km,
            quantity_kg=1000,
            accepted_grades=(QualityGrade.A, QualityGrade.B, QualityGrade.C),
            deadline=reference_date + timedelta(days=6),
            priority=3,
        ),
        capacities=(
            TemporaryCapacityOverride(
                date=reference_date + timedelta(days=6),
                effective_capacity_kg=1500,
            ),
        ),
    )
    scenario = ScenarioService().run(base, overrides)

    assert scenario.comparison.allocated_kg_delta > 0
    assert scenario.comparison.unallocated_kg_delta < 0
    assert scenario.optimization.status is SolverStatus.OPTIMAL
    assert compute_data_version(database_path) == version_before
    assert read_workspace_counts(database_path) == counts_before
    assert AnalysisRepository(database_path).count_runs() == 1


def test_scenario_rejects_no_effective_change(database_path, reference_date) -> None:
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    base = AnalysisService(database_path).run_base(reference_date)
    with pytest.raises(ValidationError):
        ScenarioService().run(base, ScenarioOverrides(scenario_name="No change"))

    current = base.analysis.daily_capacity[0]
    with pytest.raises(ValidationError):
        ScenarioService().run(
            base,
            ScenarioOverrides(
                scenario_name="Same capacity",
                capacities=(
                    TemporaryCapacityOverride(
                        date=current.date,
                        effective_capacity_kg=current.quantity_kg,
                    ),
                ),
            ),
        )
