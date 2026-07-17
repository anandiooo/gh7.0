from datetime import date, timedelta

import pytest

from src.db.repositories import FarmerRepository
from src.enums import (
    BatchStatus,
    ChannelType,
    DemandStatus,
    EstimateConfidence,
    QualityGrade,
    WorkspaceMode,
)
from src.errors import ValidationError
from src.services.buyer_service import BuyerService
from src.services.capacity_service import CapacityService
from src.services.data_version_service import compute_data_version
from src.services.harvest_service import HarvestService
from src.services.workspace_service import reset_workspace


def test_harvest_service_create_filter_update_cancel_and_version(
    database_path, reference_date
) -> None:
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    service = HarvestService(database_path)
    farmer = service.list_active_farmers()[0]
    initial_version = compute_data_version(database_path)

    created = service.create_harvest(
        farmer_id=farmer.id,
        estimated_harvest_date=reference_date + timedelta(days=2),
        estimated_quantity_kg=125.5,
        grade=QualityGrade.A,
        confidence=EstimateConfidence.HIGH,
        maturity_note="  siap panen  ",
        reference_date=reference_date,
    )
    assert created.maturity_note == "siap panen"
    assert compute_data_version(database_path) != initial_version
    assert service.list_harvests(
        farmer_id=farmer.id,
        grade=QualityGrade.A,
        confidence=EstimateConfidence.HIGH,
        status=BatchStatus.PLANNED,
        start_date=reference_date + timedelta(days=2),
        end_date=reference_date + timedelta(days=2),
    )

    created_version = compute_data_version(database_path)
    updated = service.update_harvest(
        created.id,
        farmer_id=farmer.id,
        estimated_harvest_date=reference_date + timedelta(days=3),
        estimated_quantity_kg=200,
        grade=QualityGrade.B,
        confidence=EstimateConfidence.MEDIUM,
        maturity_note="updated",
        reference_date=reference_date,
    )
    assert updated.estimated_quantity_kg == 200
    assert compute_data_version(database_path) != created_version

    updated_version = compute_data_version(database_path)
    cancelled = service.cancel_harvest(created.id)
    assert cancelled.status is BatchStatus.CANCELLED
    assert service.planned_quantity_summary([cancelled]) == 0
    assert compute_data_version(database_path) != updated_version


def test_harvest_service_creates_first_farmer_for_empty_workspace(
    database_path, reference_date
) -> None:
    reset_workspace(WorkspaceMode.EMPTY, database_path, reference_date=reference_date)
    service = HarvestService(database_path)

    farmer = service.create_farmer(
        name="Siti Rahayu",
        village_name="Sumber",
        subdistrict_name="Dukun",
    )

    assert farmer.active is True
    assert service.list_active_farmers() == [farmer]


@pytest.mark.parametrize("quantity", [0, -1, float("inf"), float("nan"), 100001])
def test_harvest_service_rejects_invalid_quantity(database_path, reference_date, quantity) -> None:
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    service = HarvestService(database_path)
    with pytest.raises(ValidationError):
        service.create_harvest(
            farmer_id=service.list_active_farmers()[0].id,
            estimated_harvest_date=reference_date,
            estimated_quantity_kg=quantity,
            grade=QualityGrade.A,
            confidence=EstimateConfidence.HIGH,
            reference_date=reference_date,
        )


def test_harvest_service_rejects_inactive_farmer(database_path, reference_date, aware_timestamp):
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    service = HarvestService(database_path)
    farmer = service.list_active_farmers()[0]
    FarmerRepository(database_path).deactivate(farmer.id, aware_timestamp)

    with pytest.raises(ValidationError):
        service.create_harvest(
            farmer_id=farmer.id,
            estimated_harvest_date=reference_date,
            estimated_quantity_kg=100,
            grade=QualityGrade.A,
            confidence=EstimateConfidence.HIGH,
            reference_date=reference_date,
        )


