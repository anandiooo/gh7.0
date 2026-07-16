from __future__ import annotations

from datetime import date, timedelta

from src.analysis_models import (
    AnalysisDemand,
    AnalysisHarvest,
    AnalysisInput,
    DailyCapacity,
    DailyCompatibleDemand,
    DailySupply,
    WeatherDisruptionInput,
)
from src.config import OPERATIONAL_HORIZON_DAYS, PILOT_COMMODITY_CODE
from src.db.connection import DatabasePath
from src.db.repositories import (
    BuyerRepository,
    CapacityRepository,
    DemandRepository,
    FarmerRepository,
    HarvestRepository,
)
from src.enums import BatchStatus, DemandStatus, WeatherSourceStatus
from src.services.data_version_service import compute_data_version


class AnalysisInputService:
    def __init__(self, database_path: DatabasePath | None = None) -> None:
        self.database_path = database_path
        self.farmers = FarmerRepository(database_path)
        self.harvests = HarvestRepository(database_path)
        self.buyers = BuyerRepository(database_path)
        self.demands = DemandRepository(database_path)
        self.capacities = CapacityRepository(database_path)

    def build(self, horizon_start: date) -> AnalysisInput:
        """Build stable canonical seven-day inputs for risk and allocation."""
        horizon_end = horizon_start + timedelta(days=OPERATIONAL_HORIZON_DAYS - 1)
        farmers = {item.id: item for item in self.farmers.list(active=True)}
        buyers = {item.id: item for item in self.buyers.list(active=True)}
        harvests = tuple(
            AnalysisHarvest(
                batch_id=batch.id,
                farmer_id=batch.farmer_id,
                farmer_name=farmers[batch.farmer_id].name,
                harvest_date=batch.estimated_harvest_date,
                quantity_kg=batch.estimated_quantity_kg,
                grade=batch.grade,
                confidence=batch.confidence,
            )
            for batch in self.harvests.list_planned_within(horizon_start, horizon_end)
            if batch.farmer_id in farmers
            and batch.commodity_code == PILOT_COMMODITY_CODE
            and batch.status is BatchStatus.PLANNED
        )
        demands = tuple(
            AnalysisDemand(
                demand_id=demand.id,
                buyer_id=demand.buyer_id,
                buyer_name=buyers[demand.buyer_id].name,
                channel=buyers[demand.buyer_id].channel.value,
                deadline=demand.deadline,
                quantity_kg=demand.quantity_kg,
                accepted_grades=demand.accepted_grades,
                priority=demand.priority,
                distance_km=buyers[demand.buyer_id].distance_km,
            )
            for demand in self.demands.list(status=DemandStatus.OPEN)
            if demand.buyer_id in buyers
            and demand.commodity_code == PILOT_COMMODITY_CODE
            and horizon_start <= demand.deadline <= horizon_end
        )
        dates = tuple(horizon_start + timedelta(days=offset) for offset in range(7))
        compatible_demands = tuple(
            demand for demand in demands if self._is_compatible(demand, harvests)
        )
        capacities = {
            item.date: item for item in self.capacities.list_date_range(horizon_start, horizon_end)
        }
        return AnalysisInput(
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            data_version=compute_data_version(self.database_path),
            harvests=harvests,
            demands=demands,
            daily_supply=tuple(
                DailySupply(
                    date=current,
                    quantity_kg=sum(
                        batch.quantity_kg for batch in harvests if batch.harvest_date == current
                    ),
                )
                for current in dates
            ),
            daily_compatible_demand=tuple(
                DailyCompatibleDemand(
                    date=current,
                    quantity_kg=sum(
                        demand.quantity_kg
                        for demand in compatible_demands
                        if demand.deadline == current
                    ),
                )
                for current in dates
            ),
            daily_capacity=tuple(
                DailyCapacity(
                    date=current,
                    quantity_kg=(
                        capacities[current].available_capacity_kg if current in capacities else 0
                    ),
                    missing=current not in capacities,
                )
                for current in dates
            ),
            compatible_demand_kg=sum(item.quantity_kg for item in compatible_demands),
            weather=WeatherDisruptionInput(status=WeatherSourceStatus.UNAVAILABLE),
        )

    @staticmethod
    def _is_compatible(demand: AnalysisDemand, harvests: tuple[AnalysisHarvest, ...]) -> bool:
        return any(
            harvest.grade in demand.accepted_grades and harvest.harvest_date <= demand.deadline
            for harvest in harvests
        )


__all__ = ["AnalysisInputService"]
