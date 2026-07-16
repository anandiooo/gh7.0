from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.enums import (
    AllocationReasonCode,
    EstimateConfidence,
    QualityGrade,
    RecommendedActionCode,
    RiskFactorCode,
    RiskLevel,
    SolverStatus,
    WeatherSourceStatus,
)


class AnalysisContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DailySupply(AnalysisContract):
    date: date
    quantity_kg: float = Field(ge=0)


class DailyCompatibleDemand(AnalysisContract):
    date: date
    quantity_kg: float = Field(ge=0)


class DailyCapacity(AnalysisContract):
    date: date
    quantity_kg: float = Field(ge=0)
    missing: bool = False


class AnalysisHarvest(AnalysisContract):
    batch_id: str
    farmer_id: str
    farmer_name: str
    harvest_date: date
    quantity_kg: float = Field(gt=0)
    grade: QualityGrade
    confidence: EstimateConfidence


class AnalysisDemand(AnalysisContract):
    demand_id: str
    buyer_id: str
    buyer_name: str
    channel: str
    deadline: date
    quantity_kg: float = Field(gt=0)
    accepted_grades: tuple[QualityGrade, ...]
    priority: int = Field(ge=1, le=3)
    distance_km: float = Field(ge=0)


class WeatherDisruptionInput(AnalysisContract):
    status: WeatherSourceStatus = WeatherSourceStatus.UNAVAILABLE
    daily_scores: tuple[tuple[date, float], ...] = ()

    @model_validator(mode="after")
    def validate_scores(self) -> WeatherDisruptionInput:
        if any(score < 0 or score > 1 for _, score in self.daily_scores):
            raise ValueError("weather disruption scores must be between zero and one")
        return self


class AnalysisInput(AnalysisContract):
    horizon_start: date
    horizon_end: date
    data_version: str
    harvests: tuple[AnalysisHarvest, ...]
    demands: tuple[AnalysisDemand, ...]
    daily_supply: tuple[DailySupply, ...]
    daily_compatible_demand: tuple[DailyCompatibleDemand, ...]
    daily_capacity: tuple[DailyCapacity, ...]
    compatible_demand_kg: float = Field(ge=0)
    weather: WeatherDisruptionInput

    @model_validator(mode="after")
    def validate_horizon(self) -> AnalysisInput:
        if self.horizon_end < self.horizon_start:
            raise ValueError("analysis horizon end must not precede its start")
        return self

    @property
    def total_supply_kg(self) -> float:
        return sum(item.quantity_kg for item in self.harvests)

    @property
    def total_capacity_kg(self) -> float:
        return sum(item.quantity_kg for item in self.daily_capacity)


class RiskFactor(AnalysisContract):
    code: RiskFactorCode
    raw_value: float = Field(ge=0, le=1)
    weight: float = Field(ge=0)
    weighted_points: float = Field(ge=0)


class RiskResult(AnalysisContract):
    has_data: bool
    score: float | None = Field(default=None, ge=0, le=100)
    level: RiskLevel | None = None
    total_supply_kg: float = Field(ge=0)
    compatible_demand_kg: float = Field(ge=0)
    critical_date: date | None = None
    factors: tuple[RiskFactor, ...]
    top_factors: tuple[RiskFactorCode, ...]
    recommended_actions: tuple[RecommendedActionCode, ...]
    weather_status: WeatherSourceStatus
    warnings: tuple[str, ...] = ()
    runtime_ms: float = Field(ge=0)


class OptimizationInput(AnalysisContract):
    analysis: AnalysisInput


class AllocationDecision(AnalysisContract):
    harvest_batch_id: str
    buyer_demand_id: str
    delivery_date: date
    quantity_kg: float = Field(gt=0)
    distance_km: float = Field(ge=0)
    reason_codes: tuple[AllocationReasonCode, ...]


class UnallocatedBatch(AnalysisContract):
    harvest_batch_id: str
    quantity_kg: float = Field(ge=0)
    grade: QualityGrade
    harvest_date: date


class UnmetDemand(AnalysisContract):
    buyer_demand_id: str
    quantity_kg: float = Field(ge=0)
    deadline: date


class OptimizationResult(AnalysisContract):
    status: SolverStatus
    objective_value: float | None = None
    allocations: tuple[AllocationDecision, ...]
    allocated_kg: float = Field(ge=0)
    unallocated_kg: float = Field(ge=0)
    unmet_demand_kg: float = Field(ge=0)
    unallocated_supply_rate: float = Field(ge=0, le=1)
    demand_fulfillment_rate: float = Field(ge=0, le=1)
    unallocated_batches: tuple[UnallocatedBatch, ...]
    unmet_demands: tuple[UnmetDemand, ...]
    warnings: tuple[str, ...] = ()
    runtime_ms: float = Field(ge=0)


class RadarResult(AnalysisContract):
    analysis: AnalysisInput
    risk: RiskResult
    optimization: OptimizationResult
    potential_surplus_kg: float = Field(ge=0)
    operationally_constrained_surplus_kg: float = Field(ge=0)


class TemporaryBuyerDemandOverride(AnalysisContract):
    buyer_id: str
    buyer_name: str
    channel: str
    distance_km: float = Field(ge=0)
    quantity_kg: float = Field(gt=0)
    accepted_grades: tuple[QualityGrade, ...]
    deadline: date
    priority: int = Field(ge=1, le=3)

    @model_validator(mode="after")
    def validate_grades(self) -> TemporaryBuyerDemandOverride:
        if not self.accepted_grades:
            raise ValueError("scenario demand must accept at least one grade")
        if len(set(self.accepted_grades)) != len(self.accepted_grades):
            raise ValueError("scenario demand grades must not contain duplicates")
        return self


class TemporaryCapacityOverride(AnalysisContract):
    date: date
    effective_capacity_kg: float = Field(ge=0)


class ScenarioOverrides(AnalysisContract):
    scenario_name: str = Field(min_length=1, max_length=100)
    buyer_demand: TemporaryBuyerDemandOverride | None = None
    capacities: tuple[TemporaryCapacityOverride, ...] = ()

    @model_validator(mode="after")
    def validate_overrides(self) -> ScenarioOverrides:
        if not self.scenario_name.strip():
            raise ValueError("scenario name must not be blank")
        dates = [item.date for item in self.capacities]
        if len(set(dates)) != len(dates):
            raise ValueError("scenario capacity dates must not contain duplicates")
        return self


class ScenarioComparison(AnalysisContract):
    risk_score_delta: float
    allocated_kg_delta: float
    unallocated_kg_delta: float
    unallocated_supply_rate_delta: float
    demand_fulfillment_rate_delta: float
    unmet_demand_kg_delta: float


class ScenarioResult(AnalysisContract):
    overrides: ScenarioOverrides
    analysis: AnalysisInput
    risk: RiskResult
    optimization: OptimizationResult
    comparison: ScenarioComparison


__all__ = [
    "AllocationDecision",
    "AnalysisDemand",
    "AnalysisHarvest",
    "AnalysisInput",
    "DailyCapacity",
    "DailyCompatibleDemand",
    "DailySupply",
    "OptimizationInput",
    "OptimizationResult",
    "RadarResult",
    "RiskFactor",
    "RiskResult",
    "ScenarioComparison",
    "ScenarioOverrides",
    "ScenarioResult",
    "TemporaryBuyerDemandOverride",
    "TemporaryCapacityOverride",
    "UnallocatedBatch",
    "UnmetDemand",
    "WeatherDisruptionInput",
]
