import json
from datetime import date, timedelta

import pytest

from src.config import PILOT_COMMODITY_CODE
from src.db.connection import connection_context
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
from src.enums import (
    AnalysisRunType,
    BatchStatus,
    ChannelType,
    DemandStatus,
    EstimateConfidence,
    QualityGrade,
    SeedableSource,
    SourceType,
    WeatherSourceStatus,
    WorkspaceMode,
)
from src.errors import ConflictError, NotFoundError
from src.models import (
    Allocation,
    AnalysisRun,
    Buyer,
    BuyerDemand,
    CooperativeProfile,
    DistributionCapacity,
    Farmer,
    HarvestBatch,
    WeatherSnapshot,
)


def test_cooperative_repository_enforces_single_profile(database_path, aware_timestamp) -> None:
    repository = CooperativeRepository(database_path)
    profile = _profile(aware_timestamp)
    assert repository.create(profile) == profile
    assert repository.get_profile() == profile
    with pytest.raises(ConflictError):
        repository.create(profile.model_copy(update={"id": "profile-2"}))


def test_farmer_repository_crud_and_deactivation(database_path, aware_timestamp) -> None:
    repository = FarmerRepository(database_path)
    farmer = _farmer(aware_timestamp)
    repository.create(farmer)
    assert repository.get_by_id(farmer.id) == farmer
    updated = farmer.model_copy(
        update={"name": "Petani Diperbarui", "updated_at": aware_timestamp + timedelta(minutes=1)}
    )
    assert repository.update(updated).name == "Petani Diperbarui"
    inactive = repository.deactivate(farmer.id, aware_timestamp + timedelta(minutes=2))
    assert inactive.active is False
    assert repository.list(active=True) == []
    assert repository.count() == 1
    with pytest.raises(NotFoundError):
        repository.get_by_id("missing")


def test_harvest_repository_queries_updates_and_atomic_bulk(database_path, aware_timestamp) -> None:
    FarmerRepository(database_path).create(_farmer(aware_timestamp))
    repository = HarvestRepository(database_path)
    first = _harvest(aware_timestamp)
    second = _harvest(
        aware_timestamp,
        id="harvest-2",
        estimated_harvest_date=date(2026, 7, 18),
        import_fingerprint="fingerprint-2",
    )
    repository.create_many([first, second])
    assert repository.get_by_id(first.id) == first
    assert repository.list_planned_within(date(2026, 7, 17), date(2026, 7, 19)) == [second]
    assert repository.find_by_import_fingerprint("fingerprint-2") == second

    updated = second.model_copy(
        update={
            "estimated_quantity_kg": 125.0,
            "updated_at": aware_timestamp + timedelta(minutes=1),
        }
    )
    assert repository.update(updated).estimated_quantity_kg == 125.0
    cancelled = repository.cancel(first.id, aware_timestamp + timedelta(minutes=2))
    assert cancelled.status is BatchStatus.CANCELLED

    before = repository.count()
    valid = _harvest(aware_timestamp, id="harvest-3", import_fingerprint="atomic")
    duplicate = _harvest(aware_timestamp, id="harvest-4", import_fingerprint="atomic")
    with pytest.raises(ConflictError):
        repository.create_many([valid, duplicate])
    assert repository.count() == before


def test_buyer_and_demand_repositories_round_trip_typed_grades(
    database_path, aware_timestamp
) -> None:
    buyer_repository = BuyerRepository(database_path)
    buyer = _buyer(aware_timestamp)
    buyer_repository.create(buyer)
    assert buyer_repository.get_by_id(buyer.id) == buyer
    updated_buyer = buyer.model_copy(
        update={"distance_km": 15.0, "updated_at": aware_timestamp + timedelta(minutes=1)}
    )
    assert buyer_repository.update(updated_buyer).distance_km == 15.0

    demand_repository = DemandRepository(database_path)
    demand = _demand(aware_timestamp)
    demand_repository.create(demand)
    stored = demand_repository.get_by_id(demand.id)
    assert stored.accepted_grades == (QualityGrade.A, QualityGrade.C)
    assert demand_repository.list_open_within(date(2026, 7, 16), date(2026, 7, 20)) == [stored]
    with connection_context(database_path) as connection:
        raw = connection.execute(
            "SELECT accepted_grades_json FROM buyer_demands WHERE id = ?", (demand.id,)
        ).fetchone()[0]
    assert raw == '["A","C"]'

    updated_demand = demand.model_copy(
        update={"priority": 3, "updated_at": aware_timestamp + timedelta(minutes=2)}
    )
    assert demand_repository.update(updated_demand).priority == 3
    assert (
        demand_repository.close(demand.id, aware_timestamp + timedelta(minutes=3)).status
        is DemandStatus.CLOSED
    )
    assert demand_repository.count(status=DemandStatus.OPEN) == 0
    assert (
        buyer_repository.deactivate(buyer.id, aware_timestamp + timedelta(minutes=4)).active
        is False
    )


def test_demand_bulk_insert_is_atomic(database_path, aware_timestamp) -> None:
    BuyerRepository(database_path).create(_buyer(aware_timestamp))
    repository = DemandRepository(database_path)
    first = _demand(aware_timestamp, id="demand-1")
    duplicate = _demand(aware_timestamp, id="demand-1")
    with pytest.raises(ConflictError):
        repository.create_many([first, duplicate])
    assert repository.count() == 0


