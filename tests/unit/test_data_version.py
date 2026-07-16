from datetime import timedelta

from src.db.connection import connection_context, transaction
from src.db.repositories import (
    AnalysisRepository,
    BuyerRepository,
    CapacityRepository,
    CooperativeRepository,
    DemandRepository,
    FarmerRepository,
    HarvestRepository,
    WeatherRepository,
)
from src.db.schema import initialize_schema
from src.enums import AnalysisRunType, SeedableSource, WeatherSourceStatus, WorkspaceMode
from src.models import AnalysisRun, DistributionCapacity, Farmer, WeatherSnapshot
from src.services.data_version_service import compute_data_version
from src.services.workspace_service import initialize_workspace


def test_same_data_has_same_version_and_physical_insert_order_is_irrelevant(
    database_path, tmp_path, reference_date
) -> None:
    initialize_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    second_path = tmp_path / "reverse-order.db"
    initialize_schema(second_path)

    profile = CooperativeRepository(database_path).require_profile()
    farmers = FarmerRepository(database_path).list()
    harvests = HarvestRepository(database_path).list()
    buyers = BuyerRepository(database_path).list()
    demands = DemandRepository(database_path).list()
    capacities = CapacityRepository(database_path).list_all()
    with connection_context(second_path) as connection, transaction(connection):
        CooperativeRepository(connection=connection).create(profile)
        FarmerRepository(connection=connection).create_many(list(reversed(farmers)))
        HarvestRepository(connection=connection).create_many(list(reversed(harvests)))
        BuyerRepository(connection=connection).create_many(list(reversed(buyers)))
        DemandRepository(connection=connection).create_many(list(reversed(demands)))
        for capacity in reversed(capacities):
            CapacityRepository(connection=connection).upsert_by_date(capacity)

    assert compute_data_version(database_path) == compute_data_version(second_path)
    assert compute_data_version(database_path) == compute_data_version(database_path)


def test_relevant_mutations_change_data_version(
    database_path, reference_date, aware_timestamp
) -> None:
    initialize_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    version = compute_data_version(database_path)

    farmer_repository = FarmerRepository(database_path)
    farmer = Farmer(
        id="new-farmer",
        name="Petani Tambahan",
        village_name="Sengi",
        subdistrict_name="Dukun",
        created_at=aware_timestamp + timedelta(days=1),
        updated_at=aware_timestamp + timedelta(days=1),
    )
    farmer_repository.create(farmer)
    version = _assert_changed(database_path, version)
    farmer_repository.update(
        farmer.model_copy(
            update={
                "name": "Petani Tambahan Diperbarui",
                "updated_at": aware_timestamp + timedelta(days=1, minutes=1),
            }
        )
    )
    version = _assert_changed(database_path, version)

    harvest = HarvestRepository(database_path).list()[0]
    HarvestRepository(database_path).cancel(
        harvest.id, aware_timestamp + timedelta(days=1, minutes=2)
    )
    version = _assert_changed(database_path, version)
    demand = DemandRepository(database_path).list()[0]
    DemandRepository(database_path).close(demand.id, aware_timestamp + timedelta(days=1, minutes=3))
    version = _assert_changed(database_path, version)
    buyer = BuyerRepository(database_path).list()[0]
    BuyerRepository(database_path).deactivate(
        buyer.id, aware_timestamp + timedelta(days=1, minutes=4)
    )
    version = _assert_changed(database_path, version)

    capacity = CapacityRepository(database_path).list_all()[0]
    CapacityRepository(database_path).upsert_by_date(
        DistributionCapacity(
            id=capacity.id,
            date=capacity.date,
            available_capacity_kg=capacity.available_capacity_kg + 1,
            source=SeedableSource.MANUAL,
            note="changed",
            created_at=capacity.created_at,
            updated_at=aware_timestamp + timedelta(days=1, minutes=5),
        )
    )
    _assert_changed(database_path, version)


def test_analysis_run_does_not_change_canonical_version(
    database_path, reference_date, aware_timestamp
) -> None:
    initialize_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    version = compute_data_version(database_path)
    AnalysisRepository(database_path).create_run(
        AnalysisRun(
            id="run-1",
            run_type=AnalysisRunType.BASE,
            created_at=aware_timestamp,
            horizon_start=reference_date,
            horizon_end=reference_date + timedelta(days=6),
            data_version=version,
            input_snapshot_json="{}",
        )
    )
    assert compute_data_version(database_path) == version


def test_only_compatible_weather_is_included(
    database_path, reference_date, aware_timestamp
) -> None:
    initialize_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    version = compute_data_version(database_path)
    repository = WeatherRepository(database_path)
    repository.insert(
        WeatherSnapshot(
            id="incompatible-weather",
            adm4_code="different",
            fetched_at=aware_timestamp,
            source_status=WeatherSourceStatus.CACHE,
            normalized_json="{}",
            raw_payload_json="{}",
        )
    )
    assert compute_data_version(database_path) == version
    repository.insert(
        WeatherSnapshot(
            id="compatible-weather",
            adm4_code="33.08.01.2001",
            fetched_at=aware_timestamp,
            source_status=WeatherSourceStatus.CACHE,
            normalized_json='{"source":"fixture"}',
            raw_payload_json="{}",
        )
    )
    assert compute_data_version(database_path) != version


def _assert_changed(database_path, previous: str) -> str:
    current = compute_data_version(database_path)
    assert current != previous
    return current
