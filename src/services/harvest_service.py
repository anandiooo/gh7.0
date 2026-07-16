from __future__ import annotations

from datetime import date, datetime, timedelta
from uuid import uuid4

from pydantic import ValidationError as PydanticValidationError

from src.config import APP_TIMEZONE, MAX_HARVEST_FUTURE_DAYS, PILOT_COMMODITY_CODE
from src.db.connection import DatabasePath
from src.db.repositories import FarmerRepository, HarvestRepository
from src.enums import BatchStatus, EstimateConfidence, QualityGrade, SourceType
from src.errors import ValidationError
from src.models import Farmer, HarvestBatch
from src.services._timestamps import mutation_timestamp


class HarvestService:
    def __init__(self, database_path: DatabasePath | None = None) -> None:
        self.database_path = database_path
        self.farmers = FarmerRepository(database_path)
        self.harvests = HarvestRepository(database_path)

    def list_active_farmers(self) -> list[Farmer]:
        """Return active farmers in stable display order."""
        return self.farmers.list(active=True)

    def list_harvests(
        self,
        *,
        farmer_id: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        grade: QualityGrade | None = None,
        confidence: EstimateConfidence | None = None,
        status: BatchStatus | None = None,
    ) -> list[HarvestBatch]:
        """Return harvests matching optional UI filters in stable order."""
        batches = self.harvests.list(status=status)
        return [
            batch
            for batch in batches
            if (farmer_id is None or batch.farmer_id == farmer_id)
            and (start_date is None or batch.estimated_harvest_date >= start_date)
            and (end_date is None or batch.estimated_harvest_date <= end_date)
            and (grade is None or batch.grade is grade)
            and (confidence is None or batch.confidence is confidence)
        ]

    def planned_quantity_summary(self, batches: list[HarvestBatch] | None = None) -> float:
        """Return planned kilograms, excluding cancelled harvests."""
        selected = batches if batches is not None else self.harvests.list()
        return sum(
            batch.estimated_quantity_kg for batch in selected if batch.status is BatchStatus.PLANNED
        )

    def create_harvest(
        self,
        *,
        farmer_id: str,
        estimated_harvest_date: date,
        estimated_quantity_kg: float,
        grade: QualityGrade,
        confidence: EstimateConfidence,
        maturity_note: str | None = None,
        reference_date: date | None = None,
    ) -> HarvestBatch:
        """Validate and create one manual harvest or raise a typed application error."""
        farmer = self.farmers.get_by_id(farmer_id.strip())
        if not farmer.active:
            raise ValidationError("A new harvest requires an active farmer")
        self._validate_manual_date(estimated_harvest_date, reference_date)
        timestamp = datetime.now(APP_TIMEZONE)
        try:
            batch = HarvestBatch(
                id=str(uuid4()),
                farmer_id=farmer.id,
                commodity_code=PILOT_COMMODITY_CODE,
                estimated_harvest_date=estimated_harvest_date,
                estimated_quantity_kg=estimated_quantity_kg,
                grade=grade,
                confidence=confidence,
                maturity_note=maturity_note,
                status=BatchStatus.PLANNED,
                source=SourceType.MANUAL,
                import_fingerprint=None,
                created_at=timestamp,
                updated_at=timestamp,
            )
        except PydanticValidationError as exc:
            raise ValidationError("Harvest input validation failed") from exc
        return self.harvests.create(batch)

    def update_harvest(
        self,
        batch_id: str,
        *,
        farmer_id: str,
        estimated_harvest_date: date,
        estimated_quantity_kg: float,
        grade: QualityGrade,
        confidence: EstimateConfidence,
        maturity_note: str | None = None,
        reference_date: date | None = None,
    ) -> HarvestBatch:
        """Validate and update mutable harvest fields while retaining lifecycle state."""
        existing = self.harvests.get_by_id(batch_id)
        self.farmers.get_by_id(farmer_id.strip())
        self._validate_manual_date(estimated_harvest_date, reference_date)
        values = existing.model_dump()
        values.update(
            farmer_id=farmer_id,
            estimated_harvest_date=estimated_harvest_date,
            estimated_quantity_kg=estimated_quantity_kg,
            grade=grade,
            confidence=confidence,
            maturity_note=maturity_note,
            updated_at=mutation_timestamp(existing.created_at),
        )
        try:
            updated = HarvestBatch.model_validate(values)
        except PydanticValidationError as exc:
            raise ValidationError("Harvest input validation failed") from exc
        return self.harvests.update(updated)

    def cancel_harvest(self, batch_id: str) -> HarvestBatch:
        """Retain a harvest while marking it cancelled for future analysis exclusion."""
        existing = self.harvests.get_by_id(batch_id)
        return self.harvests.cancel(batch_id, mutation_timestamp(existing.created_at))

    @staticmethod
    def _validate_manual_date(value: date, reference_date: date | None) -> None:
        today = reference_date or datetime.now(APP_TIMEZONE).date()
        if value < today or value > today + timedelta(days=MAX_HARVEST_FUTURE_DAYS):
            raise ValidationError("Harvest date is outside the allowed manual planning horizon")


__all__ = ["HarvestService"]
