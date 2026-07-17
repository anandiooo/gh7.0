from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from uuid import uuid4

from pydantic import ValidationError as PydanticValidationError

from src.config import APP_TIMEZONE, OPERATIONAL_HORIZON_DAYS
from src.db.connection import DatabasePath
from src.db.repositories import CapacityRepository
from src.enums import SeedableSource
from src.errors import ValidationError
from src.models import DistributionCapacity
from src.services._timestamps import mutation_timestamp


@dataclass(frozen=True)
class CapacityDay:
    date: date
    available_capacity_kg: float
    note: str | None
    missing: bool


class CapacityService:
    def __init__(self, database_path: DatabasePath | None = None) -> None:
        self.capacities = CapacityRepository(database_path)

    def seven_day_horizon(self, start_date: date) -> list[CapacityDay]:
        """Return seven effective daily capacities, treating missing records as zero."""
        end_date = start_date + timedelta(days=OPERATIONAL_HORIZON_DAYS - 1)
        stored = {item.date: item for item in self.capacities.list_date_range(start_date, end_date)}
        return [
            CapacityDay(
                date=current,
                available_capacity_kg=(
                    stored[current].available_capacity_kg if current in stored else 0
                ),
                note=stored[current].note if current in stored else None,
                missing=current not in stored,
            )
            for current in (start_date + timedelta(days=offset) for offset in range(7))
        ]

    def upsert_capacity(
        self, *, capacity_date: date, available_capacity_kg: float, note: str | None = None
    ) -> DistributionCapacity:
        """Validate and upsert one manual daily capacity record."""
        capacity = self._build_capacity(capacity_date, available_capacity_kg, note)
        return self.capacities.upsert_by_date(capacity)

    def upsert_week(
        self, values: list[tuple[date, float, str | None]]
    ) -> list[DistributionCapacity]:
        """Validate and save a set of daily capacities in one transaction."""
        dates = [capacity_date for capacity_date, _, _ in values]
        if not values or len(set(dates)) != len(dates):
            raise ValidationError("Capacity dates must be present and unique")
        capacities = [
            self._build_capacity(capacity_date, quantity, note)
            for capacity_date, quantity, note in values
        ]
        return self.capacities.upsert_many(capacities)

    def _build_capacity(
        self, capacity_date: date, available_capacity_kg: float, note: str | None
    ) -> DistributionCapacity:
        existing = self.capacities.get_by_date(capacity_date)
        timestamp = (
            mutation_timestamp(existing.created_at) if existing else datetime.now(APP_TIMEZONE)
        )
        try:
            return DistributionCapacity(
                id=existing.id if existing else str(uuid4()),
                date=capacity_date,
                available_capacity_kg=available_capacity_kg,
                source=SeedableSource.MANUAL,
                note=note,
                created_at=existing.created_at if existing else timestamp,
                updated_at=timestamp,
            )
        except PydanticValidationError as exc:
            raise ValidationError("Capacity input validation failed") from exc


__all__ = ["CapacityDay", "CapacityService"]
