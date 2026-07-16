# Universal Coding Agent Rules — MimpiTani

Read this before touching any code. Refer to `SPEC.md` for what to build; this file defines how to build it. This file is named `CLAUDE.md` for compatibility, but its rules apply equally to Claude Code, Codex, Cursor, Windsurf, Cline, Aider, and other coding agents.

## Code-Only Responses

When generating or modifying code, output only the requested code or patch. Do not include explanations, summaries, implementation commentary, or conversational text. Do not add comments or docstrings unless they are explicitly required by the user.

## Stack — Do Not Deviate Without Asking

- Language: Python 3.12.
- Frontend: Streamlit multipage application.
- Backend: same-process modular Python service layer.
- Database: SQLite through Python standard-library `sqlite3`.
- Validation: Pydantic.
- Data processing: pandas and NumPy.
- Optimization: `scipy.optimize.linprog` with HiGHS.
- Charts: Plotly.
- HTTP client: httpx.
- Testing: pytest; Streamlit built-in testing utilities where useful.
- Formatting and linting: Ruff.
- Auth: none.
- Deployment: Streamlit Community Cloud.
- Local run target: `streamlit run app.py`.
- Dependency declaration: pinned `requirements.txt`.

Do not introduce FastAPI, Flask, Django, React, Next.js, Supabase, PostgreSQL, Firebase, SQLAlchemy, Alembic, an LLM API, a vector database, or a separate microservice unless the user explicitly approves a revised architecture.

---

## Product Boundaries

MimpiTani is a bilingual, single-operator, one-cooperative, one-commodity decision-support prototype.

The product must remain centered on:

1. Recording upcoming harvests.
2. Recording compatible buyer demand and daily transport capacity.
3. Detecting and explaining short-horizon surplus risk.
4. Generating and comparing feasible allocation scenarios.

There is no price module in v1.

Do not add functionality because it appears useful, common, modern, or easy. If it is not in `SPEC.md §3 In scope`, propose it separately and wait for approval.

The system is advisory. Never present recommendations as executed transactions, guaranteed outcomes, or validated field impact.

---

## Conventions

### Required folder structure

Use this structure unless a concrete technical issue requires a proposed change:

```text
mimpitani/
├── app.py
├── SPEC.md
├── CLAUDE.md
├── README.md
├── requirements.txt
├── pyproject.toml
├── .gitignore
│
├── pages/
│   ├── 1_surplus_radar.py
│   ├── 2_harvest_plans.py
│   ├── 3_buyers_and_capacity.py
│   └── 4_analysis_and_simulation.py
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── enums.py
│   ├── models.py
│   ├── errors.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── schema.sql
│   │   ├── initialize.py
│   │   └── repositories.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── workspace_service.py
│   │   ├── harvest_service.py
│   │   ├── buyer_service.py
│   │   ├── radar_service.py
│   │   ├── risk_engine.py
│   │   ├── allocation_optimizer.py
│   │   ├── greedy_fallback.py
│   │   ├── scenario_service.py
│   │   └── analysis_service.py
│   │
│   ├── integrations/
│   │   ├── __init__.py
│   │   └── bmkg_weather.py
│   │
│   ├── i18n/
│   │   ├── __init__.py
│   │   ├── translator.py
│   │   ├── id.json
│   │   └── en.json
│   │
│   └── ui/
│       ├── __init__.py
│       ├── components.py
│       ├── formatting.py
│       ├── messages.py
│       └── theme.py
│
├── data/
│   ├── seed/
│   │   ├── cooperative.csv
│   │   ├── farmers.csv
│   │   ├── harvest_batches.csv
│   │   ├── buyers.csv
│   │   ├── buyer_demands.csv
│   │   └── distribution_capacity.csv
│   ├── templates/
│   │   └── harvest_import_template.csv
│   └── cache/
│       └── .gitkeep
│
├── scripts/
│   ├── reset_demo.py
│   └── smoke_test.py
│
└── tests/
    ├── conftest.py
    ├── fixtures/
    ├── unit/
    │   ├── test_models.py
    │   ├── test_translations.py
    │   ├── test_risk_engine.py
    │   ├── test_optimizer.py
    │   ├── test_greedy_fallback.py
    │   └── test_weather_adapter.py
    ├── integration/
    │   ├── test_repositories.py
    │   ├── test_seed_reset.py
    │   └── test_analysis_flow.py
    └── ui/
        └── test_pages_smoke.py
```

Do not create extra top-level directories without explaining why.

### Dependency direction

Allowed dependency direction:

```text
pages/ui
   ↓
services
   ↓
models + repositories + integrations + i18n
   ↓
sqlite3 / httpx / scipy
```

Rules:

