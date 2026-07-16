from enum import StrEnum


class WorkspaceMode(StrEnum):
    DEMO = "DEMO"
    EMPTY = "EMPTY"


class QualityGrade(StrEnum):
    A = "A"
    B = "B"
    C = "C"


class EstimateConfidence(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class BatchStatus(StrEnum):
    PLANNED = "PLANNED"
    CANCELLED = "CANCELLED"


class SourceType(StrEnum):
    MANUAL = "MANUAL"
    CSV = "CSV"
    SEED = "SEED"


class ChannelType(StrEnum):
    TRADITIONAL_MARKET = "TRADITIONAL_MARKET"
    RETAILER = "RETAILER"
    RESTAURANT = "RESTAURANT"
    PROCESSOR = "PROCESSOR"


class DemandStatus(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class WeatherSourceStatus(StrEnum):
    LIVE = "LIVE"
    CACHE = "CACHE"
    UNAVAILABLE = "UNAVAILABLE"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SolverStatus(StrEnum):
    OPTIMAL = "OPTIMAL"
    FEASIBLE_FALLBACK = "FEASIBLE_FALLBACK"
    NO_DATA = "NO_DATA"
    FAILED = "FAILED"