def test_buyer_and_demand_service_lifecycle_changes_version(database_path, reference_date) -> None:
    reset_workspace(WorkspaceMode.EMPTY, database_path, reference_date=reference_date)
    service = BuyerService(database_path)
    initial_version = compute_data_version(database_path)
    buyer = service.create_buyer(
        name="  Buyer Manual  ",
        channel=ChannelType.PROCESSOR,
        location="  Magelang  ",
        distance_km=12.5,
    )
    assert buyer.name == "Buyer Manual"
    assert compute_data_version(database_path) != initial_version

    buyer_version = compute_data_version(database_path)
    updated = service.update_buyer(
        buyer.id,
        name="Buyer Updated",
        channel=ChannelType.RETAILER,
        location="Mungkid",
        distance_km=10,
    )
    assert updated.channel is ChannelType.RETAILER
    assert compute_data_version(database_path) != buyer_version

    demand_version = compute_data_version(database_path)
    demand = service.create_demand(
        buyer_id=buyer.id,
        quantity_kg=350,
        accepted_grades=(QualityGrade.C, QualityGrade.A),
        deadline=reference_date + timedelta(days=3),
        priority=3,
        reference_date=reference_date,
    )
    assert demand.accepted_grades == (QualityGrade.A, QualityGrade.C)
    assert compute_data_version(database_path) != demand_version

    updated_demand = service.update_demand(
        demand.id,
        buyer_id=buyer.id,
        quantity_kg=400,
        accepted_grades=(QualityGrade.B,),
        deadline=reference_date + timedelta(days=4),
        priority=2,
        reference_date=reference_date,
    )
    assert updated_demand.quantity_kg == 400
    closed = service.close_demand(demand.id)
    assert closed.status is DemandStatus.CLOSED
    deactivated = service.deactivate_buyer(buyer.id)
    assert deactivated.active is False

    with pytest.raises(ValidationError):
        service.create_demand(
            buyer_id=buyer.id,
            quantity_kg=100,
            accepted_grades=(QualityGrade.A,),
            deadline=reference_date,
            priority=1,
            reference_date=reference_date,
        )


def test_demand_service_rejects_empty_and_duplicate_grades(database_path, reference_date) -> None:
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    service = BuyerService(database_path)
    buyer = service.list_buyers(active=True)[0]
    for grades in ((), (QualityGrade.A, QualityGrade.A)):
        with pytest.raises(ValidationError):
            service.create_demand(
                buyer_id=buyer.id,
                quantity_kg=100,
                accepted_grades=grades,
                deadline=reference_date,
                priority=1,
                reference_date=reference_date,
            )


def test_capacity_service_missing_days_upsert_and_version(database_path, reference_date) -> None:
    reset_workspace(WorkspaceMode.EMPTY, database_path, reference_date=reference_date)
    service = CapacityService(database_path)
    assert all(
        day.missing and day.available_capacity_kg == 0
        for day in service.seven_day_horizon(reference_date)
    )
    initial_version = compute_data_version(database_path)

    stored = service.upsert_capacity(
        capacity_date=reference_date,
        available_capacity_kg=750,
        note="  Manual capacity  ",
    )
    assert stored.note == "Manual capacity"
    assert compute_data_version(database_path) != initial_version
    horizon = service.seven_day_horizon(reference_date)
    assert horizon[0].missing is False
    assert horizon[0].available_capacity_kg == 750
    assert all(day.missing for day in horizon[1:])

    with pytest.raises(ValidationError):
        service.upsert_capacity(
            capacity_date=reference_date,
            available_capacity_kg=float("inf"),
        )


def test_capacity_week_is_validated_before_atomic_write(database_path, reference_date) -> None:
    reset_workspace(WorkspaceMode.EMPTY, database_path, reference_date=reference_date)
    service = CapacityService(database_path)

    with pytest.raises(ValidationError):
        service.upsert_week(
            [
                (reference_date, 500, None),
                (reference_date + timedelta(days=1), -1, None),
            ]
        )
    assert service.capacities.count() == 0

    stored = service.upsert_week(
        [(reference_date + timedelta(days=offset), 500 + offset, None) for offset in range(7)]
    )
    assert len(stored) == 7
    assert all(not day.missing for day in service.seven_day_horizon(reference_date))

    with pytest.raises(ValidationError):
        service.upsert_week([(reference_date, 100, None), (reference_date, 200, None)])


def test_seeded_records_can_mutate_before_their_deterministic_clock_time(database_path) -> None:
    future_reference = date.today() + timedelta(days=1)
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=future_reference)

    harvest_service = HarvestService(database_path)
    harvest = harvest_service.list_harvests(status=BatchStatus.PLANNED)[0]
    assert harvest_service.cancel_harvest(harvest.id).status is BatchStatus.CANCELLED

    buyer_service = BuyerService(database_path)
    buyer = buyer_service.list_buyers(active=True)[0]
    updated_buyer = buyer_service.update_buyer(
        buyer.id,
        name=buyer.name,
        channel=buyer.channel,
        location=buyer.location,
        distance_km=buyer.distance_km + 1,
    )
    assert updated_buyer.updated_at >= updated_buyer.created_at
    demand = buyer_service.list_demands(status=DemandStatus.OPEN)[0]
    assert buyer_service.close_demand(demand.id).status is DemandStatus.CLOSED

    capacity_service = CapacityService(database_path)
    capacity = capacity_service.upsert_capacity(
        capacity_date=future_reference,
        available_capacity_kg=777,
        note="Before deterministic clock time",
    )
    assert capacity.updated_at >= capacity.created_at
