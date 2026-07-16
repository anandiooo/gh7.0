from datetime import timedelta

from src.db.repositories import (
    AnalysisRepository,
    BuyerRepository,
    CapacityRepository,
    DemandRepository,
    HarvestRepository,
    WeatherRepository,
)
from src.enums import (
    ChannelType,
    EstimateConfidence,
    QualityGrade,
    SeedableSource,
    SourceType,
    WorkspaceMode,
)
from src.services.data_version_service import compute_data_version
from src.services.seed_service import EXPECTED_DEMO_COUNTS
from src.services.workspace_service import initialize_workspace, read_workspace_counts


def test_demo_seed_has_exact_counts_and_required_categories(database_path, reference_date) -> None:
    initialize_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    assert read_workspace_counts(database_path) == EXPECTED_DEMO_COUNTS

    harvests = HarvestRepository(database_path).list()
    buyers = BuyerRepository(database_path).list()
    demands = DemandRepository(database_path).list()
    assert {batch.grade for batch in harvests} == set(QualityGrade)
    assert {batch.confidence for batch in harvests} == set(EstimateConfidence)
    assert {buyer.channel for buyer in buyers} == set(ChannelType)
    assert {demand.priority for demand in demands} == {1, 2, 3}
    assert {batch.source for batch in harvests} == {SourceType.SEED}
    assert {demand.source for demand in demands} == {SeedableSource.SEED}


def test_all_seed_dates_derive_from_reference_date(database_path, reference_date) -> None:
    initialize_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    horizon = {reference_date + timedelta(days=offset) for offset in range(7)}
    harvest_dates = {
        batch.estimated_harvest_date for batch in HarvestRepository(database_path).list()
    }
    assert harvest_dates <= horizon
    assert {demand.deadline for demand in DemandRepository(database_path).list()} <= horizon
    assert {capacity.date for capacity in CapacityRepository(database_path).list_all()} == horizon


def test_demo_reset_is_identical_and_never_duplicates(database_path, reference_date) -> None:
    initialize_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    version = compute_data_version(database_path)
    first_harvests = HarvestRepository(database_path).list()
    initialize_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    assert compute_data_version(database_path) == version
    assert HarvestRepository(database_path).list() == first_harvests
    assert read_workspace_counts(database_path) == EXPECTED_DEMO_COUNTS


def test_seed_has_visible_surplus_and_selected_capacity_shortages(
    database_path, reference_date
) -> None:
    initialize_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    harvests = HarvestRepository(database_path).list()
    demands = DemandRepository(database_path).list()
    capacities = CapacityRepository(database_path).list_all()
    assert sum(batch.estimated_quantity_kg for batch in harvests) > 2 * sum(
        demand.quantity_kg for demand in demands
    )
    daily_supply = {
        day: sum(
            batch.estimated_quantity_kg for batch in harvests if batch.estimated_harvest_date == day
        )
        for day in {capacity.date for capacity in capacities}
    }
    shortage_dates = [
        capacity.date
        for capacity in capacities
        if daily_supply[capacity.date] > capacity.available_capacity_kg
    ]
    assert len(shortage_dates) >= 3


def test_seed_does_not_create_weather_or_analysis_results(database_path, reference_date) -> None:
    initialize_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    assert WeatherRepository(database_path).count() == 0
    assert AnalysisRepository(database_path).count_runs() == 0
    assert AnalysisRepository(database_path).count_allocations() == 0
