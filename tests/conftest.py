from datetime import date, datetime
from pathlib import Path

import pytest

from src.config import APP_TIMEZONE
from src.db.schema import initialize_schema


@pytest.fixture
def reference_date() -> date:
    return date(2026, 7, 16)


@pytest.fixture
def aware_timestamp(reference_date: date) -> datetime:
    return datetime(2026, 7, 16, 8, 0, tzinfo=APP_TIMEZONE)


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    path = tmp_path / "tetani-test.db"
    initialize_schema(path)
    return path
