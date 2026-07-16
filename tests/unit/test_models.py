from datetime import date, datetime, timedelta

import pytest
from pydantic import ValidationError as PydanticValidationError

from src.config import APP_TIMEZONE, PILOT_COMMODITY_CODE
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

NOW = datetime(2026, 7, 16, 8, 0, tzinfo=APP_TIMEZONE)


def test_valid_models_are_created_with_typed_values() -> None:
    profile = CooperativeProfile(
        id="coop-1",
        name="Koperasi Uji",
        pilot_region="Magelang",
        commodity_code=PILOT_COMMODITY_CODE,
        adm4_code="33.08.01.2001",
        workspace_mode=WorkspaceMode.DEMO,
        created_at=NOW,
        updated_at=NOW,
    )
    farmer = Farmer(
        id="farmer-1",
        name="Petani Uji",
        village_name="Sengi",
        subdistrict_name="Dukun",
        created_at=NOW,
        updated_at=NOW,
    )
    harvest = _harvest()
    buyer = _buyer()
    demand = _demand()
    capacity = DistributionCapacity(
        id="capacity-1",
        date=date(2026, 7, 16),
        available_capacity_kg=0,
        source=SeedableSource.MANUAL,
        created_at=NOW,
        updated_at=NOW,
    )
    assert profile.workspace_mode is WorkspaceMode.DEMO
    assert farmer.active is True
    assert harvest.grade is QualityGrade.A
    assert buyer.channel is ChannelType.RETAILER
    assert demand.accepted_grades == (QualityGrade.A, QualityGrade.B)
    assert capacity.available_capacity_kg == 0


@pytest.mark.parametrize(
    ("model", "field", "value"),
    [
        (Farmer, "name", "  "),
        (Farmer, "village_name", ""),
        (Buyer, "name", "\t"),
        (Buyer, "location", " "),
    ],
)
def test_blank_required_text_is_rejected(model: type, field: str, value: str) -> None:
    data = (
        {
            "id": "farmer-1",
            "name": "Petani Uji",
            "village_name": "Sengi",
            "subdistrict_name": "Dukun",
            "created_at": NOW,
            "updated_at": NOW,
        }
        if model is Farmer
        else {
            "id": "buyer-1",
            "name": "Buyer Uji",
            "channel": ChannelType.RETAILER,
            "location": "Magelang",
            "distance_km": 10,
            "created_at": NOW,
            "updated_at": NOW,
        }
    )
    data[field] = value
    with pytest.raises(PydanticValidationError):
        model(**data)


@pytest.mark.parametrize("quantity", [0, -1, float("nan"), float("inf")])
def test_harvest_invalid_quantity_is_rejected(quantity: float) -> None:
    with pytest.raises(PydanticValidationError):
        _harvest(estimated_quantity_kg=quantity)


@pytest.mark.parametrize("distance", [-0.1, float("nan"), float("inf")])
def test_buyer_invalid_distance_is_rejected(distance: float) -> None:
    with pytest.raises(PydanticValidationError):
        _buyer(distance_km=distance)


@pytest.mark.parametrize("grades", [(), (QualityGrade.A, QualityGrade.A)])
def test_demand_empty_or_duplicate_grades_are_rejected(
    grades: tuple[QualityGrade, ...],
) -> None:
    with pytest.raises(PydanticValidationError):
        _demand(accepted_grades=grades)


def test_demand_grades_are_stored_in_canonical_order() -> None:
    demand = _demand(accepted_grades=(QualityGrade.C, QualityGrade.A, QualityGrade.B))
    assert demand.accepted_grades == (QualityGrade.A, QualityGrade.B, QualityGrade.C)


@pytest.mark.parametrize("quantity", [0, -1, float("nan"), float("inf")])
def test_demand_invalid_quantity_is_rejected(quantity: float) -> None:
    with pytest.raises(PydanticValidationError):
        _demand(quantity_kg=quantity)


@pytest.mark.parametrize("priority", [0, 4])
def test_demand_invalid_priority_is_rejected(priority: int) -> None:
    with pytest.raises(PydanticValidationError):
        _demand(priority=priority)


@pytest.mark.parametrize(
    ("factory_name", "field", "value"),
    [
        ("harvest", "grade", "D"),
        ("harvest", "confidence", "CERTAIN"),
        ("harvest", "status", "DONE"),
        ("harvest", "source", "API"),
        ("buyer", "channel", "WHOLESALE"),
        ("demand", "status", "PENDING"),
    ],
)
def test_invalid_enum_values_are_rejected(factory_name: str, field: str, value: str) -> None:
    factory = {"harvest": _harvest, "buyer": _buyer, "demand": _demand}[factory_name]
    with pytest.raises(PydanticValidationError):
        factory(**{field: value})


def test_invalid_date_is_rejected() -> None:
    with pytest.raises(PydanticValidationError):
        _harvest(estimated_harvest_date="not-a-date")


