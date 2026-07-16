from __future__ import annotations

from datetime import date, datetime
from uuid import uuid4

from pydantic import ValidationError as PydanticValidationError

from src.config import APP_TIMEZONE, PILOT_COMMODITY_CODE
from src.db.connection import DatabasePath
from src.db.repositories import BuyerRepository, DemandRepository
from src.enums import ChannelType, DemandStatus, QualityGrade, SeedableSource
from src.errors import ValidationError
from src.models import Buyer, BuyerDemand
from src.services._timestamps import mutation_timestamp


class BuyerService:
    def __init__(self, database_path: DatabasePath | None = None) -> None:
        self.buyers = BuyerRepository(database_path)
        self.demands = DemandRepository(database_path)

    def list_buyers(self, *, active: bool | None = None) -> list[Buyer]:
        """Return buyers in stable display order."""
        return self.buyers.list(active=active)

    def create_buyer(
        self, *, name: str, channel: ChannelType, location: str, distance_km: float
    ) -> Buyer:
        """Validate and create an active buyer."""
        timestamp = datetime.now(APP_TIMEZONE)
        try:
            buyer = Buyer(
                id=str(uuid4()),
                name=name,
                channel=channel,
                location=location,
                distance_km=distance_km,
                active=True,
                created_at=timestamp,
                updated_at=timestamp,
            )
        except PydanticValidationError as exc:
            raise ValidationError("Buyer input validation failed") from exc
        return self.buyers.create(buyer)

    def update_buyer(
        self,
        buyer_id: str,
        *,
        name: str,
        channel: ChannelType,
        location: str,
        distance_km: float,
    ) -> Buyer:
        """Validate and update mutable buyer fields without reactivating it."""
        existing = self.buyers.get_by_id(buyer_id)
        values = existing.model_dump()
        values.update(
            name=name,
            channel=channel,
            location=location,
            distance_km=distance_km,
            updated_at=mutation_timestamp(existing.created_at),
        )
        try:
            updated = Buyer.model_validate(values)
        except PydanticValidationError as exc:
            raise ValidationError("Buyer input validation failed") from exc
        return self.buyers.update(updated)

    def deactivate_buyer(self, buyer_id: str) -> Buyer:
        """Deactivate a buyer while retaining it and its historical demands."""
        existing = self.buyers.get_by_id(buyer_id)
        return self.buyers.deactivate(buyer_id, mutation_timestamp(existing.created_at))

    def list_demands(self, *, status: DemandStatus | None = None) -> list[BuyerDemand]:
        """Return buyer demands in stable deadline order."""
        return self.demands.list(status=status)

    def create_demand(
        self,
        *,
        buyer_id: str,
        quantity_kg: float,
        accepted_grades: tuple[QualityGrade, ...],
        deadline: date,
        priority: int,
        reference_date: date | None = None,
    ) -> BuyerDemand:
        """Validate and create one open manual demand for an active buyer."""
        buyer = self.buyers.get_by_id(buyer_id)
        if not buyer.active:
            raise ValidationError("A new demand requires an active buyer")
        self._validate_deadline(deadline, reference_date)
        return self.demands.create(
            self._build_demand(
                buyer_id=buyer.id,
                quantity_kg=quantity_kg,
                accepted_grades=accepted_grades,
                deadline=deadline,
                priority=priority,
            )
        )

    def update_demand(
        self,
        demand_id: str,
        *,
        buyer_id: str,
        quantity_kg: float,
        accepted_grades: tuple[QualityGrade, ...],
        deadline: date,
        priority: int,
        reference_date: date | None = None,
    ) -> BuyerDemand:
        """Validate and update mutable demand fields while retaining its status."""
        existing = self.demands.get_by_id(demand_id)
        self.buyers.get_by_id(buyer_id)
        self._validate_deadline(deadline, reference_date)
        values = existing.model_dump()
        values.update(
            buyer_id=buyer_id,
            quantity_kg=quantity_kg,
            accepted_grades=accepted_grades,
            deadline=deadline,
            priority=priority,
            updated_at=mutation_timestamp(existing.created_at),
        )
        try:
            updated = BuyerDemand.model_validate(values)
        except PydanticValidationError as exc:
            raise ValidationError("Demand input validation failed") from exc
        return self.demands.update(updated)

    def close_demand(self, demand_id: str) -> BuyerDemand:
        """Retain a demand while marking it closed for optimization exclusion."""
        existing = self.demands.get_by_id(demand_id)
        return self.demands.close(demand_id, mutation_timestamp(existing.created_at))

    @staticmethod
    def _build_demand(
        *,
        buyer_id: str,
        quantity_kg: float,
        accepted_grades: tuple[QualityGrade, ...],
        deadline: date,
        priority: int,
    ) -> BuyerDemand:
        timestamp = datetime.now(APP_TIMEZONE)
        try:
            return BuyerDemand(
                id=str(uuid4()),
                buyer_id=buyer_id,
                commodity_code=PILOT_COMMODITY_CODE,
                quantity_kg=quantity_kg,
                accepted_grades=accepted_grades,
                deadline=deadline,
                priority=priority,
                status=DemandStatus.OPEN,
                source=SeedableSource.MANUAL,
                created_at=timestamp,
                updated_at=timestamp,
            )
        except PydanticValidationError as exc:
            raise ValidationError("Demand input validation failed") from exc

    @staticmethod
    def _validate_deadline(value: date, reference_date: date | None) -> None:
        today = reference_date or datetime.now(APP_TIMEZONE).date()
        if value < today:
            raise ValidationError("Demand deadline must not be in the past")


__all__ = ["BuyerService"]