def test_capacity_upsert_and_date_range(database_path, aware_timestamp) -> None:
    repository = CapacityRepository(database_path)
    capacity = _capacity(aware_timestamp)
    assert repository.upsert_by_date(capacity) == capacity
    changed = capacity.model_copy(
        update={
            "id": "ignored-new-id",
            "available_capacity_kg": 250.0,
            "updated_at": aware_timestamp + timedelta(minutes=1),
        }
    )
    stored = repository.upsert_by_date(changed)
    assert stored.id == capacity.id
    assert stored.available_capacity_kg == 250.0
    assert repository.list_date_range(date(2026, 7, 16), date(2026, 7, 16)) == [stored]
    assert repository.get_by_date(date(2026, 7, 17)) is None


def test_weather_repository_returns_latest_compatible_snapshot(
    database_path, aware_timestamp
) -> None:
    repository = WeatherRepository(database_path)
    older = _weather(aware_timestamp, "weather-1")
    newer = _weather(aware_timestamp + timedelta(hours=1), "weather-2")
    repository.insert(older)
    repository.insert(newer)
    assert repository.get_latest_compatible_snapshot("33.08.01.2001") == newer
    assert repository.get_latest_compatible_snapshot("different") is None
    assert repository.count() == 2


def test_analysis_runs_are_immutable_and_allocations_link_to_inputs(
    database_path, aware_timestamp
) -> None:
    FarmerRepository(database_path).create(_farmer(aware_timestamp))
    HarvestRepository(database_path).create(_harvest(aware_timestamp))
    BuyerRepository(database_path).create(_buyer(aware_timestamp))
    DemandRepository(database_path).create(_demand(aware_timestamp))
    repository = AnalysisRepository(database_path)
    run = _run(aware_timestamp)
    repository.create_run(run)
    assert repository.get_run_by_id(run.id) == run
    assert repository.list_runs() == [run]
    assert not hasattr(repository, "update_run")
    assert not hasattr(repository, "delete_run")

    allocation = Allocation(
        id="allocation-1",
        analysis_run_id=run.id,
        harvest_batch_id="harvest-1",
        buyer_demand_id="demand-1",
        delivery_date=date(2026, 7, 16),
        quantity_kg=25,
        distance_km_snapshot=10,
        reason_json=json.dumps({"reason": "repository primitive"}),
        created_at=aware_timestamp,
    )
    repository.create_allocation(allocation)
    assert repository.list_allocations_for_run(run.id) == [allocation]
    assert repository.count_runs() == 1
    assert repository.count_allocations() == 1


def _profile(timestamp) -> CooperativeProfile:
    return CooperativeProfile(
        id="profile-1",
        name="Koperasi Uji",
        pilot_region="Magelang",
        commodity_code=PILOT_COMMODITY_CODE,
        adm4_code="33.08.01.2001",
        workspace_mode=WorkspaceMode.DEMO,
        created_at=timestamp,
        updated_at=timestamp,
    )


def _farmer(timestamp) -> Farmer:
    return Farmer(
        id="farmer-1",
        name="Petani Uji",
        village_name="Sengi",
        subdistrict_name="Dukun",
        created_at=timestamp,
        updated_at=timestamp,
    )


def _harvest(timestamp, **updates) -> HarvestBatch:
    values = {
        "id": "harvest-1",
        "farmer_id": "farmer-1",
        "commodity_code": PILOT_COMMODITY_CODE,
        "estimated_harvest_date": date(2026, 7, 16),
        "estimated_quantity_kg": 100,
        "grade": QualityGrade.A,
        "confidence": EstimateConfidence.HIGH,
        "status": BatchStatus.PLANNED,
        "source": SourceType.MANUAL,
        "import_fingerprint": "fingerprint-1",
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    values.update(updates)
    return HarvestBatch(**values)


def _buyer(timestamp) -> Buyer:
    return Buyer(
        id="buyer-1",
        name="Buyer Uji",
        channel=ChannelType.RETAILER,
        location="Magelang",
        distance_km=10,
        created_at=timestamp,
        updated_at=timestamp,
    )


def _demand(timestamp, **updates) -> BuyerDemand:
    values = {
        "id": "demand-1",
        "buyer_id": "buyer-1",
        "commodity_code": PILOT_COMMODITY_CODE,
        "quantity_kg": 50,
        "accepted_grades": (QualityGrade.A, QualityGrade.C),
        "deadline": date(2026, 7, 18),
        "priority": 2,
        "status": DemandStatus.OPEN,
        "source": SeedableSource.MANUAL,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    values.update(updates)
    return BuyerDemand(**values)


def _capacity(timestamp) -> DistributionCapacity:
    return DistributionCapacity(
        id="capacity-1",
        date=date(2026, 7, 16),
        available_capacity_kg=100,
        source=SeedableSource.MANUAL,
        created_at=timestamp,
        updated_at=timestamp,
    )


def _weather(timestamp, weather_id: str) -> WeatherSnapshot:
    return WeatherSnapshot(
        id=weather_id,
        adm4_code="33.08.01.2001",
        fetched_at=timestamp,
        valid_from=timestamp,
        valid_until=timestamp + timedelta(days=1),
        source_status=WeatherSourceStatus.CACHE,
        normalized_json="{}",
        raw_payload_json="{}",
    )


def _run(timestamp) -> AnalysisRun:
    return AnalysisRun(
        id="run-1",
        run_type=AnalysisRunType.BASE,
        created_at=timestamp,
        horizon_start=date(2026, 7, 16),
        horizon_end=date(2026, 7, 22),
        data_version="test-version",
        input_snapshot_json="{}",
    )
