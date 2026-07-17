# tetani

tetani is a bilingual early-warning and decision-support prototype for a chili farmer
cooperative. It combines seven-day harvest plans, compatible buyer demand, distribution
capacity, deterministic surplus risk, advisory allocation, and temporary scenarios.

## Requirements

- Python 3.12+
- Git

## Setup

1. Create and activate a virtual environment:
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   ```

## Running the Application

To start the Streamlit interface:
```cmd
streamlit run app.py
```

The application creates `data/tetani.db` only after the operator explicitly selects
Demo or Empty workspace initialization.

To initialize or deterministically reset the default database in Demo mode without
starting Streamlit:

```cmd
python scripts/initialize_demo.py
```

## Development and Testing

Run the automated test suite:
```cmd
python -m pytest -q
```

Run code linting:
```cmd
python -m ruff check .
```

Run format checking:
```cmd
python -m ruff format --check .
```

## Demo Workflow

1. Select **Muat Data Demo / Load Demo Data**.
2. Review or edit harvest plans, buyers, demand, and daily capacity.
3. Open **Radar Surplus / Surplus Radar** to inspect supply, compatible demand, capacity,
   surplus exposure, the five-factor risk score, and recommended actions.
4. Run **Analysis & Allocation** to persist an immutable base snapshot and advisory plan.
5. Add temporary demand and/or effective capacity on **Analysis & Simulation**.
6. Run the scenario and compare risk, allocation, unallocated supply, and fulfillment.

The deterministic Demo contains 30 farmers, 42 harvest batches, 8 buyers, 16 open demands,
and 7 capacity days. It provides 12,600.0 kg supply, 2,760.0 kg demand, and 4,350.0 kg
capacity.

## Architecture

```text
Streamlit pages
    -> application services
        -> deterministic risk engine / scipy HiGHS optimizer
        -> explicit repositories
            -> SQLite (canonical source of truth)
```

- Pydantic validates domain and analysis contracts.
- Repository modules own parameterized SQL and transactions.
- Services contain CRUD orchestration, risk, allocation, persistence, and scenarios.
- Streamlit session state contains only UI metadata and temporary scenario results.
- Analysis snapshots are immutable and canonical operational changes mark them stale.

## Data Provenance and Safety

- Cooperative, harvest, buyer, demand, and capacity records in Demo mode are simulated.
- Weather is currently reported as **Unavailable** and contributes zero risk points.
- The application does not claim live BMKG data when no verified source is available.
- Allocation and scenario results are advisory simulations, not executed transactions or
  confirmed buyer commitments.
- The seeded core workflow works without internet access.

## Known Limitations

- CSV harvest import is deferred; manual harvest CRUD is complete.
- Live and cached BMKG retrieval are deferred; the safe unavailable-weather path is complete.
- Scenario results are temporary session data. They are not saved because temporary demand
  identifiers must not be inserted into canonical demand tables merely to satisfy allocation
  foreign keys.
- SQLite storage on Streamlit Community Cloud is ephemeral across application restarts.
- This is a single-operator, single-cooperative, single-commodity hackathon prototype.

No authentication, marketplace, pricing, payments, notifications, route optimization, or
automatic execution is included.
