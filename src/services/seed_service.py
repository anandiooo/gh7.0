import sqlite3
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from uuid import UUID, uuid5

from src.config import (
    APP_TIMEZONE,
    DEFAULT_ADM4_CODE,
    DEFAULT_COOPERATIVE_NAME,
    PILOT_COMMODITY_CODE,
    PILOT_REGION,
)
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
    BatchStatus,
    ChannelType,
    DemandStatus,
    EstimateConfidence,
    QualityGrade,
    SeedableSource,
    SourceType,
    WorkspaceMode,
)
from src.errors import ValidationError
from src.models import (
    Buyer,
    BuyerDemand,
    CooperativeProfile,
    DistributionCapacity,
    Farmer,
    HarvestBatch,
)

_SEED_NAMESPACE = UUID("f84e38e4-3447-5c46-8150-166b55f478d2")


@dataclass(frozen=True)
class SeedCounts:
    cooperative_profiles: int
    farmers: int
    harvest_batches: int
    buyers: int
    buyer_demands: int
    distribution_capacities: int
    weather_snapshots: int
    analysis_runs: int
    allocations: int

    def as_dict(self) -> dict[str, int]:
        """Return count values for concise script and test reporting."""
        return asdict(self)


EXPECTED_DEMO_COUNTS = SeedCounts(1, 30, 42, 8, 16, 7, 0, 0, 0)
EXPECTED_EMPTY_COUNTS = SeedCounts(1, 0, 0, 0, 0, 0, 0, 0, 0)


