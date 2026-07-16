import json
import math
from datetime import date
from typing import Annotated, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

from src.config import (
    MAX_BUYER_DISTANCE_KM,
    MAX_CAPACITY_KG,
    MAX_HARVEST_QUANTITY_KG,
    PILOT_COMMODITY_CODE,
)
from src.enums import (
    AnalysisRunType,
    BatchStatus,
    ChannelType,
    DemandStatus,
    EstimateConfidence,
    QualityGrade,
    RiskLevel,
    SeedableSource,
    SolverStatus,
    SourceType,
    WeatherSourceStatus,
    WorkspaceMode,
)

NonBlankStr = Annotated[str, Field(min_length=1)]


def _normalize_non_blank(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("value must not be blank")
    return normalized


def _canonical_json(value: str) -> str:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("value must be valid serialized JSON") from exc
    return json.dumps(parsed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    @field_validator("id", check_fields=False)
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _normalize_non_blank(value)


class TimestampedModel(DomainModel):
    created_at: AwareDatetime
    updated_at: AwareDatetime

    @model_validator(mode="after")
    def validate_timestamps(self) -> Self:
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not be before created_at")
        return self


class CooperativeProfile(TimestampedModel):
    id: NonBlankStr
    name: NonBlankStr
    pilot_region: NonBlankStr
    commodity_code: str
    adm4_code: NonBlankStr
    workspace_mode: WorkspaceMode

    @field_validator("name", "pilot_region", "adm4_code")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return _normalize_non_blank(value)

    @field_validator("commodity_code")
    @classmethod
    def validate_commodity(cls, value: str) -> str:
        if value != PILOT_COMMODITY_CODE:
            raise ValueError(f"commodity_code must be {PILOT_COMMODITY_CODE}")
        return value


class Farmer(TimestampedModel):
    id: NonBlankStr
    name: Annotated[str, Field(min_length=2, max_length=100)]
    village_name: NonBlankStr
    subdistrict_name: NonBlankStr
    active: bool = True

    @field_validator("name", "village_name", "subdistrict_name")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return _normalize_non_blank(value)


class HarvestBatch(TimestampedModel):
    id: NonBlankStr
    farmer_id: NonBlankStr
    commodity_code: str
    estimated_harvest_date: date
    estimated_quantity_kg: float = Field(gt=0, le=MAX_HARVEST_QUANTITY_KG)
    grade: QualityGrade
    confidence: EstimateConfidence
    maturity_note: str | None = None
    status: BatchStatus
    source: SourceType
    import_fingerprint: str | None = None

    @field_validator("farmer_id")
    @classmethod
    def validate_farmer_id(cls, value: str) -> str:
        return _normalize_non_blank(value)

    @field_validator("commodity_code")
    @classmethod
    def validate_commodity(cls, value: str) -> str:
        if value != PILOT_COMMODITY_CODE:
            raise ValueError(f"commodity_code must be {PILOT_COMMODITY_CODE}")
        return value

    @field_validator("estimated_quantity_kg")
    @classmethod
    def validate_quantity(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("estimated_quantity_kg must be finite")
        return value

    @field_validator("maturity_note", "import_fingerprint")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class Buyer(TimestampedModel):
    id: NonBlankStr
    name: NonBlankStr
    channel: ChannelType
    location: NonBlankStr
    distance_km: float = Field(ge=0, le=MAX_BUYER_DISTANCE_KM)
    active: bool = True

    @field_validator("name", "location")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return _normalize_non_blank(value)

    @field_validator("distance_km")
    @classmethod
    def validate_distance(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("distance_km must be finite")
        return value


class BuyerDemand(TimestampedModel):
    id: NonBlankStr
    buyer_id: NonBlankStr
    commodity_code: str
    quantity_kg: float = Field(gt=0, le=MAX_HARVEST_QUANTITY_KG)
    accepted_grades: tuple[QualityGrade, ...]
    deadline: date
    priority: int = Field(ge=1, le=3)
    status: DemandStatus
    source: SeedableSource

    @field_validator("buyer_id")
    @classmethod
    def validate_buyer_id(cls, value: str) -> str:
        return _normalize_non_blank(value)

    @field_validator("commodity_code")
    @classmethod
    def validate_commodity(cls, value: str) -> str:
        if value != PILOT_COMMODITY_CODE:
            raise ValueError(f"commodity_code must be {PILOT_COMMODITY_CODE}")
        return value

    @field_validator("quantity_kg")
    @classmethod
    def validate_quantity(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("quantity_kg must be finite")
        return value

    @field_validator("accepted_grades")
    @classmethod
    def validate_accepted_grades(cls, value: tuple[QualityGrade, ...]) -> tuple[QualityGrade, ...]:
        if not value:
            raise ValueError("accepted_grades must contain at least one grade")
        if len(set(value)) != len(value):
            raise ValueError("accepted_grades must not contain duplicates")
        return tuple(sorted(value, key=lambda grade: grade.value))


class DistributionCapacity(TimestampedModel):
    id: NonBlankStr
    date: date
    available_capacity_kg: float = Field(ge=0, le=MAX_CAPACITY_KG)
    source: SeedableSource
    note: str | None = None

    @field_validator("available_capacity_kg")
    @classmethod
    def validate_capacity(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("available_capacity_kg must be finite")
        return value

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class WeatherSnapshot(DomainModel):
    id: NonBlankStr
    adm4_code: NonBlankStr
    fetched_at: AwareDatetime
    analysis_date: AwareDatetime | None = None
    valid_from: AwareDatetime | None = None
    valid_until: AwareDatetime | None = None
    source_status: WeatherSourceStatus
    normalized_json: str
    raw_payload_json: str

    @field_validator("adm4_code")
    @classmethod
    def validate_adm4_code(cls, value: str) -> str:
        return _normalize_non_blank(value)

    @field_validator("source_status")
    @classmethod
    def validate_stored_status(cls, value: WeatherSourceStatus) -> WeatherSourceStatus:
        if value not in {WeatherSourceStatus.LIVE, WeatherSourceStatus.CACHE}:
            raise ValueError("stored weather source_status must be LIVE or CACHE")
        return value

    @field_validator("normalized_json", "raw_payload_json")
    @classmethod
    def validate_json(cls, value: str) -> str:
        return _canonical_json(value)

    @model_validator(mode="after")
    def validate_window(self) -> Self:
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("valid_until must not be before valid_from")
        return self


class AnalysisRun(DomainModel):
    id: NonBlankStr
    parent_run_id: str | None = None
    scenario_name: str | None = None
    run_type: AnalysisRunType
    created_at: AwareDatetime
    horizon_start: date
    horizon_end: date
    data_version: NonBlankStr
    risk_score: float | None = Field(default=None, ge=0, le=100)
    risk_level: RiskLevel | None = None
    total_supply_kg: float | None = Field(default=None, ge=0)
    compatible_demand_kg: float | None = Field(default=None, ge=0)
    allocated_kg: float | None = Field(default=None, ge=0)
    unallocated_kg: float | None = Field(default=None, ge=0)
    unallocated_supply_rate: float | None = Field(default=None, ge=0, le=1)
    demand_fulfillment_rate: float | None = Field(default=None, ge=0, le=1)
    solver_status: SolverStatus | None = None
    weather_status: WeatherSourceStatus | None = None
    input_snapshot_json: str
    override_snapshot_json: str | None = None
    risk_snapshot_json: str | None = None
    result_snapshot_json: str | None = None
    error_message: str | None = None

    @field_validator("data_version")
    @classmethod
    def validate_data_version(cls, value: str) -> str:
        return _normalize_non_blank(value)

    @field_validator("parent_run_id", "scenario_name", "error_message")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator(
        "input_snapshot_json",
        "override_snapshot_json",
        "risk_snapshot_json",
        "result_snapshot_json",
    )
    @classmethod
    def validate_json(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _canonical_json(value)

    @model_validator(mode="after")
    def validate_run(self) -> Self:
        if self.horizon_end < self.horizon_start:
            raise ValueError("horizon_end must not be before horizon_start")
        if self.parent_run_id == self.id:
            raise ValueError("parent_run_id must not reference the same run")
        return self


class Allocation(DomainModel):
    id: NonBlankStr
    analysis_run_id: NonBlankStr
    harvest_batch_id: NonBlankStr
    buyer_demand_id: NonBlankStr
    delivery_date: date
    quantity_kg: float = Field(gt=0, le=MAX_HARVEST_QUANTITY_KG)
    distance_km_snapshot: float = Field(ge=0, le=MAX_BUYER_DISTANCE_KM)
    reason_json: str
    created_at: AwareDatetime

    @field_validator("analysis_run_id", "harvest_batch_id", "buyer_demand_id")
    @classmethod
    def validate_foreign_id(cls, value: str) -> str:
        return _normalize_non_blank(value)

    @field_validator("quantity_kg", "distance_km_snapshot")
    @classmethod
    def validate_finite_number(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("numeric values must be finite")
        return value

    @field_validator("reason_json")
    @classmethod
    def validate_reason_json(cls, value: str) -> str:
        return _canonical_json(value)
