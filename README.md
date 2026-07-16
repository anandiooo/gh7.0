# MimpiTani

Early-warning and decision-support system prototype for chili farmer cooperatives.

## Requirements

- Python 3.12+
- Windows environment (recommended for development)

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

The application creates `data/mimpitani.db` only after the operator explicitly selects
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

## Project Status

**Phase 1**: Canonical Pydantic contracts, SQLite schema, repositories, deterministic Demo
and Empty workspace initialization, and local reset behavior.

*Note: As this is a hackathon prototype, all operational data is simulated. Weather data integration via BMKG is planned for a future implementation phase.*