class SeedService:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.cooperatives = CooperativeRepository(connection=connection)
        self.farmers = FarmerRepository(connection=connection)
        self.harvests = HarvestRepository(connection=connection)
        self.buyers = BuyerRepository(connection=connection)
        self.demands = DemandRepository(connection=connection)
        self.capacities = CapacityRepository(connection=connection)
        self.weather = WeatherRepository(connection=connection)
        self.analysis = AnalysisRepository(connection=connection)

    def seed_demo(self, reference_date: date) -> SeedCounts:
        """Insert the complete deterministic Demo dataset using the active transaction."""
        base_time = datetime.combine(reference_date, time.min, tzinfo=APP_TIMEZONE)
        profile = self._build_profile(WorkspaceMode.DEMO, reference_date, base_time)
        farmers = self._build_farmers(reference_date, base_time)
        harvests = self._build_harvests(reference_date, base_time, farmers)
        buyers = self._build_buyers(reference_date, base_time)
        demands = self._build_demands(reference_date, base_time, buyers)
        capacities = self._build_capacities(reference_date, base_time)

        self.cooperatives.create(profile)
        self.farmers.create_many(farmers)
        self.harvests.create_many(harvests)
        self.buyers.create_many(buyers)
        self.demands.create_many(demands)
        for capacity in capacities:
            self.capacities.upsert_by_date(capacity)
        return self.validate_counts(EXPECTED_DEMO_COUNTS)

    def seed_empty(self, reference_date: date) -> SeedCounts:
        """Insert only the deterministic Empty cooperative profile."""
        base_time = datetime.combine(reference_date, time.min, tzinfo=APP_TIMEZONE)
        self.cooperatives.create(
            self._build_profile(WorkspaceMode.EMPTY, reference_date, base_time)
        )
        return self.validate_counts(EXPECTED_EMPTY_COUNTS)

    def read_counts(self) -> SeedCounts:
        """Read exact counts for every canonical workspace table."""
        return SeedCounts(
            cooperative_profiles=int(self.cooperatives.get_profile() is not None),
            farmers=self.farmers.count(),
            harvest_batches=self.harvests.count(),
            buyers=self.buyers.count(),
            buyer_demands=self.demands.count(),
            distribution_capacities=self.capacities.count(),
            weather_snapshots=self.weather.count(),
            analysis_runs=self.analysis.count_runs(),
            allocations=self.analysis.count_allocations(),
        )

    def validate_counts(self, expected: SeedCounts) -> SeedCounts:
        """Return actual counts or raise when initialization is incomplete."""
        actual = self.read_counts()
        if actual != expected:
            raise ValidationError(f"Seed counts differ: expected {expected}, found {actual}")
        return actual

    @staticmethod
    def _seed_id(reference_date: date, entity: str, index: int = 0) -> str:
        return str(uuid5(_SEED_NAMESPACE, f"{reference_date.isoformat()}:{entity}:{index}"))

    @classmethod
    def _build_profile(
        cls, mode: WorkspaceMode, reference_date: date, created_at: datetime
    ) -> CooperativeProfile:
        return CooperativeProfile(
            id=cls._seed_id(reference_date, f"cooperative:{mode.value}"),
            name=DEFAULT_COOPERATIVE_NAME,
            pilot_region=PILOT_REGION,
            commodity_code=PILOT_COMMODITY_CODE,
            adm4_code=DEFAULT_ADM4_CODE,
            workspace_mode=mode,
            created_at=created_at,
            updated_at=created_at,
        )

    @classmethod
    def _build_farmers(cls, reference_date: date, base_time: datetime) -> list[Farmer]:
        locations = (
            ("Sengi", "Dukun"),
            ("Krinjing", "Dukun"),
            ("Paten", "Dukun"),
            ("Banyuroto", "Sawangan"),
            ("Ketep", "Sawangan"),
            ("Wonolelo", "Sawangan"),
            ("Kaliurang", "Srumbung"),
            ("Kemiren", "Srumbung"),
            ("Ngablak", "Ngablak"),
            ("Kanigoro", "Ngablak"),
        )
        return [
            Farmer(
                id=cls._seed_id(reference_date, "farmer", index),
                name=f"Petani Simulasi {index + 1:02d}",
                village_name=locations[index % len(locations)][0],
                subdistrict_name=locations[index % len(locations)][1],
                active=True,
                created_at=base_time + timedelta(minutes=index + 1),
                updated_at=base_time + timedelta(minutes=index + 1),
            )
            for index in range(30)
        ]

    @classmethod
    def _build_harvests(
        cls, reference_date: date, base_time: datetime, farmers: list[Farmer]
    ) -> list[HarvestBatch]:
        grades = tuple(QualityGrade)
        confidences = tuple(EstimateConfidence)
        batches: list[HarvestBatch] = []
        for index in range(42):
            day_offset = index % 7
            timestamp = base_time + timedelta(hours=2, minutes=index)
            batches.append(
                HarvestBatch(
                    id=cls._seed_id(reference_date, "harvest", index),
                    farmer_id=farmers[index % len(farmers)].id,
                    commodity_code=PILOT_COMMODITY_CODE,
                    estimated_harvest_date=reference_date + timedelta(days=day_offset),
                    estimated_quantity_kg=float(180 + (index % 6) * 30 + day_offset * 15),
                    grade=grades[index % len(grades)],
                    confidence=confidences[(index // 3) % len(confidences)],
                    maturity_note=f"Simulasi kematangan petak {index + 1:02d}",
                    status=BatchStatus.PLANNED,
                    source=SourceType.SEED,
                    import_fingerprint=f"SEED-{reference_date.isoformat()}-{index + 1:02d}",
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
        return batches

    @classmethod
    def _build_buyers(cls, reference_date: date, base_time: datetime) -> list[Buyer]:
        definitions = (
            ("Pasar Simulasi Muntilan", ChannelType.TRADITIONAL_MARKET, "Muntilan", 18.0),
            ("Pasar Simulasi Rejowinangun", ChannelType.TRADITIONAL_MARKET, "Magelang", 26.0),
            ("Retail Simulasi Magelang", ChannelType.RETAILER, "Mertoyudan", 23.0),
            ("Gerai Simulasi Sleman", ChannelType.RETAILER, "Sleman", 31.0),
            ("Dapur Simulasi Borobudur", ChannelType.RESTAURANT, "Borobudur", 28.0),
            ("Rumah Makan Simulasi Mungkid", ChannelType.RESTAURANT, "Mungkid", 21.0),
            ("Pengolah Simulasi Merapi", ChannelType.PROCESSOR, "Secang", 34.0),
            ("Unit Olahan Simulasi Grabag", ChannelType.PROCESSOR, "Grabag", 39.0),
        )
        return [
            Buyer(
                id=cls._seed_id(reference_date, "buyer", index),
                name=name,
                channel=channel,
                location=location,
                distance_km=distance,
                active=True,
                created_at=base_time + timedelta(hours=4, minutes=index),
                updated_at=base_time + timedelta(hours=4, minutes=index),
            )
            for index, (name, channel, location, distance) in enumerate(definitions)
        ]

    @classmethod
    def _build_demands(
        cls, reference_date: date, base_time: datetime, buyers: list[Buyer]
    ) -> list[BuyerDemand]:
        grade_sets = (
            (QualityGrade.A,),
            (QualityGrade.A, QualityGrade.B),
            (QualityGrade.B, QualityGrade.C),
            (QualityGrade.A, QualityGrade.B, QualityGrade.C),
        )
        return [
            BuyerDemand(
                id=cls._seed_id(reference_date, "demand", index),
                buyer_id=buyers[index % len(buyers)].id,
                commodity_code=PILOT_COMMODITY_CODE,
                quantity_kg=float(120 + (index % 4) * 35),
                accepted_grades=grade_sets[index % len(grade_sets)],
                deadline=reference_date + timedelta(days=index % 7),
                priority=(index % 3) + 1,
                status=DemandStatus.OPEN,
                source=SeedableSource.SEED,
                created_at=base_time + timedelta(hours=6, minutes=index),
                updated_at=base_time + timedelta(hours=6, minutes=index),
            )
            for index in range(16)
        ]

    @classmethod
    def _build_capacities(
        cls, reference_date: date, base_time: datetime
    ) -> list[DistributionCapacity]:
        daily_capacities = (700.0, 450.0, 900.0, 400.0, 800.0, 350.0, 750.0)
        return [
            DistributionCapacity(
                id=cls._seed_id(reference_date, "capacity", index),
                date=reference_date + timedelta(days=index),
                available_capacity_kg=capacity,
                source=SeedableSource.SEED,
                note="Kapasitas simulasi terbatas" if index in {1, 3, 5} else "Kapasitas simulasi",
                created_at=base_time + timedelta(hours=8, minutes=index),
                updated_at=base_time + timedelta(hours=8, minutes=index),
            )
            for index, capacity in enumerate(daily_capacities)
        ]


__all__ = [
    "EXPECTED_DEMO_COUNTS",
    "EXPECTED_EMPTY_COUNTS",
    "SeedCounts",
    "SeedService",
]