- `pages/` may import `src.ui`, `src.services`, `src.models`, and `src.config`.
- `src.services` must not import Streamlit.
- `src.db` must not import Streamlit.
- `src.integrations` must not import Streamlit.
- `src.models` must not import database or UI modules.
- UI modules must not execute SQL.
- Only repository modules execute application SQL.
- Only `bmkg_weather.py` parses the upstream BMKG payload.
- Risk and optimization logic must remain callable from tests without starting Streamlit.

### Naming

- Python files and modules: `snake_case`.
- Functions and variables: `snake_case`.
- Classes and Pydantic models: `PascalCase`.
- Constants: `UPPER_SNAKE_CASE`.
- Database tables and columns: `snake_case`.
- Enum members: `UPPER_SNAKE_CASE`.
- User-facing labels: Bahasa Indonesia.
- Internal domain and code identifiers: English.
- Test names: `test_<behavior>_<expected_result>`.

Use precise domain names. Prefer `estimated_quantity_kg` over `amount`, `BuyerDemand` over `Request`, and `unallocated_supply_rate` over `percentage`.

### Bilingual UI and translation rules

- Default language is `id`.
- Language switcher is `ID | EN`.
- Language preference is stored only for the active session.
- Product name is `MimpiTani` in Indonesian and `MimpiTani (Farmers' Dream)` in English.
- All user-facing text must use `t("translation.key")`.
- `src/i18n/id.json` and `src/i18n/en.json` must contain identical keys.
- A missing translation key is a test failure; do not silently display the raw key.
- Names, locations, IDs, and user-entered content are not translated.
- Developer logs and code identifiers remain English.

### Locked visual system

```text
PRIMARY_DARK_GREEN = #145319
SECONDARY_LIGHT_GREEN = #388E3C
ACCENT_WARNING_ORANGE = #D97706
APP_BACKGROUND = #F1F5F0
SURFACE_BACKGROUND = #FFFFFF
PRIMARY_TEXT = #1A2E1A
```

- Do not replace this palette without approval.
- Risk information must include text and may not rely on color alone.
- Additional semantic error or neutral colors may be added minimally and must maintain readable contrast.
- Do not add decorative animations, excessive gradients, or a marketing-style landing page.

### Type and validation rules

- Add type hints to every public function.
- Validate data at system boundaries with Pydantic.
- Do not pass unstructured dictionaries through several layers when a Pydantic model exists.
- Use `Decimal` only where exact currency arithmetic is required. Kilogram optimization may use float, with explicit tolerance handling.
- Never use `Any` merely to bypass type decisions.
- Reject unknown enum values.
- Keep date and datetime types as actual Python types internally, not strings.

### Database rules

- Use `sqlite3.Row`.
- Use parameterized SQL for every query.
- Use explicit transactions for writes.
- Enable foreign keys on every connection.
- Centralize connection creation.
- Keep schema in `src/db/schema.sql`.
- Make initialization idempotent.
- Do not implement a general migration framework for v1.
- Never edit or commit the runtime `.db` file.
- Repository methods return domain models or explicit result objects, not raw tuples.
- Do not hide write failures; return or raise a typed application error.

### State management

- SQLite is the canonical state.
- `st.session_state` is for temporary UI state only:
  - selected language and workspace choice;
  - unsaved form state;
  - import preview;
  - current filters;
  - temporary scenario changes;
  - selected base analysis.
- Do not store canonical harvest, buyer, demand, or analysis records only in session state.
- Do not rely on Streamlit cache for mutable domain data.
- Cache only:
  - stable configuration;
  - read-only seed resources;
  - short-lived weather fetches;
  - pure expensive calculations keyed by complete input.
- Invalidate or bypass cached analysis after canonical data changes.

### Style and lint

- Use Ruff for linting and formatting.
- Keep functions focused and generally below 50 lines.
- Keep page files thin; orchestration and rendering only.
- Prefer guard clauses over deeply nested conditionals.
- Avoid clever abstractions that are used only once.
- No wildcard imports.
- No commented-out code.
- No debug `print` in committed code.
- No silent exception swallowing.
- User errors and system errors must be distinguished.
- Logs may contain IDs and technical context but no secrets or personal data.

### Comments and documentation

- Comments explain why, not what the code already states.
- Public service functions need concise docstrings describing inputs, outputs, and failure modes.
- Risk weights, thresholds, optimizer penalties, and tolerances require comments and tests.
- Any intentional simplification must be documented near the implementation and in README limitations.
- Do not label deterministic rules as machine learning.
- Do not label a greedy fallback as optimal.

---

## Workflow

### Plan before code

For anything beyond a trivial one-line change:

