CREATE TABLE IF NOT EXISTS schema_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
;

CREATE TABLE IF NOT EXISTS cooperative_profiles (
    id TEXT PRIMARY KEY,
    singleton_key INTEGER NOT NULL DEFAULT 1 UNIQUE CHECK (singleton_key = 1),
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    pilot_region TEXT NOT NULL CHECK (length(trim(pilot_region)) > 0),
    commodity_code TEXT NOT NULL CHECK (commodity_code = 'CABAI_RAWIT_MERAH'),
    adm4_code TEXT NOT NULL CHECK (length(trim(adm4_code)) > 0),
    workspace_mode TEXT NOT NULL CHECK (workspace_mode IN ('DEMO', 'EMPTY')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
;

CREATE TABLE IF NOT EXISTS farmers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(trim(name)) BETWEEN 2 AND 100),
    village_name TEXT NOT NULL CHECK (length(trim(village_name)) > 0),
    subdistrict_name TEXT NOT NULL CHECK (length(trim(subdistrict_name)) > 0),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
;

CREATE TABLE IF NOT EXISTS harvest_batches (
    id TEXT PRIMARY KEY,
    farmer_id TEXT NOT NULL REFERENCES farmers(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    commodity_code TEXT NOT NULL CHECK (commodity_code = 'CABAI_RAWIT_MERAH'),
    estimated_harvest_date TEXT NOT NULL,
    estimated_quantity_kg REAL NOT NULL
        CHECK (estimated_quantity_kg > 0 AND estimated_quantity_kg <= 100000),
    grade TEXT NOT NULL CHECK (grade IN ('A', 'B', 'C')),
    confidence TEXT NOT NULL CHECK (confidence IN ('LOW', 'MEDIUM', 'HIGH')),
    maturity_note TEXT,
    status TEXT NOT NULL CHECK (status IN ('PLANNED', 'CANCELLED')),
    source TEXT NOT NULL CHECK (source IN ('MANUAL', 'CSV', 'SEED')),
    import_fingerprint TEXT UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
;

CREATE INDEX IF NOT EXISTS idx_harvest_farmer ON harvest_batches(farmer_id)
;
CREATE INDEX IF NOT EXISTS idx_harvest_status_date
    ON harvest_batches(status, estimated_harvest_date)
;

CREATE TABLE IF NOT EXISTS buyers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    channel TEXT NOT NULL CHECK (
        channel IN ('TRADITIONAL_MARKET', 'RETAILER', 'RESTAURANT', 'PROCESSOR')
    ),
    location TEXT NOT NULL CHECK (length(trim(location)) > 0),
    distance_km REAL NOT NULL CHECK (distance_km >= 0 AND distance_km <= 1000),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
;

CREATE INDEX IF NOT EXISTS idx_buyers_active ON buyers(active)
;

CREATE TABLE IF NOT EXISTS buyer_demands (
    id TEXT PRIMARY KEY,
    buyer_id TEXT NOT NULL REFERENCES buyers(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    commodity_code TEXT NOT NULL CHECK (commodity_code = 'CABAI_RAWIT_MERAH'),
    quantity_kg REAL NOT NULL CHECK (quantity_kg > 0 AND quantity_kg <= 100000),
    accepted_grades_json TEXT NOT NULL CHECK (
        json_valid(accepted_grades_json) AND json_array_length(accepted_grades_json) > 0
    ),
    deadline TEXT NOT NULL,
    priority INTEGER NOT NULL CHECK (priority IN (1, 2, 3)),
    status TEXT NOT NULL CHECK (status IN ('OPEN', 'CLOSED')),
    source TEXT NOT NULL CHECK (source IN ('MANUAL', 'SEED')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
;

CREATE INDEX IF NOT EXISTS idx_demands_buyer ON buyer_demands(buyer_id)
;
CREATE INDEX IF NOT EXISTS idx_demands_status_deadline ON buyer_demands(status, deadline)
;

CREATE TABLE IF NOT EXISTS distribution_capacities (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL UNIQUE,
    available_capacity_kg REAL NOT NULL
        CHECK (available_capacity_kg >= 0 AND available_capacity_kg <= 1000000),
    source TEXT NOT NULL CHECK (source IN ('MANUAL', 'SEED')),
    note TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
;

CREATE TABLE IF NOT EXISTS weather_snapshots (
    id TEXT PRIMARY KEY,
    adm4_code TEXT NOT NULL CHECK (length(trim(adm4_code)) > 0),
    fetched_at TEXT NOT NULL,
    analysis_date TEXT,
    valid_from TEXT,
    valid_until TEXT,
    source_status TEXT NOT NULL CHECK (source_status IN ('LIVE', 'CACHE')),
    normalized_json TEXT NOT NULL CHECK (json_valid(normalized_json)),
    raw_payload_json TEXT NOT NULL CHECK (json_valid(raw_payload_json))
)
;

CREATE INDEX IF NOT EXISTS idx_weather_adm4_fetched
    ON weather_snapshots(adm4_code, fetched_at DESC)
;

CREATE TABLE IF NOT EXISTS analysis_runs (
    id TEXT PRIMARY KEY,
    parent_run_id TEXT REFERENCES analysis_runs(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    scenario_name TEXT,
    run_type TEXT NOT NULL CHECK (run_type IN ('BASE', 'SCENARIO')),
    created_at TEXT NOT NULL,
    horizon_start TEXT NOT NULL,
    horizon_end TEXT NOT NULL CHECK (horizon_end >= horizon_start),
    data_version TEXT NOT NULL CHECK (length(trim(data_version)) > 0),
    risk_score REAL CHECK (risk_score IS NULL OR risk_score BETWEEN 0 AND 100),
    risk_level TEXT CHECK (
        risk_level IS NULL OR risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
    ),
    total_supply_kg REAL CHECK (total_supply_kg IS NULL OR total_supply_kg >= 0),
    compatible_demand_kg REAL CHECK (
        compatible_demand_kg IS NULL OR compatible_demand_kg >= 0
    ),
    allocated_kg REAL CHECK (allocated_kg IS NULL OR allocated_kg >= 0),
    unallocated_kg REAL CHECK (unallocated_kg IS NULL OR unallocated_kg >= 0),
    unallocated_supply_rate REAL CHECK (
        unallocated_supply_rate IS NULL OR unallocated_supply_rate BETWEEN 0 AND 1
    ),
    demand_fulfillment_rate REAL CHECK (
        demand_fulfillment_rate IS NULL OR demand_fulfillment_rate BETWEEN 0 AND 1
    ),
    solver_status TEXT CHECK (
        solver_status IS NULL OR solver_status IN (
            'OPTIMAL', 'FEASIBLE_FALLBACK', 'NO_DATA', 'FAILED'
        )
    ),
    weather_status TEXT CHECK (
        weather_status IS NULL OR weather_status IN ('LIVE', 'CACHE', 'UNAVAILABLE')
    ),
    input_snapshot_json TEXT NOT NULL CHECK (json_valid(input_snapshot_json)),
    override_snapshot_json TEXT CHECK (
        override_snapshot_json IS NULL OR json_valid(override_snapshot_json)
    ),
    risk_snapshot_json TEXT CHECK (
        risk_snapshot_json IS NULL OR json_valid(risk_snapshot_json)
    ),
    result_snapshot_json TEXT CHECK (
        result_snapshot_json IS NULL OR json_valid(result_snapshot_json)
    ),
    error_message TEXT,
    CHECK (parent_run_id IS NULL OR parent_run_id <> id)
)
;

CREATE INDEX IF NOT EXISTS idx_analysis_created ON analysis_runs(created_at DESC)
;
CREATE INDEX IF NOT EXISTS idx_analysis_parent ON analysis_runs(parent_run_id)
;

CREATE TABLE IF NOT EXISTS allocations (
    id TEXT PRIMARY KEY,
    analysis_run_id TEXT NOT NULL
        REFERENCES analysis_runs(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    harvest_batch_id TEXT NOT NULL
        REFERENCES harvest_batches(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    buyer_demand_id TEXT NOT NULL
        REFERENCES buyer_demands(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    delivery_date TEXT NOT NULL,
    quantity_kg REAL NOT NULL CHECK (quantity_kg > 0 AND quantity_kg <= 100000),
    distance_km_snapshot REAL NOT NULL
        CHECK (distance_km_snapshot >= 0 AND distance_km_snapshot <= 1000),
    reason_json TEXT NOT NULL CHECK (json_valid(reason_json)),
    created_at TEXT NOT NULL
)
;

CREATE INDEX IF NOT EXISTS idx_allocations_run ON allocations(analysis_run_id)
;
CREATE INDEX IF NOT EXISTS idx_allocations_batch ON allocations(harvest_batch_id)
;
CREATE INDEX IF NOT EXISTS idx_allocations_demand ON allocations(buyer_demand_id)
;
