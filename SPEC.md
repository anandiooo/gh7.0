# tetani — SPEC.md

# Rapid Hackathon Execution Edition

## 1. Status and Deadline

tetani is being developed for a time-limited hackathon submission.

Current implementation status:

- Phase 0: COMPLETE
- Phase 1: COMPLETE
- Python 3.12 verification: PASSED
- SQLite schema and repositories: COMPLETE
- Deterministic Demo and Empty workspace initialization: COMPLETE
- Current automated test baseline: 83 passing tests

Remaining implementation time at the start of this revision: approximately 21 hours.

This specification replaces the previous sequential Phase 2–10 workflow with a compressed, checkpoint-based execution plan.

The implementation agent is authorized to combine related phases and continue between checkpoints without requesting approval after every phase.

The priority is a reliable end-to-end judging demonstration, not exhaustive production completeness.

---

## 2. Product Identity

### Product names

- Indonesian: tetani
- English: tetani (Farmers' Dream)

### Taglines

- Indonesian: Antisipasi surplus, selamatkan hasil panen.
- English: Detect surplus early. Protect every harvest.

### Product category

Early-warning and decision-support system for agricultural cooperatives.

### Primary module

- Indonesian: Radar Surplus
- English: Surplus Radar

### One-liner

tetani helps an agricultural cooperative detect likely chili-harvest surpluses within the next seven days and generate an explainable allocation plan before produce becomes unabsorbed, loses value, or is wasted.

### Demo organization

Koperasi Tani Merapi Sejahtera.

### Pilot

- Region: Kabupaten Magelang, Central Java
- Commodity: Cabai rawit merah / red bird's-eye chili
- Planning horizon: 7 days
- Stored active horizon: up to 14 days
- Operational data: simulated
- Weather context: BMKG live, cached, or unavailable
- Decision mode: advisory only

---

## 3. Core Judging Story

The complete demo must answer these questions clearly:

1. How much chili is expected to be harvested?
2. How much compatible buyer demand exists?
3. Is daily transport capacity sufficient?
4. When is surplus risk highest?
5. Why is the risk high?
6. How should available harvest be allocated?
7. How much harvest remains unallocated?
8. How does adding demand or transport capacity improve the result?

### Required end-to-end demo

1. Open tetani.
2. Choose Demo workspace.
3. Show deterministic cooperative data.
4. Open Radar Surplus.
5. Show high expected harvest relative to demand and capacity.
6. Display surplus risk score, level, critical date, and explanations.
7. Run allocation.
8. Show allocations, unallocated supply, and unmet demand.
9. Add temporary buyer demand or temporary transport capacity.
10. Run a scenario.
11. Show improved before-and-after metrics.
12. Explain that the recommendation is advisory and based partly on simulated data.

This path has priority over all secondary interfaces.

---

## 4. Priority Classification

### P0 — Submission-critical

These features must work before submission:

- Demo and Empty workspace initialization.
- Manual harvest create, edit, and cancel.
- Buyer create, edit, and deactivate.
- Buyer-demand create, edit, and close.
- Seven-day distribution-capacity editing.
- Deterministic five-factor risk engine.
- Linear allocation optimizer.
- Deterministic greedy fallback.
- Functional Surplus Radar.
- Functional Analysis and Simulation screen.
- At least two scenario overrides:
  - temporary buyer demand;
  - temporary transport capacity.
- Before-and-after scenario comparison.
- Bilingual core demo path.
- Data-provenance labels.
- Error handling without raw tracebacks.
- Local execution.
- Public deployment or documented local fallback.
- Final tests, lint, format check, and Git safety check.

### P1 — Important when time permits

Implement after all P0 items work:

- CSV template.
- CSV preview and atomic import.
- Duplicate import detection.
- Temporary harvest-date scenario override.
- Saving scenario snapshots.
- Analysis history list.
- Live BMKG retrieval.
- Cached BMKG fallback.
- Wider mobile responsiveness.
- Detailed filtering on CRUD screens.

### P2 — Cut or simplify when blocked

These items must not delay the working demo:

- Elaborate animations.
- Complex table styling.
- Full historical analysis-management interface.
- Advanced CSV partial-import workflow.
- Downloadable invalid-row CSV.
- Deep mobile-layout optimization.
- Custom design-system abstractions.
- Additional charts beyond the required daily Radar chart.
- Full browser automation coverage for every control.
- Exhaustive technical-detail panels.
- Nonessential refactoring.
- Repository-hygiene review loops after the repository is already clean.

A P1 or P2 feature may be simplified when the main demo remains correct and the limitation is documented.

---

## 5. Locked Scope

### In scope

- One cooperative.
- One commodity.
- One operator.
- Bahasa Indonesia and English.
- Manual and seeded operational data.
- Harvest planning.
- Buyer and demand management.
- Aggregate daily transport capacity.
- Seven-day surplus detection.
- Deterministic explainable risk score.
- Linear allocation optimization.
- Scenario comparison.
- BMKG context with graceful fallback.
- Immutable analysis snapshots where implemented.
- Demo reset.

### Explicitly out of scope

Do not implement:

- Authentication.
- Authorization or user roles.
- Farmer accounts.
- Buyer accounts.
- Multi-cooperative tenancy.
- Multi-commodity support.
- Marketplace orders.
- Contracts.
- Payments or escrow.
- Buyer outreach.
- WhatsApp, SMS, email, or push notifications.
- Price prediction.
- Revenue calculations.
- LLM-generated decisions.
- ML classifiers trained on simulated labels.
- Computer vision.
- IoT or satellite integration.
- Vehicle, driver, or route models.
- Cold-storage inventory.
- Automatic harvest rescheduling.
- Autonomous execution.
- Credit, insurance, or investment products.
- Native mobile application.
- PDF export.
- Government monitoring dashboards.
- Private personal information.

---

## 6. Locked Technical Stack

Use:

- Python 3.12
- Streamlit multipage application
- SQLite through standard-library sqlite3
- Pydantic
- pandas
- NumPy
- scipy.optimize.linprog with HiGHS
- Plotly
- httpx
- pytest
- Streamlit testing utilities where practical
- Ruff
- requirements.txt with exact pins

Do not add:

- FastAPI
- Flask
- Django
- SQLAlchemy
- Alembic
- External databases
- Separate frontend frameworks
- New dependencies unless a P0 function cannot be implemented with the current stack

---

## 7. Architecture Rules

Use a modular monolith:

Streamlit UI
↓
Application services
├── Harvest management
├── Buyer and capacity management
├── Risk engine
├── Allocation optimizer
├── Scenario service
└── Weather adapter
↓
Repository layer
↓
SQLite

Hard rules:

- UI pages must not contain SQL.
- UI pages must not contain risk formulas.
- UI pages must not build optimization matrices.
- Services must not import Streamlit.
- Repositories own application SQL.
- BMKG adapter is the only module that understands upstream BMKG response structure.
- Identical inputs must produce identical risk and allocation results.
- Session state is temporary UI state only.
- SQLite remains the canonical operational store.
- User-facing text must use centralized translation keys.
- Raw exceptions must not be displayed to users.

---

## 8. Existing Phase 1 Foundation

The following implementation is complete and must be reused rather than rebuilt:

### Canonical tables

- schema_metadata
- cooperative_profiles
- farmers
- harvest_batches
- buyers
- buyer_demands
- distribution_capacities
- weather_snapshots
- analysis_runs
- allocations

### Existing domain models

- CooperativeProfile
- Farmer
- HarvestBatch
- Buyer
- BuyerDemand
- DistributionCapacity
- WeatherSnapshot
- AnalysisRun
- Allocation

### Existing capabilities

- Idempotent schema initialization.
- Parameterized repositories.
- Deterministic Demo workspace.
- Empty workspace.
- Atomic reset.
- Canonical data version.
- Immutable analysis-run repository interface.
- Deterministic seed data.
- Bilingual workspace shell.

### Deterministic Demo baseline

- Cooperative profiles: 1
- Farmers: 30
- Harvest batches: 42
- Buyers: 8
- Buyer demands: 16
- Distribution-capacity records: 7
- Weather snapshots: 0
- Analysis runs: 0
- Allocations: 0

Totals:

- Planned supply: 12,600.0 kg
- Open demand: 2,760.0 kg
- Distribution capacity: 4,350.0 kg

Do not redesign the Phase 1 schema unless a real P0 defect requires a minimal migration.

---

## 9. Screen Requirements

## 9.1 Radar Surplus / Surplus Radar

### Purpose

Show the cooperative's seven-day supply, compatible demand, transport capacity, surplus exposure, and risk.

### P0 elements

- Cooperative and pilot identity.
- Seven-day horizon.
- Total expected harvest.
- Compatible buyer demand.
- Potential surplus.
- Operationally constrained surplus.
- Risk score.
- Risk level.
- Daily Plotly chart:
  - supply;
  - compatible demand;
  - capacity.
- Critical date.
- Top risk factors.
- Plain-language explanation.
- Top recommended actions.
- Weather status.
- Simulated-data label.
- Run Analysis and Allocation button.

### States

- Empty harvest data.
- Missing demand.
- Missing capacity.
- Weather unavailable.
- Successful analysis.
- Analysis failure.

No harvest data must show an empty state, not a misleading low-risk score.

---

## 9.2 Rencana Panen / Harvest Plans

### P0 elements

- Current harvest table.
- Farmer name.
- Harvest date.
- Quantity.
- Grade.
- Confidence.
- Status.
- Add form.
- Edit form or edit mode.
- Cancel action with confirmation.
- Planned-quantity summary.
- Basic filters where inexpensive.

### Required validation

- Farmer must exist and be active.
- Quantity must be finite and greater than zero.
- Quantity must not exceed 100,000 kg.
- Date must be valid.
- Grade must be A, B, or C.
- Confidence must be LOW, MEDIUM, or HIGH.
- Cancelled harvests remain stored but are excluded from current analysis.
- User-facing failures use safe translated messages.

### P1 CSV support

When time permits:

- Downloadable CSV template.
- Upload.
- Preview.
- Row-level validation.
- Deterministic duplicate fingerprint.
- Atomic import by default.
- Maximum 1,000 rows.

CSV work must not delay manual CRUD, risk, optimizer, or deployment.

---

## 9.3 Buyer & Kapasitas / Buyers & Capacity

### Buyers

P0 operations:

- Create.
- Edit.
- Deactivate.
- List.

Fields:

- Name.
- Channel.
- Location.
- Distance.

Channels:

- TRADITIONAL_MARKET
- RETAILER
- RESTAURANT
- PROCESSOR

Validation:

- Name and location are required.
- Distance is between 0 and 1,000 km.
- Inactive buyers are excluded from new analysis.

### Buyer demands

P0 operations:

- Create.
- Edit.
- Close.
- List.

Fields:

- Buyer.
- Quantity.
- Accepted grades.
- Required-by date.
- Priority.

Validation:

- Quantity must be greater than zero.
- At least one accepted grade is required.
- Priority is 1, 2, or 3.
- Priority 3 is highest.
- Closed demands are excluded from new optimization.
- Buyer must be active when creating new demand.

### Distribution capacity

P0 operations:

- Show seven dates.
- Enter or update capacity for each date.
- Save through repository/service.
- Flag missing dates.

Rules:

- Capacity is zero or greater.
- Missing capacity is treated as zero.
- No vehicle or route entities.

---

## 9.4 Analysis & Simulation

### P0 base analysis

The screen must support:

- Seven-day horizon.
- Run-analysis button.
- Risk score and level.
- Factor breakdown.
- Solver status.
- Allocation table.
- Unallocated-harvest table.
- Unmet-demand table.
- Allocated kilograms.
- Unallocated supply rate.
- Demand-fulfillment rate.
- Advisory disclaimer.

### P0 scenarios

At minimum support:

1. Add temporary buyer demand.
2. Increase temporary daily capacity.

Temporary changes:

- exist only in memory for calculation;
- do not mutate canonical tables;
- are clearly labeled;
- are applied to a copy of the base analysis input.

Show:

- base metrics;
- scenario metrics;
- metric differences;
- risk change;
- allocated-quantity change;
- unallocated-supply change;
- demand-fulfillment change.

### P1 scenario capability

When time permits:

- Move a temporary harvest date.
- Save immutable scenario snapshot.
- Link scenario run to base run.
- Show minimal analysis history.

Do not build a complex history-management screen.

---

## 10. Risk Engine

The risk engine must be deterministic and independent from Streamlit.

### Formula

risk_score =
45 × supply_demand_gap_ratio

- 20 × harvest_concentration_ratio
- 15 × transport_capacity_gap_ratio
- 10 × weather_disruption_score
- 10 × estimate_uncertainty_score

Clamp the result to 0–100.

### Supply-demand gap

supply_demand_gap_ratio =
max(0, total_supply - compatible_demand)
/ max(total_supply, 1)

### Harvest concentration

harvest_concentration_ratio =
largest_single_day_supply
/ max(total_supply, 1)

### Capacity gap

transport_capacity_gap_ratio =
sum(max(0, daily_supply - daily_capacity))
/ max(total_supply, 1)

### Weather disruption

weather_disruption_score:

- Average normalized score for available forecast dates.
- Value between 0 and 1.
- Use 0 when unavailable.
- Add an explicit weather-unavailable warning.

### Estimate uncertainty

Confidence values:

- HIGH = 0.0
- MEDIUM = 0.5
- LOW = 1.0

Use a quantity-weighted average unless existing implementation contracts require an equivalent documented deterministic calculation.

### Risk levels

- 0.00–24.99: LOW
- 25.00–49.99: MEDIUM
- 50.00–74.99: HIGH
- 75.00–100.00: CRITICAL

### Risk result

Expose:

- score;
- level;
- total supply;
- compatible demand;
- daily values;
- critical dates;
- factor raw values;
- weighted points;
- weather status;
- warnings;
- translated explanation codes.

### Critical date

Use the date with the greatest operational surplus or highest documented daily-risk contribution.

Tie-breaking must be deterministic, preferring the earliest date.

### Explanations

Generate explanations from translation keys.

Show at least the top three non-zero factors when available.

Do not use an LLM.

---

## 11. Allocation Optimizer

Use scipy.optimize.linprog with HiGHS.

### Decision variable

Continuous kilograms allocated from:

harvest batch → buyer demand → delivery date

### Constraints

1. Allocation is non-negative.
2. A harvest batch cannot be overallocated.
3. A demand cannot be overfulfilled.
4. Harvest grade must be accepted.
5. Delivery date must be on or after harvest date.
6. Delivery date must be on or before demand deadline.
7. Daily allocation cannot exceed transport capacity.
8. Cancelled batches are excluded.
9. Closed demands are excluded.
10. Inactive buyers are excluded.
11. Inactive farmers cannot contribute new harvest records.
12. Tiny floating residue below 0.001 kg becomes zero.

### Objective priority

Use documented linear penalties in this order:

1. Strongly minimize unallocated supply.
2. Prefer higher-priority demand.
3. Prefer earlier feasible delivery.
4. Prefer shorter distance.
5. Never include price or speculative revenue.

### Result

Expose:

- status;
- objective value;
- allocations;
- allocated kilograms;
- unallocated kilograms;
- unmet demand kilograms;
- unallocated batches;
- unmet demands;
- warnings;
- reason codes.

### Statuses

- OPTIMAL
- FEASIBLE_FALLBACK
- NO_DATA
- FAILED

Only a successful linprog result may be labeled OPTIMAL.

### Greedy fallback

On solver failure:

- use deterministic ordering;
- prioritize earlier deadlines;
- then higher demand priority;
- then shorter distance;
- respect all quantity, date, grade, and capacity constraints;
- label result FEASIBLE_FALLBACK.

No fallback may violate an optimizer constraint.

---

## 12. Weather Integration

Weather must never block the core demo.

### P0 behavior

Core risk and optimization must work with:

weather_status = UNAVAILABLE

When unavailable:

- weather contributes zero risk points;
- the UI shows Weather Unavailable / Cuaca Tidak Tersedia;
- analysis continues;
- BMKG is not falsely labeled live.

### P1 BMKG adapter

Implement when core workflow is stable:

Endpoint:

GET <https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={adm4_code}>

Timeout:

- 3 seconds.

Behavior:

1. Attempt live request only when necessary.
2. Normalize supported fields.
3. Store successful snapshot.
4. On timeout, HTTP failure, or malformed data:
   - use newest compatible cache.
5. Mark cache older than 24 hours stale.
6. When no cache exists:
   - return UNAVAILABLE.
7. Never execute a live request on every Streamlit rerun.
8. Tests must mock all network calls.

### Timebox

Do not spend more than 60 minutes debugging live BMKG structure.

When live parsing remains unstable:

- retain mocked adapter tests;
- retain cache and unavailable behavior;
- display the limitation;
- continue to deployment.

---

## 13. Bilingual UI

Languages:

- ID
- EN

Default:

- ID

All core-demo text must be translated:

- navigation;
- page headings;
- form labels;
- validation messages;
- success messages;
- error messages;
- risk levels;
- risk explanations;
- KPI labels;
- scenario labels;
- source badges;
- disclaimers.

Translation dictionaries must have identical key sets.

Names, locations, identifiers, and user-entered content are not translated.

Hard-coded user-facing strings inside pages are prohibited unless they are non-linguistic data values.

---

## 14. Visual and Accessibility Requirements

Locked colors:

- Primary: #145319
- Secondary: #388E3C
- Accent: #D97706
- Background: #F1F5F0
- Surface: #FFFFFF
- Primary text: #1A2E1A

P0 requirements:

- Main workflow works at 1366×768.
- No horizontal overflow.
- KPI cards remain readable.
- Forms have visible labels.
- Risk status includes text, not color alone.
- Tables remain understandable without hover.
- Primary actions use explicit verbs.
- User errors do not expose stack traces or paths.
- Prototype banner is visible.
- Simulated-data status is visible.
- Allocation output is labeled advisory.

Tablet and mobile layouts must remain usable, but pixel-perfect mobile polish is P1.

---

## 15. Error and Empty States

### No harvest

- Show guidance.
- Do not calculate a low-risk score.

### No demand

- Show full absorption gap.
- Risk may run.
- Optimizer may return zero allocation.

### No capacity

- Treat missing dates as zero.
- Show a blocking warning for allocation.

### No compatible grade

- Keep affected harvest unallocated.
- Explain grade incompatibility.

### Demand exceeds supply

- Allocate available supply.
- Show unmet demand.
- Do not call the shortage a surplus.

### Solver failure

- Run deterministic fallback.
- Mark FEASIBLE_FALLBACK.

### Weather failure

- Use cache.
- Otherwise use UNAVAILABLE.
- Continue analysis.

### Database error

- Show concise translated error.
- Do not expose SQL, stack trace, or local file path.

### Stale analysis

When canonical data version differs from the analysis input version:

- label the previous result stale;
- require a new base analysis before saving a scenario.

---

## 16. Performance Targets

On the seeded Demo dataset:

- Initial Radar render: under 2 seconds after startup.
- Risk calculation: under 500 ms.
- Optimization: under 3 seconds.
- CSV preview for 1,000 rows: under 2 seconds when CSV is implemented.
- BMKG timeout: 3 seconds.

Performance work must focus on visible judging delays, not premature micro-optimization.

---

## 17. Accelerated Execution Plan

The old Phase 2–10 sequence is replaced by four execution waves.

## Wave A — Operational Data UI

Combines previous Phases 2 and 3.

Maximum implementation time: 3 hours.

Implement in this order:

1. Harvest list.
2. Manual harvest create.
3. Harvest cancel.
4. Harvest edit.
5. Buyer list and create.
6. Demand list and create.
7. Seven-day capacity editor.
8. Buyer/demand edit and state transitions.
9. Basic filters.
10. CSV only after manual flows work.

Required verification:

- Targeted model/service/page tests.
- Create, edit, cancel, close, and deactivate smoke tests.
- Full test suite once at wave completion.
- Ruff check.

Exit condition:

The operator can modify supply, demand, and capacity through the UI without direct database editing.

## Wave B — Decision Core

Combines previous Phases 4 and 5.

Maximum implementation time: 3.5 hours.

Implement:

1. Analysis input builder.
2. Risk models.
3. Five factor calculations.
4. Score and threshold mapping.
5. Critical-date calculation.
6. Explanation codes.
7. Optimization model.
8. Result normalization.
9. Greedy fallback.
10. Invariant tests.

Required verification:

- Risk boundary tests.
- Missing-data tests.
- Optimizer invariant tests.
- Controlled solver-failure test.
- Performance check on seeded data.
- Full test suite at wave completion.

Exit condition:

A deterministic service call produces a valid risk result and valid allocation result from seeded repository data.

## Wave C — Complete Product Demo

Combines previous Phases 6, 7, and 8.

Maximum implementation time: 4 hours.

Implement:

1. Radar KPIs.
2. Daily chart.
3. Risk explanation.
4. Critical-date view.
5. Run-analysis action.
6. Analysis result screen.
7. Allocation table.
8. Unallocated and unmet-demand tables.
9. Temporary buyer-demand scenario.
10. Temporary capacity scenario.
11. Before-and-after comparison.
12. Save snapshot only when inexpensive.
13. Weather unavailable state.
14. BMKG live/cache adapter only after core workflow works.

Required verification:

- Seeded Radar totals match fixture.
- Base analysis runs from UI.
- Scenario improves at least one expected metric.
- Scenario does not mutate canonical data.
- ID and EN core path.
- Full test suite.

Exit condition:

The complete judging story can be demonstrated from Demo reset through scenario comparison.

## Wave D — Hardening and Submission

Combines previous Phases 9 and 10.

Maximum code-polish time: 2 hours.

Then freeze features.

Tasks:

1. Fix empty/loading/error states on the four pages.
2. Verify translation parity.
3. Verify prototype and provenance labels.
4. Verify 1366×768.
5. Test without internet.
6. Deploy to Streamlit Community Cloud.
7. Verify clean startup.
8. Confirm database and secrets are ignored.
9. Capture screenshots.
10. Record backup demo.
11. Run final automated checks.
12. Freeze implementation.

Exit condition:

- Public URL works, or local fallback and recording are ready.
- Complete demo can be performed twice after fresh Demo reset.
- No critical error remains.

---

## 18. Remaining-Time Budget

Recommended allocation from a 21-hour remaining window:

- Phase 1 checkpoint commit: 15 minutes
- Wave A: 3 hours
- Wave B: 3.5 hours
- Wave C: 4 hours
- Wave D code hardening: 2 hours
- Deployment and clean-checkout verification: 1.5 hours
- Demo video and screenshots: 2 hours
- Pitch deck and submission materials: 2 hours
- Rehearsal and final bug buffer: 2.75 hours

Hard rule:

Do not consume submission-material time for secondary product features.

---

## 19. Agent Execution Protocol

The coding agent must operate continuously through the authorized waves.

### Approval behavior

- Do not request approval between every old phase.
- Do not wait after each file.
- Do not repeat Phase 0 or Phase 1 verification.
- Begin the next wave when the current wave exit condition passes.
- Stop only for:
  - destructive schema change;
  - dependency change;
  - scope change outside this specification;
  - security risk;
  - blocker that requires user credentials or deployment access.

### Checkpoint reports

After each wave, report only:

- wave completed;
- major functionality;
- tests passed;
- current blocker;
- next wave.

Keep intermediate reports concise.

### Testing strategy

During implementation:

- run targeted tests;
- run Ruff on changed modules;
- perform focused page smoke checks.

At the end of Waves A, B, and C:

python -m pytest -q
python -m ruff check .
python -m ruff format --check .

At final freeze:

python -m pytest -q
python -m ruff check .
python -m ruff format --check .
git diff --check
git status --short --untracked-files=all

Do not perform repeated clean-environment installations after Python 3.12 has already been verified unless deployment fails.

### Blocker rule

Do not spend more than 20 minutes on one isolated defect.

After 20 minutes:

1. Identify the smallest reliable fallback.
2. Add or preserve a safe error state.
3. Document the limitation.
4. Continue the critical path.

### Code-quality rule

Do not use rapid mode as permission to:

- bypass validation;
- place SQL in pages;
- violate optimizer constraints;
- fake BMKG live status;
- mutate scenario data;
- expose raw exceptions;
- silently skip failing tests;
- label fallback results optimal.

Rapid execution means reducing process overhead and secondary scope, not reducing correctness of the decision engine.

---

## 20. Critical Acceptance Gate

The submission is technically ready when all items below pass.

### Workspace

- Demo initializes deterministically.
- Empty initializes without operational records.
- Reset requires confirmation.

### Data management

- Manual harvest create works.
- Harvest edit works.
- Harvest cancel works.
- Buyer create works.
- Buyer update/deactivate works.
- Demand create works.
- Demand update/close works.
- Seven-day capacity editing works.

### Risk

- Seeded input produces deterministic score.
- Factor points sum to final score within tolerance.
- Thresholds are correct.
- Missing weather does not fail analysis.
- Top factors are explained.

### Optimization

- No batch is overallocated.
- No demand is overfilled.
- Grade compatibility is respected.
- Dates are respected.
- Capacity is respected.
- Fallback is deterministic and correctly labeled.

### Radar

- Supply, demand, capacity, surplus, and risk appear.
- Daily chart appears.
- Critical date appears.
- Empty and partial-data states work.

### Scenario

- Temporary buyer demand works.
- Temporary capacity works.
- Canonical data remains unchanged.
- Before-and-after metrics appear.
- Scenario changes the seeded result.

### UX

- Indonesian core path works.
- English core path works.
- Four pages load.
- No raw exception is shown.
- Data is clearly labeled simulated.
- Allocation is clearly labeled advisory.
- Main demo works at 1366×768.

### Submission

- pytest passes.
- Ruff lint passes.
- Ruff format check passes.
- Runtime database is ignored.
- Secrets are absent.
- Public deployment works or a verified local fallback exists.
- Backup recording exists.
- Complete demo succeeds twice from fresh reset.

---

## 21. Submission Freeze Rules

When fewer than four hours remain:

- Do not add new features.
- Do not restructure modules.
- Do not rename files.
- Do not change the database schema unless the app cannot run.
- Do not change dependency versions unless deployment cannot install.
- Fix only critical demo failures.
- Preserve a working local version.
- Record the demo before attempting optional polish.

When fewer than two hours remain:

- Freeze source code.
- Run final checks.
- Capture screenshots.
- Verify repository contents.
- Complete submission forms.
- Rehearse the pitch.
- Keep local and prerecorded fallbacks ready.

---

## 22. Definition of Done

tetani is done for the hackathon when:

1. The deterministic Demo workspace loads.
2. The operator can inspect and modify supply, demand, and capacity.
3. The Radar exposes a clear seven-day surplus problem.
4. The risk engine explains why the risk is high.
5. The optimizer creates a valid allocation plan.
6. Unallocated supply is visible.
7. A temporary buyer or capacity scenario improves the result.
8. The comparison is clear.
9. Indonesian and English core paths work.
10. The application starts without uncaught exceptions.
11. Tests and Ruff checks pass.
12. Simulated and advisory status is clear.
13. A deployable or recordable working version exists.

Anything beyond these points is secondary to submitting a stable, understandable, and convincing prototype.
