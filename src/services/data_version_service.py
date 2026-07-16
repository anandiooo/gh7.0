import hashlib
import json
import sqlite3
from collections.abc import Sequence

from pydantic import BaseModel

from src.db.connection import DatabasePath
from src.db.repositories import (
    BuyerRepository,
    CapacityRepository,
    CooperativeRepository,
    DemandRepository,
    FarmerRepository,
    HarvestRepository,
    WeatherRepository,
)


def compute_data_version(
    database_path: DatabasePath | None = None,
    *,
    connection: sqlite3.Connection | None = None,
) -> str:
    """Hash an order-independent canonical snapshot of operational source data."""
    cooperative_repository = CooperativeRepository(database_path, connection=connection)
    profile = cooperative_repository.get_profile()
    weather = (
        WeatherRepository(database_path, connection=connection).list_compatible(profile.adm4_code)
        if profile
        else []
    )
    payload = {
        "cooperative": _dump_one(profile),
        "farmers": _dump_many(FarmerRepository(database_path, connection=connection).list()),
        "harvest_batches": _dump_many(
            HarvestRepository(database_path, connection=connection).list()
        ),
        "buyers": _dump_many(BuyerRepository(database_path, connection=connection).list()),
        "buyer_demands": _dump_many(DemandRepository(database_path, connection=connection).list()),
        "distribution_capacities": _dump_many(
            CapacityRepository(database_path, connection=connection).list_all()
        ),
        "weather_snapshots": _dump_many(weather),
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _dump_one(model: BaseModel | None) -> dict[str, object] | None:
    if model is None:
        return None
    return model.model_dump(mode="json")


def _dump_many(models: Sequence[BaseModel]) -> list[dict[str, object]]:
    dumped = [model.model_dump(mode="json") for model in models]
    return sorted(dumped, key=lambda item: str(item["id"]))


__all__ = ["compute_data_version"]