1. Restate the relevant requirement and acceptance criteria.
2. Inspect existing code and tests.
3. Propose a small implementation plan.
4. Identify files to add or modify.
5. Identify risks, assumptions, and tests.
6. Wait for approval before writing code.

Do not produce the whole application in one unreviewed pass.

### One independently verifiable task per pass

Implement one small unit such as:

- one Pydantic model group;
- schema initialization;
- one repository;
- one CRUD flow;
- the risk engine;
- optimizer constraints;
- BMKG normalization;
- one screen state.

Do not combine unrelated refactoring, styling, and feature work.

### Before modifying code

- Read `SPEC.md`.
- Read this file.
- Check the current Git diff.
- Identify whether the requested work changes scope, schema, contracts, or dependencies.
- Ask before any change to those four categories unless the user explicitly requested it.

### During implementation

- Write or update tests with the behavior.
- Keep the smallest viable diff.
- Preserve existing accepted behavior.
- Handle relevant edge cases from `SPEC.md §9`.
- Use fixtures instead of live network calls.
- Make calculations deterministic.
- Do not fake command output or test results.

### After each task

Run the relevant commands and report the real result.

Minimum:

```bash
python -m pytest -q <relevant-test-paths>
ruff check <changed-paths>
ruff format --check <changed-paths>
```

For a milestone:

```bash
python -m pytest -q
ruff check .
ruff format --check .
```

For UI work, also run:

```bash
streamlit run app.py
```

Then perform the stated manual smoke test.

A valid report includes:

- files changed;
- tests executed;
- exact pass/fail count;
- lint/format result;
- manual test performed;
- unresolved limitations.

Never say “done,” “working,” or “tests pass” without having run the relevant checks in the current session.

### Ambiguity

When a requirement is ambiguous:

- State the ambiguity.
- State the lowest-scope assumption.
- Explain its consequence.
- Ask for confirmation if it affects data model, user flow, scope, external contract, or architecture.

Do not silently guess.

### Failures

When a command or test fails:

- Report the failure accurately.
- Include the relevant error summary.
- Diagnose before changing unrelated code.
- Do not weaken or delete a valid test to obtain a green result.
- Do not catch broad exceptions merely to hide failure.
- Add fallback behavior only when it is specified in `SPEC.md`.

---

## Domain Implementation Rules

### Risk engine

- Must be deterministic.
- Must implement the formula in `SPEC.md §7`.
- Factor contributions must sum to the score within tolerance.
- Missing weather yields a warning and zero weather contribution.
- Do not extrapolate unavailable weather beyond official forecast coverage.
- Explanations must identify concrete input conditions.
- Keep thresholds in configuration and test every boundary.

### Allocation optimizer

- Use continuous kilogram variables.
- Build constraints explicitly and test them as invariants.
- Never allocate an incompatible grade.
- Never allocate before harvest or after deadline.
- Never exceed batch quantity, buyer demand, or daily capacity.
- Use a strong but finite unallocated-supply penalty.
- Keep objective weights in configuration.
- Record solver status and diagnostics.
- Invoke greedy fallback only on a genuine solver failure, not merely because the optimal result includes unallocated supply.
- Fallback output must respect the same hard constraints.

### Scenario simulation

- Scenario changes are temporary by default.
- Never mutate canonical records while computing a scenario.
- Build scenario input as a copy of base canonical input plus explicit overrides.
- Store immutable snapshots only when the user chooses to save.
- Link saved scenarios to the base run.
- Mark a base run stale after canonical input changes.

### Weather integration

- One adapter owns the BMKG contract.
- Timeout is 3 seconds.
- No repeated network call on every rerun.
- Tests use mocked payloads.
- Normalize only required fields.
- Preserve source timestamp and status.
- Credit BMKG in the UI.
- Live failure falls back to cache.
- Cache failure yields unavailable weather; it must not stop core analysis.
- Never treat cache as live.

### CSV import

- Preview before write.
- Validate every row.
- Report row-level errors.
- Default behavior is atomic import.
- Partial import requires explicit user confirmation.
- Detect duplicates using a stable fingerprint.
- Do not infer invalid enum values.
- Do not silently convert invalid dates or quantities.

### Data provenance

Every screen displaying analysis must make source status explicit:

- simulated operational data;
- manual ;
- live BMKG;
- cached BMKG;
- unavailable weather;
- simulated potential impact.

Never remove these labels for visual cleanliness.

---

## UI Rules

- The first initialization must offer `Load Demo Data` and `Start Empty`.
- Simulated data must never load silently.
- Show a global prototype banner.
- Show live, cache, stale, or unavailable weather status accurately.
- Use the locked visual tokens from this file.
- All visible strings use translation keys.

