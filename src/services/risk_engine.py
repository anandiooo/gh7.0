from __future__ import annotations

from time import perf_counter

from src.analysis_models import AnalysisInput, RiskFactor, RiskResult
from src.config import (
    RISK_THRESHOLD_CRITICAL,
    RISK_THRESHOLD_HIGH,
    RISK_THRESHOLD_MEDIUM,
    RISK_WEIGHT_ESTIMATE_UNCERTAINTY,
    RISK_WEIGHT_HARVEST_CONCENTRATION,
    RISK_WEIGHT_SUPPLY_DEMAND_GAP,
    RISK_WEIGHT_TRANSPORT_CAPACITY_GAP,
    RISK_WEIGHT_WEATHER_DISRUPTION,
)
from src.enums import (
    EstimateConfidence,
    RecommendedActionCode,
    RiskFactorCode,
    RiskLevel,
    WeatherSourceStatus,
)

_CONFIDENCE_UNCERTAINTY = {
    EstimateConfidence.HIGH: 0.0,
    EstimateConfidence.MEDIUM: 0.5,
    EstimateConfidence.LOW: 1.0,
}
_FACTOR_ORDER = {code: index for index, code in enumerate(RiskFactorCode)}
_ACTION_BY_FACTOR = {
    RiskFactorCode.SUPPLY_DEMAND_GAP: RecommendedActionCode.ADD_COMPATIBLE_DEMAND,
    RiskFactorCode.TRANSPORT_CAPACITY_GAP: (RecommendedActionCode.INCREASE_CRITICAL_DATE_CAPACITY),
    RiskFactorCode.ESTIMATE_UNCERTAINTY: (RecommendedActionCode.VERIFY_LOW_CONFIDENCE_HARVESTS),
    RiskFactorCode.HARVEST_CONCENTRATION: (RecommendedActionCode.REVIEW_CLUSTERED_HARVEST_DATES),
}


def calculate_risk(analysis: AnalysisInput) -> RiskResult:
    """Apply the locked deterministic five-factor risk formula."""
    started = perf_counter()
    total_supply = analysis.total_supply_kg
    if total_supply <= 0:
        return RiskResult(
            has_data=False,
            total_supply_kg=0,
            compatible_demand_kg=analysis.compatible_demand_kg,
            factors=(),
            top_factors=(),
            recommended_actions=(),
            weather_status=analysis.weather.status,
            warnings=("NO_HARVEST_DATA",),
            runtime_ms=(perf_counter() - started) * 1000,
        )

    daily_supply = {item.date: item.quantity_kg for item in analysis.daily_supply}
    daily_demand = {item.date: item.quantity_kg for item in analysis.daily_compatible_demand}
    daily_capacity = {item.date: item.quantity_kg for item in analysis.daily_capacity}
    gap_ratio = _clamp(
        max(0.0, total_supply - analysis.compatible_demand_kg) / max(total_supply, 1.0)
    )
    concentration_ratio = _clamp(max(daily_supply.values(), default=0.0) / total_supply)
    capacity_gap_ratio = _clamp(
        sum(
            max(0.0, daily_supply.get(current, 0.0) - daily_capacity.get(current, 0.0))
            for current in daily_supply
        )
        / total_supply
    )
    weather_score = _clamp(
        sum(score for _, score in analysis.weather.daily_scores)
        / max(len(analysis.weather.daily_scores), 1)
    )
    uncertainty_score = _clamp(
        sum(
            harvest.quantity_kg * _CONFIDENCE_UNCERTAINTY[harvest.confidence]
            for harvest in analysis.harvests
        )
        / total_supply
    )
    factors = (
        _factor(
            RiskFactorCode.SUPPLY_DEMAND_GAP,
            gap_ratio,
            RISK_WEIGHT_SUPPLY_DEMAND_GAP,
        ),
        _factor(
            RiskFactorCode.HARVEST_CONCENTRATION,
            concentration_ratio,
            RISK_WEIGHT_HARVEST_CONCENTRATION,
        ),
        _factor(
            RiskFactorCode.TRANSPORT_CAPACITY_GAP,
            capacity_gap_ratio,
            RISK_WEIGHT_TRANSPORT_CAPACITY_GAP,
        ),
        _factor(
            RiskFactorCode.WEATHER_DISRUPTION,
            weather_score,
            RISK_WEIGHT_WEATHER_DISRUPTION,
        ),
        _factor(
            RiskFactorCode.ESTIMATE_UNCERTAINTY,
            uncertainty_score,
            RISK_WEIGHT_ESTIMATE_UNCERTAINTY,
        ),
    )
    ordered = tuple(
        sorted(
            factors,
            key=lambda item: (-item.weighted_points, _FACTOR_ORDER[item.code]),
        )
    )
    score = _clamp(sum(item.weighted_points for item in ordered), 0, 100)
    top_factors = tuple(item.code for item in ordered if item.weighted_points > 0)[:3]
    actions = tuple(_ACTION_BY_FACTOR[code] for code in top_factors if code in _ACTION_BY_FACTOR)
    warnings = []
    if analysis.weather.status is WeatherSourceStatus.UNAVAILABLE:
        warnings.append("WEATHER_UNAVAILABLE")
    if not analysis.demands:
        warnings.append("NO_OPEN_DEMAND")
    if any(item.missing for item in analysis.daily_capacity):
        warnings.append("MISSING_CAPACITY")
    critical_date = max(
        daily_supply,
        key=lambda current: (
            daily_supply[current]
            - min(daily_demand.get(current, 0.0), daily_capacity.get(current, 0.0)),
            -current.toordinal(),
        ),
    )
    return RiskResult(
        has_data=True,
        score=score,
        level=_risk_level(score),
        total_supply_kg=total_supply,
        compatible_demand_kg=analysis.compatible_demand_kg,
        critical_date=critical_date,
        factors=ordered,
        top_factors=top_factors,
        recommended_actions=actions,
        weather_status=analysis.weather.status,
        warnings=tuple(warnings),
        runtime_ms=(perf_counter() - started) * 1000,
    )


def _factor(code: RiskFactorCode, raw_value: float, weight: float) -> RiskFactor:
    value = _clamp(raw_value)
    return RiskFactor(
        code=code,
        raw_value=value,
        weight=weight,
        weighted_points=value * weight,
    )


def _risk_level(score: float) -> RiskLevel:
    if score >= RISK_THRESHOLD_CRITICAL:
        return RiskLevel.CRITICAL
    if score >= RISK_THRESHOLD_HIGH:
        return RiskLevel.HIGH
    if score >= RISK_THRESHOLD_MEDIUM:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return min(upper, max(lower, value))


__all__ = ["calculate_risk"]
