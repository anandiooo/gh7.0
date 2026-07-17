import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from pydantic import ValidationError as PydanticValidationError

from src.config import APP_TIMEZONE
from src.db.connection import DatabasePath, connection_context, resolve_database_path, transaction
from src.db.repositories import (
    BuyerRepository,
    CapacityRepository,
    CooperativeRepository,
    DemandRepository,
    FarmerRepository,
    HarvestRepository,
    WorkspaceRepository,
)
from src.db.schema import initialize_schema
from src.enums import BatchStatus, DemandStatus, WorkspaceMode
from src.errors import TetaniError, SystemError, ValidationError, WorkspaceNotInitializedError
from src.models import CooperativeProfile
from src.services.data_version_service import compute_data_version
from src.services.seed_service import SeedCounts, SeedService


@dataclass(frozen=True)
class WorkspaceSummary:
    profile: CooperativeProfile
    active_farmers: int
    planned_harvest_batches: int
    active_buyers: int
    open_demands: int
    capacity_days: int
    data_version: str

    def session_metadata(self) -> dict[str, str]:
        """Return transient metadata suitable for Streamlit session state."""
        return {
            "workspace_mode": self.profile.workspace_mode.value,
            "cooperative_id": self.profile.id,
            "cooperative_name": self.profile.name,
            "commodity_code": self.profile.commodity_code,
            "pilot_region": self.profile.pilot_region,
            "data_version": self.data_version,
        }


def initialize_workspace(
    mode: WorkspaceMode,
    database_path: DatabasePath | None = None,
    *,
    reference_date: date | None = None,
) -> WorkspaceSummary:
    """Explicitly initialize a Demo or Empty workspace and return its summary."""
    return reset_workspace(mode, database_path, reference_date=reference_date)


def reset_workspace(
    mode: WorkspaceMode,
    database_path: DatabasePath | None = None,
    *,
    reference_date: date | None = None,
) -> WorkspaceSummary:
    """Atomically clear and deterministically recreate the selected workspace."""
    selected_date = reference_date or datetime.now(APP_TIMEZONE).date()
    initialize_schema(database_path)
    try:
        with (
            connection_context(database_path) as connection,
            transaction(connection, immediate=True),
        ):
            WorkspaceRepository(connection=connection).clear_operational_data()
            seed_service = SeedService(connection)
            if mode is WorkspaceMode.DEMO:
                seed_service.seed_demo(selected_date)
            else:
                seed_service.seed_empty(selected_date)
    except TetaniError:
        raise
    except PydanticValidationError as exc:
        raise ValidationError("Workspace seed validation failed") from exc
    except (sqlite3.Error, OSError) as exc:
        raise SystemError("Workspace initialization failed") from exc
    except Exception as exc:
        raise SystemError("Workspace initialization failed unexpectedly") from exc
    return get_workspace_summary(database_path)


def get_workspace_summary(database_path: DatabasePath | None = None) -> WorkspaceSummary:
    """Read workspace identity, operational counts, and canonical data version."""
    path = resolve_database_path(database_path)
    if not Path(path).is_file():
        raise WorkspaceNotInitializedError("The workspace database does not exist")
    profile = CooperativeRepository(path).get_profile()
    if profile is None:
        raise WorkspaceNotInitializedError("The workspace profile does not exist")
    return WorkspaceSummary(
        profile=profile,
        active_farmers=FarmerRepository(path).count(active=True),
        planned_harvest_batches=HarvestRepository(path).count(status=BatchStatus.PLANNED),
        active_buyers=BuyerRepository(path).count(active=True),
        open_demands=DemandRepository(path).count(status=DemandStatus.OPEN),
        capacity_days=CapacityRepository(path).count(),
        data_version=compute_data_version(path),
    )


def read_workspace_counts(database_path: DatabasePath | None = None) -> SeedCounts:
    """Read exact table counts without placing canonical data in session state."""
    with connection_context(database_path) as connection:
        return SeedService(connection).read_counts()


__all__ = [
    "WorkspaceSummary",
    "get_workspace_summary",
    "initialize_workspace",
    "read_workspace_counts",
    "reset_workspace",
]