- Support complete Bahasa Indonesia and English interfaces; default to Bahasa Indonesia.
- Use concise operational language.
- The primary screen is a dashboard, not a marketing landing page.
- Do not add decorative animations.
- Do not use color as the only risk indicator.
- Always include empty, loading, partial, success, and error states where specified.
- Preserve typed data after recoverable errors.
- Show the action the operator can take next.
- Technical details belong in an expander.
- Avoid horizontal scrolling at 1366×768 for primary content.
- Do not render more than the necessary charts.
- Any simulated metric must include the word `Estimasi` or `Simulasi`.
- Any stale analysis must be visibly marked.

---

## Testing Rules

### Unit tests

Required for:

- Pydantic validation.
- Translation key parity and language switching.
- Demo and empty workspace initialization.
- Risk-factor normalization.
- Risk-score boundaries.
- Critical-date selection.
- Optimizer matrix construction.
- Optimizer hard constraints.
- Greedy fallback.
- CSV duplicate detection.
- BMKG normalization.
- Weather cache fallback.
- Metric calculations.

### Integration tests

Required for:

- Schema initialization.
- Seed reset.
- Repository CRUD.
- Atomic CSV import.
- Full analysis flow using temporary SQLite.
- Analysis snapshot persistence.
- Scenario isolation from canonical data.

### UI smoke tests

At minimum verify:

- welcome state renders;
- both workspace initialization paths work;
- each page imports;
- language switcher exists and both languages render;
- empty states render;
- seeded states render;
- primary action controls exist;
- a service error becomes a user-facing message rather than an uncaught exception.

### Network testing

- Never call live BMKG in automated tests.
- Use recorded minimal fixtures representing:
  - valid response;
  - missing optional fields;
  - malformed response;
  - timeout;
  - HTTP failure.

### Numerical tolerance

- Define one shared kilogram tolerance.
- Values below 0.001 kg may be normalized to zero.
- Test sums with tolerance rather than exact binary-float equality.
- Display one decimal kg but retain internal precision.

---

## Do Not Touch

Without explicit user approval, do not modify:

- `SPEC.md`.
- `CLAUDE.md`.
- `.env`.
- `.streamlit/secrets.toml`.
- GitHub Actions or deployment settings after they are known to work.
- Generated runtime SQLite databases.
- Files under `data/cache/`, except through the weather-cache service at runtime.
- Submission video, pitch deck, or other files under a future `submission/` directory.
- Historical `AnalysisRun` records after creation.
- Existing seed assumptions after Phase 1 is accepted, unless a requested task specifically changes the demo scenario.

Do not delete or rewrite tests simply because they fail.

---

## Definition of Done

A feature is done only when all of the following are true:

1. It matches the relevant acceptance criteria in `SPEC.md §10`.
2. It remains within `SPEC.md §3`.
3. Relevant edge cases from `SPEC.md §9` are handled.
4. Tests were added or updated.
5. Tests were actually run in the current session and pass.
6. Ruff lint and formatting checks were actually run and pass.
7. Relevant manual UI behavior was tested.
8. Error and empty states are implemented.
9. Data provenance remains visible.
10. No secret, generated database, cache payload, or unrelated file is added.
11. Documentation is updated when behavior or commands changed.
12. The agent reports any remaining limitation honestly.

A partial implementation must be reported as partial.

---

## Prohibited Actions

Do not:

- Add a new dependency without flagging it first and explaining why the existing stack is insufficient.
- Refactor unrelated code while implementing a feature.
- Expand scope beyond `SPEC.md §3`.
- Introduce authentication “for completeness.”
- Add a marketplace, payment flow, chat, notification system, computer vision, IoT, or route optimizer.
- Train a model on synthetic labels and market it as validated AI.
- Add an LLM where deterministic logic is specified.
- Replace SQLite with a cloud database.
- Split the monolith into frontend and backend services.
- Query BMKG directly from page files.
- Put SQL in Streamlit pages.
- Put Streamlit calls in services or repositories.
- Use raw string interpolation in SQL.
- Commit secrets, runtime databases, caches, or user data.
- Claim real-world waste reduction, revenue protection, price stabilization, or executed distribution.
- Add a price module or claim exact price prediction.
- Hard-code user-facing strings in page modules.
- Change the locked color palette silently.
- Hide missing data.
- Present cached weather as live.
- Present fallback allocation as optimal.
- Silently change risk weights, thresholds, or optimizer penalties.
- Report success without real command output.

---

## Required First Response From Any Coding Agent

When asked to begin implementation, do not immediately generate the full codebase. First provide:

1. the build phase proposed;
2. the exact acceptance criteria covered;
3. files to create or modify;
4. tests to add and run;
5. unresolved assumptions or risks;
6. a request for approval.
