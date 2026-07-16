from datetime import datetime

import pytest

from src.config import APP_TIMEZONE
from src.db.connection import connection_context
from src.enums import WorkspaceMode
from src.errors import SystemError, WorkspaceNotInitializedError
from src.services.data_version_service import compute_data_version
from src.services.seed_service import EXPECTED_DEMO_COUNTS, EXPECTED_EMPTY_COUNTS, SeedService
from src.services.workspace_service import (
    get_workspace_summary,
    initialize_workspace,
    read_workspace_counts,
    reset_workspace,
)


def test_missing_database_is_not_created_by_summary_read(tmp_path) -> None:
    path = tmp_path / "missing" / "workspace.db"
    with pytest.raises(WorkspaceNotInitializedError):
        get_workspace_summary(path)
    assert not path.exists()


def test_empty_workspace_contains_only_profile(database_path, reference_date) -> None:
    summary = initialize_workspace(
        WorkspaceMode.EMPTY, database_path, reference_date=reference_date
    )
    assert summary.profile.workspace_mode is WorkspaceMode.EMPTY
    assert read_workspace_counts(database_path) == EXPECTED_EMPTY_COUNTS
    assert summary.active_farmers == 0
    assert summary.planned_harvest_batches == 0
    assert summary.active_buyers == 0
    assert summary.open_demands == 0
    assert summary.capacity_days == 0


def test_demo_and_empty_resets_work_in_both_directions(database_path, reference_date) -> None:
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    assert read_workspace_counts(database_path) == EXPECTED_DEMO_COUNTS
    reset_workspace(WorkspaceMode.EMPTY, database_path, reference_date=reference_date)
    assert read_workspace_counts(database_path) == EXPECTED_EMPTY_COUNTS
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    assert read_workspace_counts(database_path) == EXPECTED_DEMO_COUNTS


def test_demo_to_demo_reset_is_deterministic(database_path, reference_date) -> None:
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    first_version = compute_data_version(database_path)
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    assert compute_data_version(database_path) == first_version
    assert read_workspace_counts(database_path) == EXPECTED_DEMO_COUNTS


def test_failed_reset_rolls_back_all_operational_data(
    database_path, reference_date, monkeypatch
) -> None:
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    original_version = compute_data_version(database_path)
    original_seed_empty = SeedService.seed_empty

    def fail_after_seed(self, selected_date):
        original_seed_empty(self, selected_date)
        raise RuntimeError("injected reset failure")

    monkeypatch.setattr(SeedService, "seed_empty", fail_after_seed)
    with pytest.raises(SystemError):
        reset_workspace(WorkspaceMode.EMPTY, database_path, reference_date=reference_date)
    assert read_workspace_counts(database_path) == EXPECTED_DEMO_COUNTS
    assert compute_data_version(database_path) == original_version


def test_reset_preserves_schema_metadata(database_path, reference_date) -> None:
    with connection_context(database_path) as connection:
        before = connection.execute(
            "SELECT value FROM schema_metadata WHERE key = ?", ("schema_version",)
        ).fetchone()["value"]
    reset_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    with connection_context(database_path) as connection:
        after = connection.execute(
            "SELECT value FROM schema_metadata WHERE key = ?", ("schema_version",)
        ).fetchone()["value"]
    assert after == before


def test_runtime_reference_date_defaults_to_jakarta_today(tmp_path) -> None:
    path = tmp_path / "runtime.db"
    summary = initialize_workspace(WorkspaceMode.EMPTY, path)
    assert summary.profile.created_at.date() == datetime.now(APP_TIMEZONE).date()
