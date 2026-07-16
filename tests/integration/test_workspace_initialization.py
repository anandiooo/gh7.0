from src.enums import WorkspaceMode
from src.services.data_version_service import compute_data_version
from src.services.seed_service import EXPECTED_DEMO_COUNTS, EXPECTED_EMPTY_COUNTS
from src.services.workspace_service import initialize_workspace, read_workspace_counts


def test_demo_workspace_initializes_real_temporary_database(database_path, reference_date) -> None:
    summary = initialize_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    assert summary.profile.workspace_mode is WorkspaceMode.DEMO
    assert summary.active_farmers == 30
    assert summary.planned_harvest_batches == 42
    assert summary.active_buyers == 8
    assert summary.open_demands == 16
    assert summary.capacity_days == 7
    assert read_workspace_counts(database_path) == EXPECTED_DEMO_COUNTS


def test_empty_workspace_initializes_real_temporary_database(database_path, reference_date) -> None:
    summary = initialize_workspace(
        WorkspaceMode.EMPTY, database_path, reference_date=reference_date
    )
    assert summary.profile.workspace_mode is WorkspaceMode.EMPTY
    assert read_workspace_counts(database_path) == EXPECTED_EMPTY_COUNTS


def test_repeated_demo_initialization_does_not_duplicate(database_path, reference_date) -> None:
    initialize_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    version = compute_data_version(database_path)
    initialize_workspace(WorkspaceMode.DEMO, database_path, reference_date=reference_date)
    assert read_workspace_counts(database_path) == EXPECTED_DEMO_COUNTS
    assert compute_data_version(database_path) == version
