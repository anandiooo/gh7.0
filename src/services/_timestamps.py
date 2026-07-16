from datetime import datetime

from src.config import APP_TIMEZONE


def mutation_timestamp(created_at: datetime) -> datetime:
    """Return a valid mutation time even for deterministic records seeded later today."""
    return max(datetime.now(APP_TIMEZONE), created_at)


__all__ = ["mutation_timestamp"]