def test_weather_json_is_validated_and_canonicalized() -> None:
    snapshot = WeatherSnapshot(
        id="weather-1",
        adm4_code="33.08.01.2001",
        fetched_at=NOW,
        source_status=WeatherSourceStatus.CACHE,
        normalized_json='{"b": 2, "a": 1}',
        raw_payload_json="{}",
    )
    assert snapshot.normalized_json == '{"a":1,"b":2}'
    with pytest.raises(PydanticValidationError):
        snapshot.model_copy(update={"normalized_json": "{"}).model_validate(
            {**snapshot.model_dump(), "normalized_json": "{"}
        )


def test_stored_weather_rejects_unavailable_status() -> None:
    with pytest.raises(PydanticValidationError):
        WeatherSnapshot(
            id="weather-1",
            adm4_code="33.08.01.2001",
            fetched_at=NOW,
            source_status=WeatherSourceStatus.UNAVAILABLE,
            normalized_json="{}",
            raw_payload_json="{}",
        )


def test_analysis_and_allocation_json_fields_are_validated() -> None:
    run = AnalysisRun(
        id="run-1",
        run_type=AnalysisRunType.BASE,
        created_at=NOW,
        horizon_start=date(2026, 7, 16),
        horizon_end=date(2026, 7, 22),
        data_version="abc",
        input_snapshot_json='{"z": 1}',
    )
    allocation = Allocation(
        id="allocation-1",
        analysis_run_id=run.id,
        harvest_batch_id="harvest-1",
        buyer_demand_id="demand-1",
        delivery_date=date(2026, 7, 16),
        quantity_kg=10,
        distance_km_snapshot=2,
        reason_json='{"reason": "test"}',
        created_at=NOW,
    )
    assert run.input_snapshot_json == '{"z":1}'
    assert allocation.reason_json == '{"reason":"test"}'
    with pytest.raises(PydanticValidationError):
        run.model_validate({**run.model_dump(), "result_snapshot_json": "invalid"})
    with pytest.raises(PydanticValidationError):
        allocation.model_validate({**allocation.model_dump(), "reason_json": "invalid"})


def test_allocation_invalid_quantity_or_distance_is_rejected() -> None:
    values = {
        "id": "allocation-1",
        "analysis_run_id": "run-1",
        "harvest_batch_id": "harvest-1",
        "buyer_demand_id": "demand-1",
        "delivery_date": date(2026, 7, 16),
        "quantity_kg": 10,
        "distance_km_snapshot": 2,
        "reason_json": "{}",
        "created_at": NOW,
    }
    with pytest.raises(PydanticValidationError):
        Allocation(**{**values, "quantity_kg": 0})
    with pytest.raises(PydanticValidationError):
        Allocation(**{**values, "distance_km_snapshot": -1})


def test_timestamp_and_analysis_windows_must_be_ordered() -> None:
    with pytest.raises(PydanticValidationError):
        Farmer(
            id="farmer-1",
            name="Petani Uji",
            village_name="Sengi",
            subdistrict_name="Dukun",
            created_at=NOW,
            updated_at=NOW - timedelta(seconds=1),
        )
    with pytest.raises(PydanticValidationError):
        AnalysisRun(
            id="run-1",
            run_type=AnalysisRunType.BASE,
            created_at=NOW,
            horizon_start=date(2026, 7, 17),
            horizon_end=date(2026, 7, 16),
            data_version="abc",
            input_snapshot_json="{}",
        )


def _harvest(**updates) -> HarvestBatch:
    data = {
        "id": "harvest-1",
        "farmer_id": "farmer-1",
        "commodity_code": PILOT_COMMODITY_CODE,
        "estimated_harvest_date": date(2026, 7, 16),
        "estimated_quantity_kg": 100,
        "grade": QualityGrade.A,
        "confidence": EstimateConfidence.HIGH,
        "status": BatchStatus.PLANNED,
        "source": SourceType.MANUAL,
        "created_at": NOW,
        "updated_at": NOW,
    }
    data.update(updates)
    return HarvestBatch(**data)


def _buyer(**updates) -> Buyer:
    data = {
        "id": "buyer-1",
        "name": "Buyer Uji",
        "channel": ChannelType.RETAILER,
        "location": "Magelang",
        "distance_km": 10,
        "created_at": NOW,
        "updated_at": NOW,
    }
    data.update(updates)
    return Buyer(**data)


def _demand(**updates) -> BuyerDemand:
    data = {
        "id": "demand-1",
        "buyer_id": "buyer-1",
        "commodity_code": PILOT_COMMODITY_CODE,
        "quantity_kg": 50,
        "accepted_grades": (QualityGrade.A, QualityGrade.B),
        "deadline": date(2026, 7, 18),
        "priority": 2,
        "status": DemandStatus.OPEN,
        "source": SeedableSource.MANUAL,
        "created_at": NOW,
        "updated_at": NOW,
    }
    data.update(updates)
    return BuyerDemand(**data)
