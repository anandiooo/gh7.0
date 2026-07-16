# MimpiTani — SPEC.md

## 1. Overview

### Product identity

- **Indonesian product name:** MimpiTani
- **English product name:** MimpiTani (Farmers' Dream)
- **Indonesian tagline:** Antisipasi surplus, selamatkan hasil panen.
- **English tagline:** Detect surplus early. Protect every harvest.
- **Product category:** Early-warning and decision-support system
- **Primary dashboard module:** Radar Surplus / Surplus Radar

**One-liner:** MimpiTani helps an agricultural cooperative detect likely chili harvest surpluses within the next seven days and generate an explainable allocation plan before produce becomes unabsorbed, loses value, or is wasted.

**Problem:** Small farmers usually estimate and communicate harvests separately. A cooperative may therefore discover too late that several members will harvest the same perishable commodity at the same time while confirmed buyer demand and daily transport capacity are insufficient. The late discovery leaves little time to contact alternative buyers, reserve processing capacity, or adjust distribution. MimpiTani combines upcoming harvest estimates, compatible buyer demand, transport capacity, and short-horizon weather context to expose the imbalance early and recommend an allocation plan.

**Target user:** A single operator of a chili-farmer cooperative or collection center in a simulated pilot in Kabupaten Magelang, Central Java. Farmers and buyers are stakeholders and data sources, but they do not receive separate accounts or portals in v1.

**Demo organization:** Koperasi Tani Merapi Sejahtera.

**Pilot configuration:**

- Commodity: cabai rawit merah / red bird's-eye chili.
- Operational horizon: next 7 days.
- Stored planning horizon: up to 14 days.
- Weather horizon: only dates covered by available BMKG forecasts.
- Deployment mode: public hackathon prototype.
- Harvest, buyer, and logistics data: simulated.
- External live data: BMKG weather when available.
- Decision mode: advisory only. The operator remains responsible for approving and executing decisions.

**Language requirements:**

- UI languages: Bahasa Indonesia and English.
- Default: Bahasa Indonesia.
- Language switcher: `ID | EN`.
- The preference persists for the active browser session.
- Product name in Indonesian: `MimpiTani`.
- Product name in English: `MimpiTani (Farmers' Dream)`.
- All user-facing strings use centralized translation keys.
- Names, locations, IDs, and user-entered content are not translated.

**Core product principle:** The application must answer these questions clearly:

1. How much chili is expected to be harvested?
2. How much compatible buyer demand is available?
3. Is daily transport capacity sufficient?
4. When and why is surplus risk highest?
5. How should available harvest be allocated?
6. How does adding a buyer or increasing transport capacity change the result?

The product is not a marketplace, price forecaster, fleet-management system, or autonomous trading platform.

---

## 2. Core User Flows

### Flow 1 — Start a planning workspace

Operator opens MimpiTani → selects `Muat Data Demo / Load Demo Data` or `Mulai Kosong / Start Empty` → the application initializes the selected workspace → prototype and data-source labels appear → operator enters the Surplus Radar.

Demo mode loads deterministic seeded data. Empty mode creates only the schema and workspace configuration. Simulated data must never load silently.

### Flow 2 — Record an upcoming harvest

Operator opens **Rencana Panen / Harvest Plans** → adds one harvest estimate manually or imports a CSV → the application validates farmer, date, quantity, grade, location, and estimate confidence → operator reviews errors and confirms valid data → records are stored → previous analysis is marked stale.

### Flow 3 — Record market absorption and distribution capacity

Operator opens **Buyer & Kapasitas / Buyers & Capacity** → adds or edits a buyer and its demand → specifies accepted grades, requested quantity, delivery deadline, distance, priority, and channel type → enters daily aggregate transport capacity → valid demand and capacity records are stored.

### Flow 4 — Detect and understand surplus risk

Operator opens **Radar Surplus / Surplus Radar** → selects the seven-day horizon → the application aggregates harvest supply, compatible buyer demand, and transport capacity → retrieves live or cached BMKG weather context → calculates a risk score and level → shows critical dates and a plain-language explanation in the selected language.

### Flow 5 — Generate and compare an allocation scenario

Operator opens **Analisis & Simulasi / Analysis & Simulation** → runs the allocation optimizer → reviews allocations by batch, buyer, and delivery date → sees unallocated supply and unmet demand → adds a temporary buyer and increases temporary transport capacity → reruns the scenario → compares before and after results → optionally saves the scenario snapshot.

---

## 3. Scope

### In scope (v1)

1. **Bilingual single-operator application**
   - No login.
   - One configured cooperative.
   - One pilot commodity.
   - Bahasa Indonesia and English.
   - Default Bahasa Indonesia.
   - Session-persistent `ID | EN` switcher.
   - Centralized translation dictionaries with matching keys.

2. **Explicit workspace initialization**
   - `Muat Data Demo / Load Demo Data`.
   - `Mulai Kosong / Start Empty`.
   - Deterministic demo seed.
   - No simulated operational data is loaded without the operator's choice.

3. **Harvest-plan management**
   - Create, read, update, and cancel harvest estimates.
   - Manual entry.
   - CSV template, preview, validation, and import.
   - Quality grade A/B/C entered manually.
   - Estimate confidence: Low, Medium, High.

4. **Buyer and demand management**
   - Create, read, update, and deactivate buyers.
   - Create, read, update, and close demands.
   - Specific buyer plus channel type.
   - Accepted grades, requested quantity, deadline, priority, and distance.

5. **Aggregate daily distribution capacity**
   - One total capacity in kilograms per date.
   - Missing dates are treated as zero and visibly flagged.
   - No vehicle or route model.

6. **Seven-day supply-demand radar**
   - Daily expected harvest.
   - Compatible demand.
   - Daily transport capacity.
   - Potential surplus.
   - Operationally constrained surplus.
   - Critical date.

7. **Explainable five-factor surplus-risk engine**
   - Deterministic and testable.
   - Score 0–100.
   - Low, Medium, High, Critical.
   - Supply-demand gap.
   - Harvest concentration.
   - Transport-capacity gap.
   - Weather disruption.
   - Estimate uncertainty.
   - Bilingual explanations generated from translation keys.

8. **Linear allocation optimizer**
   - A harvest batch can be split across buyers.
   - Respects quantity, grade, harvest date, buyer deadline, and daily transport capacity.
   - Prioritizes minimizing unallocated supply.
   - Secondary preferences: higher-priority demand, earlier feasible delivery, shorter distance.
   - Deterministic greedy fallback only on solver failure.

9. **What-if scenario simulator**
   - Add or increase temporary buyer demand.
   - Change temporary transport capacity.
   - Move a temporary harvest date.
   - Compare base and scenario metrics.
   - Temporary changes do not mutate canonical data.
   - Saved snapshots are immutable and linked to the base run.

10. **BMKG weather adapter**
    - Live API when available.
    - Cached fallback.
    - Analysis continues when weather is unavailable.
    - Cache timestamp and stale state are shown.
    - BMKG is visibly credited.

11. **Analysis history**
    - Base analysis snapshots.
    - Scenario snapshots linked to base runs.
    - Failed runs do not overwrite the last successful result.
    - Canonical changes mark old analysis stale.

12. **Operational metrics**
    - Allocated produce in kilograms.
    - Unallocated supply rate.
    - Buyer-demand fulfillment rate.

13. **Demo reset**
    - Rebuild from version-controlled seed data.
    - Explicit confirmation is required.

### Explicitly out of scope (later / never in v1)

The coding agent must not implement any of the following unless `SPEC.md` is explicitly revised:

- Farmer or buyer accounts and portals.
- Authentication, authorization, or multi-role access.
- Multi-cooperative tenancy.
- Multi-commodity support.
- Marketplace, orders, contracts, invoices, payments, or escrow.
- Real buyer outreach or WhatsApp/SMS/email/push notifications.
- Any price module or exact future-price prediction.
- Revenue-protected calculations.
- Machine-learning classifiers trained on synthetic decision labels.
- LLM-generated operational decisions.
- Computer-vision grading.
- IoT, sensors, or satellite forecasting.
- Vehicle entities, drivers, fuel, fleet, or road-route optimization.
- Cold-storage inventory management.
- Automatic harvest rescheduling.
- Autonomous execution of recommendations.
- Credit, insurance, or investment products.
- Native Android, iOS, or Flutter application.
- PDF export.
- Government or national monitoring dashboards.
- Personally identifiable data such as NIK, phone number, bank information, or exact household address.

---

## 4. Data Model

SQLite is the canonical local store. Pydantic models define validation contracts. IDs are UUID strings generated by the application. All timestamps use ISO 8601 consistently and are displayed in the `Asia/Jakarta` timezone.

### CooperativeProfile

Represents the single v1 workspace.

```text
CooperativeProfile
- id: str, primary key
- name: str
- pilot_region: str
- commodity_code: str
- adm4_code: str | null
- workspace_mode: enum("DEMO", "EMPTY")
- created_at: datetime
- updated_at: datetime
```

Rules:

- Exactly one profile exists in v1.
- Demo name: `Koperasi Tani Merapi Sejahtera`.
- Commodity code is fixed to `CABAI_RAWIT_MERAH`.

### Farmer

Represents a cooperative member whose future harvest is being planned.

```text
Farmer
- id: str, primary key
- name: str, required
- village_name: str, required
- subdistrict_name: str, required
- adm4_code: str | null
- is_active: bool, default true
- created_at: datetime
- updated_at: datetime

Relationships:
- has_many: HarvestBatch
```

Constraints:

- `name` must be 2–100 characters.
- `adm4_code`, when present, must follow the dotted Indonesian level-IV administrative-code pattern accepted by the weather adapter.
- Inactive farmers remain visible in historical analysis but cannot receive new harvest records.

### HarvestBatch

Represents one expected harvest from one farmer on one date.

```text
HarvestBatch
- id: str, primary key
- farmer_id: str, foreign key -> Farmer.id
- commodity_code: str, fixed to "CABAI_RAWIT_MERAH" in v1
- estimated_harvest_date: date
- estimated_quantity_kg: float
- quality_grade: enum("A", "B", "C")
- estimate_confidence: enum("LOW", "MEDIUM", "HIGH")
- maturity_note: str | null
- status: enum("PLANNED", "CANCELLED")
- source_type: enum("MANUAL", "CSV", "SEED")
- external_reference: str | null
- created_at: datetime
- updated_at: datetime

Relationships:
- belongs_to: Farmer
- has_many: Allocation
```

Constraints:

- Quantity must be greater than 0 and no more than 100,000 kg.
- Harvest date must be within 90 days of the current date for manual input.
- Cancelled batches do not contribute to current supply.
- An exact duplicate from the same CSV import must be rejected or flagged before insertion.

### Buyer

Represents a specific market, retailer, restaurant, processor, or other destination.

```text
Buyer
- id: str, primary key
- name: str, required
- channel_type: enum(
    "TRADITIONAL_MARKET",
    "RETAILER",
    "RESTAURANT",
    "PROCESSOR"
  )
- location_name: str, required
- distance_km: float
- is_active: bool, default true
- created_at: datetime
- updated_at: datetime

Relationships:
- has_many: BuyerDemand
```

Constraints:

- Distance must be 0–1,000 km.
- Inactive buyers remain in previous analysis snapshots but are excluded from new analysis.

### BuyerDemand

Represents a buyer's open demand for the pilot commodity.

```text
BuyerDemand
- id: str, primary key
- buyer_id: str, foreign key -> Buyer.id
- commodity_code: str, fixed to "CABAI_RAWIT_MERAH"
- requested_quantity_kg: float
- accepted_grades_json: str
- required_by_date: date
- priority: int, 1–3
- status: enum("OPEN", "CLOSED")
- created_at: datetime
- updated_at: datetime

Relationships:
- belongs_to: Buyer
- has_many: Allocation
```

Constraints:

- Requested quantity must be greater than 0.
- Accepted grades must contain at least one of A, B, or C.
- Priority `3` is highest; `1` is lowest.
- Closed demand is excluded from new optimization runs.

### DistributionCapacity

Represents aggregate transport capacity available on one date.

```text
DistributionCapacity
- id: str, primary key
- capacity_date: date, unique
- available_capacity_kg: float
- note: str | null
- created_at: datetime
- updated_at: datetime
```

Constraints:

- Capacity must be 0–1,000,000 kg.
- Missing dates are treated as zero capacity in optimization and visibly flagged to the operator.

### WeatherSnapshot

Stores normalized or raw BMKG weather data for fallback.

```text
WeatherSnapshot
- id: str, primary key
- adm4_code: str
- fetched_at: datetime
- analysis_date: datetime | null
- valid_from: datetime | null
- valid_to: datetime | null
- source_status: enum("LIVE", "CACHE")
- normalized_json: str
- raw_payload_json: str
```

Rules:

- Keep the newest successful snapshot per administrative code.
- Cached data must display its timestamp.
- Weather older than 24 hours is marked stale but may still be displayed for demo fallback.
- A stale cache must not block analysis.

### AnalysisRun

Immutable snapshot of one complete risk and optimization calculation.

```text
AnalysisRun
- id: str, primary key
- parent_run_id: str | null, foreign key -> AnalysisRun.id
- scenario_name: str
- created_at: datetime
- horizon_start: date
- horizon_end: date
- risk_score: float
- risk_level: enum("LOW", "MEDIUM", "HIGH", "CRITICAL")
- total_supply_kg: float
- compatible_demand_kg: float
- allocated_kg: float
- unallocated_kg: float
- unallocated_supply_rate: float
- demand_fulfillment_rate: float
- solver_status: enum("OPTIMAL", "FEASIBLE_FALLBACK", "NO_DATA", "FAILED")
- weather_status: enum("LIVE", "CACHE", "UNAVAILABLE")
- input_snapshot_json: str
- risk_breakdown_json: str
- result_snapshot_json: str
- error_message: str | null

Relationships:
- has_many: Allocation
- optionally belongs_to: parent AnalysisRun
```

Rules:

- Analysis runs are immutable after creation.
- Scenario runs reference their base run through `parent_run_id`.
- A failed run stores the error but must not overwrite the last successful run.

### Allocation

Stores one optimizer result assigning part of a batch to one buyer demand on a delivery date.

```text
Allocation
- id: str, primary key
- analysis_run_id: str, foreign key -> AnalysisRun.id
- harvest_batch_id: str, foreign key -> HarvestBatch.id
- buyer_demand_id: str, foreign key -> BuyerDemand.id
- delivery_date: date
- allocated_quantity_kg: float
- distance_km_snapshot: float
- allocation_reason_json: str
- created_at: datetime

Relationships:
- belongs_to: AnalysisRun
- belongs_to: HarvestBatch
- belongs_to: BuyerDemand
```

Constraints:

- Allocated quantity must be greater than 0.
- Total allocations from one batch cannot exceed its quantity.
- Total allocations to one demand cannot exceed requested quantity.
- Grade must be accepted by the demand.
- Delivery must not occur before harvest or after the buyer deadline.
- Total allocations on a date cannot exceed aggregate distribution capacity for that date.

### Relationship summary

```text
CooperativeProfile 1

Farmer 1 ───< HarvestBatch

Buyer 1 ───< BuyerDemand

AnalysisRun 1 ───< Allocation

HarvestBatch 1 ───< Allocation >─── 1 BuyerDemand

AnalysisRun 1 ───< AnalysisRun
(base run)          (scenario runs)
```

---

## 5. Tech Stack

The implementation must use this stack unless the user explicitly approves a change.

- **Language:** Python 3.12.
- **Frontend:** Streamlit multipage application.
- **Backend:** Same-process modular Python service layer; no separate HTTP backend.
- **Database:** SQLite through Python's standard-library `sqlite3`.
- **Schema validation:** Pydantic.
- **Data processing:** pandas and NumPy.
- **Optimization:** `scipy.optimize.linprog` using the HiGHS solver.
- **Charts:** Plotly.
- **External HTTP:** httpx.
- **Testing:** pytest and Streamlit's built-in testing utilities where practical.
- **Lint and formatting:** Ruff.
- **Auth:** None in v1.
- **Hosting/deploy:** Streamlit Community Cloud from a public GitHub repository.
- **Local fallback:** `streamlit run app.py`.
- **Secrets:** `.streamlit/secrets.toml` locally and Streamlit Cloud secrets in deployment. No secret may be committed.
- **Weather source:** Official BMKG public forecast API.
- **Timezone:** `Asia/Jakarta`.
- **Package management:** `requirements.txt` with pinned versions for the hackathon submission.

### Architecture decision

Use a **modular monolith**:

```text
Streamlit UI
    ↓
Application services
    ├── Harvest service
    ├── Buyer service
    ├── Risk engine
    ├── Allocation optimizer
    ├── Scenario service
    └── Weather adapter
    ↓
Repository layer
    ↓
SQLite
```

Hard rules:

- UI pages must not contain SQL.
- UI pages must not implement risk or optimization formulas.
- Services must not import Streamlit.
- The weather adapter is the only module allowed to understand the BMKG response shape.
- The SQLite repository is the only module allowed to execute application SQL.
- Domain calculations must be deterministic for identical inputs.

---

## 6. Screens / UI

### Locked visual system

- **Primary / Dark Green:** `#145319` — Deep Forest
- **Secondary / Light Green:** `#388E3C` — Vibrant Leaf
- **Accent / Warning Orange:** `#D97706` — Amber Earth
- **App Background:** `#F1F5F0` — Soft Sage Mist
- **Surface / Card Background:** `#FFFFFF` — Crisp White
- **Primary Text:** `#1A2E1A` — Dark Moss

Risk and state information must never depend on color alone. Additional error and neutral colors may be introduced only when necessary and must maintain readable contrast.

### Global shell

Header content:

- Indonesian: `MimpiTani`.
- English: `MimpiTani (Farmers' Dream)`.
- Prototype badge.
- `ID | EN` language switcher.

Global prototype banner:

- ID: `Data panen, buyer, dan kapasitas pada prototype ini adalah simulasi.`
- EN: `Harvest, buyer, and capacity data in this prototype are simulated.`

Weather badge must show one of:

- `BMKG Live`;
- `Cache BMKG / BMKG Cache` with timestamp;
- `Cuaca Tidak Tersedia / Weather Unavailable`.

### Welcome state — Workspace Choice

**Purpose:** Let the operator consciously choose between a deterministic demo and an empty workspace.

**Elements:** Product identity, short explanation, language switcher, `Muat Data Demo / Load Demo Data`, `Mulai Kosong / Start Empty`, and simulation disclaimer.

**States:** Initial, initializing, initialization failed, initialized and redirecting.

### Screen 1 — Radar Surplus / Surplus Radar

**Purpose:** Give the operator an immediate seven-day view of upcoming supply, market absorption, logistics constraints, and critical surplus risk.

**Elements:**

- App title and pilot label.
- Data-provenance banner:
  - simulated harvest and buyer data;
  - live, cached, or unavailable BMKG status.
- Date-range selector fixed to a maximum 7-day visible horizon.
- KPI cards:
  - total expected harvest;
  - compatible confirmed demand;
  - potential surplus;
  - operationally constrained surplus;
  - risk level.
- Daily chart containing:
  - expected harvest;
  - compatible demand;
  - transport capacity.
- Critical-date card.
- Plain-language risk explanation.
- Top three recommended actions.
- Button: `Jalankan Analisis & Alokasi / Run Analysis & Allocation`.
- Link/button to load demo data when the workspace is empty.

**States:**

- **Empty:** Explain that no harvest plan exists and provide `Muat Data Demo / Load Demo Data` and `Tambah Rencana Panen / Add Harvest Plan`.
- **Loading:** Skeleton or spinner with the exact task, for example `Menghitung risiko surplus...`.
- **Success:** Show metrics, chart, explanation, and source timestamps.
- **Partial data:** Show warning when buyer demand, transport capacity, or weather is missing.
- **Error:** Keep the page usable, show a concise error, and offer retry or navigation to the relevant data screen.

### Screen 2 — Rencana Panen / Harvest Plans

**Purpose:** Maintain upcoming harvest estimates from cooperative members.

**Elements:**

- Search and filters by farmer, date, grade, confidence, and status.
- Harvest table.
- `Tambah Rencana Panen` form.
- Edit action.
- Cancel action with confirmation.
- CSV upload.
- CSV-template download.
- Import preview showing valid rows and row-level errors.
- Demo-seed button when appropriate.
- Summary of total planned quantity in the active horizon.

**States:**

- **Empty:** Explain the required fields and show manual-add, CSV-import, and demo-data actions.
- **Uploading:** Show file name and parsing progress.
- **Validation failure:** Keep valid and invalid rows separate; do not insert any row until the operator confirms a valid batch import.
- **Partial import:** Allowed only after explicit confirmation; invalid rows remain downloadable as an error CSV.
- **Database error:** Do not lose typed form data; show retry.

### Screen 3 — Buyer & Kapasitas / Buyers & Capacity

**Purpose:** Define where harvest can go and how much can be transported.

**Elements:**

- Buyer table with channel and distance.
- Demand table with quantity, accepted grades, deadline, priority, and status.
- Add/edit buyer form.
- Add/edit/close demand form.
- Seven-day transport-capacity editor.
- Validation summary showing:
  - demand with no accepted grades;
  - deadlines outside the planning horizon;
  - missing capacity dates.
- Compatibility preview by grade.

**States:**

- **Empty buyers:** Explain that surplus cannot be allocated without demand.
- **Empty capacity:** Warn that optimization treats missing capacity as zero.
- **Invalid deadline:** Prevent save and explain the valid date range.
- **No compatible grade:** Save is allowed only if at least one grade is selected.
- **Error:** Keep unsaved form state and provide retry.

### Screen 4 — Analisis & Simulasi / Analysis & Simulation

**Purpose:** Run the risk engine and optimizer, inspect the allocation result, and compare a what-if scenario with the base plan.

**Elements:**

- Analysis controls:
  - horizon;
  - run-analysis button;
  - last-run timestamp.
- Risk score and level.
- Factor-contribution breakdown.
- Solver-status badge.
- Allocation table:
  - harvest batch;
  - farmer;
  - buyer;
  - channel;
  - delivery date;
  - allocated kilograms;
  - reason.
- Unallocated-batch table.
- Unmet-demand table.
- Metrics:
  - allocated kilograms;
  - unallocated supply rate;
  - demand-fulfillment rate.
- Scenario editor:
  - add temporary buyer demand;
  - modify temporary transport capacity;
  - move a temporary harvest date.
- `Jalankan Skenario`.
- Before/after comparison.
- `Simpan Snapshot Skenario`.
- Clear disclaimer that the result is advisory and based partly on simulated data.

**States:**

- **No analysis:** Explain prerequisites and show missing-data checklist.
- **Running:** Show risk-calculation and optimization steps separately.
- **Optimal:** Display full result.
- **No feasible allocation:** Display why, retain risk result, and suggest specific data changes.
- **Optimizer failure:** Use a documented greedy fallback and mark status as `FEASIBLE_FALLBACK`; never present fallback as optimal.
- **Scenario unchanged:** Explain that the scenario did not modify any effective constraint.
- **Stale base run:** Warn when canonical data changed after the base run and require a new base analysis.

---

## 7. API / Data Contracts

MimpiTani is a single-process application and has no internal HTTP API. Contracts between UI, services, and repositories must use Pydantic models. The only network contract is the BMKG weather API.

### Internal translation contract

All user-facing text must use centralized keys such as:

```python
t("nav.radar")
t("action.run_analysis")
t("state.empty.harvest")
t("risk.level.high")
```

Files:

```text
src/i18n/id.json
src/i18n/en.json
```

Rules:

- Both dictionaries have identical key sets.
- Missing keys fail automated tests.
- Page modules do not hard-code user-facing strings.
- Names, locations, identifiers, and user-entered text are not translated.

### External BMKG contract

**Endpoint**

```text
GET https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={administrative_level_iv_code}
```

Official reference: `https://data.bmkg.go.id/prakiraan-cuaca/`

**Timeout:** 3 seconds.

**Retry:** No automatic repeated retry during a Streamlit rerun. The operator may manually retry. This prevents a slow API from blocking every page render.

**Fields consumed after normalization:**

```json
{
  "adm4_code": "33.xx.xx.xxxx",
  "analysis_date": "2026-07-16T00:00:00Z",
  "points": [
    {
      "local_datetime": "2026-07-16 13:00:00",
      "temperature_c": 29,
      "humidity_percent": 78,
      "weather_description": "Hujan Ringan",
      "wind_speed_kmh": 8
    }
  ],
  "source_status": "LIVE"
}
```

The adapter must tolerate additional upstream fields and isolate nesting changes from the rest of the application.

### Internal contract — analysis input

```json
{
  "horizon_start": "2026-07-17",
  "horizon_end": "2026-07-23",
  "harvest_batches": [
    {
      "id": "uuid",
      "farmer_id": "uuid",
      "harvest_date": "2026-07-18",
      "quantity_kg": 500.0,
      "grade": "B",
      "confidence": "MEDIUM"
    }
  ],
  "buyer_demands": [
    {
      "id": "uuid",
      "buyer_id": "uuid",
      "quantity_kg": 300.0,
      "accepted_grades": ["A", "B"],
      "required_by_date": "2026-07-19",
      "priority": 2,
      "distance_km": 18.0
    }
  ],
  "distribution_capacity": [
    {
      "date": "2026-07-18",
      "capacity_kg": 1000.0
    }
  ],
  "weather": {
    "status": "LIVE",
    "daily_disruption_scores": {
      "2026-07-18": 0.4
    }
  }
}
```

### Internal contract — risk result

```json
{
  "score": 72.5,
  "level": "HIGH",
  "critical_dates": ["2026-07-18"],
  "factors": [
    {
      "code": "SUPPLY_DEMAND_GAP",
      "label": "Kesenjangan supply dan demand",
      "raw_value": 0.48,
      "weighted_points": 21.6,
      "explanation": "Permintaan kompatibel hanya menyerap 52% panen."
    }
  ],
  "weather_status": "LIVE",
  "warnings": []
}
```

### Risk-engine formula

The score is deterministic and clamped to 0–100.

```text
risk_score =
    45 × supply_demand_gap_ratio
  + 20 × harvest_concentration_ratio
  + 15 × transport_capacity_gap_ratio
  + 10 × weather_disruption_score
  + 10 × estimate_uncertainty_score
```

Definitions:

```text
supply_demand_gap_ratio =
max(0, total_supply - compatible_demand) / max(total_supply, 1)

harvest_concentration_ratio =
largest_single_day_supply / max(total_supply, 1)

transport_capacity_gap_ratio =
sum(max(0, daily_supply - daily_transport_capacity))
/ max(total_supply, 1)

weather_disruption_score =
average normalized disruption score for available forecast dates;
0 when unavailable, with an explicit warning

estimate_uncertainty_score =
weighted average of:
HIGH = 0.0
MEDIUM = 0.5
LOW = 1.0
```

Risk levels:

```text
0–24.99   LOW
25–49.99  MEDIUM
50–74.99  HIGH
75–100    CRITICAL
```

### Internal contract — optimizer result

```json
{
  "status": "OPTIMAL",
  "objective_value": 1432.8,
  "allocations": [
    {
      "harvest_batch_id": "uuid",
      "buyer_demand_id": "uuid",
      "delivery_date": "2026-07-18",
      "quantity_kg": 250.0,
      "reason_codes": [
        "GRADE_COMPATIBLE",
        "DEADLINE_FEASIBLE",
        "SHORT_DISTANCE"
      ]
    }
  ],
  "allocated_kg": 250.0,
  "unallocated_kg": 250.0,
  "unmet_demand_kg": 50.0,
  "warnings": []
}
```

### Optimizer constraints

For each decision variable representing kilograms from a batch to a demand on a delivery date:

1. Allocation must be non-negative.
2. Total allocated from a batch cannot exceed batch quantity.
3. Total allocated to a demand cannot exceed requested quantity.
4. Batch grade must be accepted by the demand.
5. Delivery date must be on or after harvest date.
6. Delivery date must be on or before buyer deadline.
7. Total allocation on a date cannot exceed that date's transport capacity.
8. Cancelled batches, closed demands, and inactive buyers are excluded.

### Optimizer objective order

The implementation uses one linear objective with clearly documented penalties:

1. Strongly penalize unallocated supply.
2. Penalize unmet high-priority demand.
3. Penalize later delivery for urgent batches.
4. Penalize longer distance.
5. Do not include speculative future prices in the objective.

If `linprog` fails, a deterministic greedy fallback may allocate urgent compatible batches to the earliest-deadline demand while respecting capacity. The result must be labeled `FEASIBLE_FALLBACK`, not `OPTIMAL`.

---

## 8. Non-Functional Requirements

### Scale

The v1 prototype must support:

- 1 cooperative.
- 1 commodity.
- Up to 30 active farmers in the seeded demo.
- Up to 1,000 stored harvest batches.
- Up to 100 buyers.
- Up to 500 open buyer-demand records.
- Up to 14 days of active planning data.
- Up to 5,000 optimizer decision variables in one run.

No concurrency guarantee is required beyond a small public hackathon demo. The application should warn that concurrent edits from several browser sessions may overwrite assumptions and are not production-safe.

### Offline behavior

When running locally without internet:

- Harvest CRUD works.
- Buyer and demand CRUD works.
- Distribution-capacity editing works.
- Risk calculation works.
- Optimization works.
- Scenario comparison works.
- The application uses cached weather when available.
- If no weather is available, weather contributes zero points and the UI displays `Cuaca tidak tersedia`.

The deployed cloud version may hibernate or restart. Canonical demo data must be recoverable from seed files.

### Performance

Measured on the seeded demo dataset:

- Initial Radar render: under 2 seconds, excluding a first cold deployment start.
- Risk calculation: under 500 ms.
- Optimization run: under 3 seconds for the declared v1 scale.
- CSV validation and preview: under 2 seconds for 1,000 rows.
- BMKG request timeout: 3 seconds.
- No external request may execute on every Streamlit widget rerun when cached data is still valid.

### Reliability

- Database initialization must be idempotent.
- A failed analysis must not delete the last successful analysis.
- Weather failure must not fail the application.
- Resetting demo data requires confirmation.
- All write operations use transactions.
- CSV import is atomic by default.
- Generated SQLite files and weather caches are not committed to version control.

### Security and privacy

- No authentication in v1.
- Only simulated or non-sensitive demo data may be deployed publicly.
- Do not store NIK, phone number, bank information, credentials, or exact household addresses.
- Validate all input server-side through Pydantic.
- Use parameterized SQL only.
- Never construct SQL with user-supplied string interpolation.
- Secrets must not appear in source, logs, screenshots, fixtures, or committed files.
- Error messages shown to users must not expose stack traces or file-system paths.

### Accessibility, bilingual UX, and responsiveness

- Default UI language is Bahasa Indonesia.
- English is complete, not partial.
- Language preference persists for the active session.
- Primary target is a 1366×768 judging laptop.
- The layout remains usable on tablet and mobile widths.
- KPI cards stack on narrow screens.
- Scenario comparison stacks vertically on mobile.

- Do not communicate risk through color alone; always pair color with text and iconography.
- All form controls have visible labels.
- Tables remain understandable without hover.
- Minimum body-text size: 14 px equivalent.
- Primary actions use explicit verbs.
- Technical solver terminology is confined to an expandable technical-details section.
- The interface must be usable with keyboard navigation to the extent supported by Streamlit.

### Data provenance

Every analytical screen must distinguish:

- `Simulasi` for seeded or manually created demo data.
- `BMKG Live` for live weather.
- `Cache BMKG` with timestamp.
- `Estimasi` for potential impact metrics.

The UI must never imply that simulated allocations were executed in the real world.

---

## 9. Edge Cases & Error States

### Data availability

- **No harvest batches:** Show zero-state guidance; do not calculate a misleading low-risk score.
- **Harvest exists but no buyer demand:** Show high absorption gap, explain that no confirmed demand is available, and allow risk analysis without optimization.
- **Buyer demand exceeds supply:** Allocate available supply; show unmet demand without calling it surplus.
- **No distribution-capacity record:** Treat missing capacity as zero and show a blocking warning before optimization.
- **All capacity is zero:** Risk analysis still runs; optimizer returns no allocations and explains the capacity constraint.
- **No compatible buyer grade:** Keep harvest unallocated and explain grade incompatibility.
- **All harvest is outside the selected horizon:** Show an empty-period state rather than a global zero.
- **Cancelled batch:** Exclude it from new analysis but retain it in historical snapshots.
- **Closed demand:** Exclude it from new analysis.

### Input validation

- Reject zero, negative, NaN, or infinite quantities.
- Reject invalid dates and deadlines.
- Reject harvest dates after buyer deadlines during manual allocation.
- Reject an empty accepted-grade set.
- Reject distance below 0 or above 1,000 km.
- Normalize decimal separators from valid CSV formats where safe; otherwise report a row error.
- Trim surrounding whitespace.
- Do not silently coerce unknown enum values.
- Detect duplicate CSV rows using a deterministic import fingerprint.
- Do not partially insert a CSV unless the operator explicitly chooses `Impor baris valid saja`.

### Weather

- **Timeout:** Use newest cache.
- **HTTP error:** Use newest cache.
- **Malformed response:** Log the adapter error and use cache.
- **Stale cache:** Display cache age and continue.
- **No cache:** Continue with weather status `UNAVAILABLE`.
- **Forecast does not cover all seven days:** Use weather only for covered dates; do not extrapolate.

### Optimizer

- **No feasible allocation:** Return a valid result with zero or partial allocations and constraint explanations.
- **Solver error:** Run deterministic greedy fallback and label it clearly.
- **Unbounded or malformed model:** Treat as a bug, store a failed run, and show a concise user error.
- **Floating-point residue:** Quantities below 0.001 kg are rounded to zero.
- **Rounding:** Display one decimal kilogram but keep higher precision internally.
- **Scenario input produces no change:** Do not create a duplicate run unless the user explicitly saves it.
- **Canonical data changed after base run:** Mark the base run stale.

### Database and deployment

- **Missing database:** Initialize schema and offer seed loading.
- **Corrupt database:** Do not overwrite automatically; show recovery instructions and allow reset only after confirmation.
- **Database locked:** Retry once with a short bounded delay, then preserve form state and show an error.
- **Cloud restart:** Reinitialize from schema; demo seed remains available.
- **Concurrent edit:** Last-write behavior is acceptable for v1, but updated timestamps must make the overwrite visible.
- **Deployment unavailable:** Localhost and the prerecorded demo remain valid fallbacks.

---

## 10. Acceptance Criteria

### Application shell, workspace, and navigation

- [ ] The app starts with `streamlit run app.py` on Python 3.12 without uncaught exceptions.
- [ ] First initialization offers Demo and Empty choices.
- [ ] Demo choice loads deterministic seeded data.
- [ ] Empty choice loads no operational records.
- [ ] Default language is Bahasa Indonesia.
- [ ] `ID | EN` changes all user-facing application text.
- [ ] Language selection persists for the active browser session.
- [ ] Indonesian product title is `MimpiTani`.
- [ ] English product title is `MimpiTani (Farmers' Dream)`.
- [ ] The sidebar exposes exactly four primary screens in both languages.
- [ ] The UI clearly labels the project as a prototype using simulated operational data.
- [ ] Translation dictionaries contain identical key sets.

### Visual system

- [ ] Primary green is `#145319`.
- [ ] Secondary green is `#388E3C`.
- [ ] Warning orange is `#D97706`.
- [ ] App background is `#F1F5F0`.
- [ ] Card background is `#FFFFFF`.
- [ ] Primary text is `#1A2E1A`.
- [ ] Risk states include text in addition to color.
- [ ] The primary workflow is usable at 1366×768.
- [ ] The four primary screens remain usable at tablet and mobile widths.

### Database and seed

- [ ] Starting with no database creates all tables idempotently.
- [ ] Loading the demo seed creates the cooperative profile, farmers, harvest batches, buyers, demands, and capacity records.
- [ ] Reset requires explicit confirmation.
- [ ] Reset produces the same deterministic seeded records and metrics each time.
- [ ] No generated `.db` file is tracked by Git.

### Harvest management

- [ ] A valid manual harvest record can be created and appears in the table and Radar totals.
- [ ] An existing planned harvest can be edited.
- [ ] Cancelling a harvest removes it from current analysis without deleting historical records.
- [ ] Invalid quantities, grades, confidence values, and dates are rejected with field-level messages.
- [ ] A valid CSV of up to 1,000 rows can be previewed and imported.
- [ ] Invalid CSV rows are reported with row number, field, and reason.
- [ ] Duplicate CSV rows are not silently inserted.

### Buyer-demand management

- [ ] A buyer can be created with name, channel, location, and distance.
- [ ] A demand can be created with quantity, deadline, priority, and at least one accepted grade.
- [ ] A demand can be closed and is excluded from new analysis.
- [ ] Grade compatibility is visible before optimization.
- [ ] Invalid quantity, distance, deadline, and grade input is rejected.

### Distribution capacity

- [ ] The operator can enter aggregate capacity for each day in the seven-day horizon.
- [ ] Missing capacity dates are visibly flagged.
- [ ] Missing capacity is treated as zero by the optimizer.
- [ ] Capacity changes affect a subsequent optimization result.

### Radar

- [ ] The Radar shows total supply, compatible demand, potential surplus, operationally constrained surplus, and risk level.
- [ ] The daily chart shows supply, demand, and transport capacity for the selected horizon.
- [ ] The highest-risk date is identified when data exists.
- [ ] With no harvest data, the Radar displays an empty state rather than a risk score.
- [ ] The Radar displays data-source status and timestamps.

### Risk engine

- [ ] Identical input produces identical score, level, critical dates, and factor breakdown.
- [ ] Each factor's weighted points sum to the final score within floating-point tolerance.
- [ ] Scores are clamped to 0–100.
- [ ] Threshold boundaries map correctly to Low, Medium, High, and Critical.
- [ ] Missing weather does not crash calculation and produces an explicit warning.
- [ ] Plain-language explanations identify at least the top three non-zero factors in the selected language.

### BMKG integration

- [ ] A valid administrative code can retrieve and normalize official BMKG data.
- [ ] The application visibly credits BMKG.
- [ ] A request timeout falls back to cache.
- [ ] Malformed live data falls back to cache.
- [ ] When neither live nor cached data exists, core analysis still completes.
- [ ] Tests do not make live BMKG requests.

### Allocation optimizer

- [ ] A batch can be split across multiple compatible buyer demands.
- [ ] No batch is overallocated.
- [ ] No demand is overfulfilled.
- [ ] No allocation violates accepted grade.
- [ ] No allocation is delivered before harvest or after deadline.
- [ ] Daily allocation never exceeds transport capacity.
- [ ] The result exposes allocated kilograms, unallocated kilograms, unmet demand, and solver status.
- [ ] A controlled solver failure invokes the greedy fallback and marks the result `FEASIBLE_FALLBACK`.
- [ ] Results marked `OPTIMAL` originate only from a successful optimizer result.

### Scenario simulation

- [ ] A temporary buyer-demand increase can be simulated without modifying canonical records.
- [ ] A temporary capacity change can be simulated without modifying canonical records.
- [ ] A temporary harvest-date change can be simulated without modifying canonical records.
- [ ] Before and after metrics are displayed side by side.
- [ ] Saving a scenario creates an immutable AnalysisRun linked to its base run.
- [ ] A scenario with no effective change is identified.

### Error handling and accessibility

- [ ] User-facing errors contain an actionable message and no stack trace.
- [ ] Form input remains available after a recoverable database or network error.
- [ ] Risk is communicated with text in addition to color.
- [ ] Every input has a visible label.
- [ ] Empty, loading, success, partial-data, and error states exist for each primary screen.
- [ ] The complete seeded demo can be performed without internet using cached or unavailable weather mode.

### Performance and quality

- [ ] Risk calculation meets the target on seeded data.
- [ ] Optimization completes within 3 seconds at the declared v1 scale.
- [ ] `pytest` passes.
- [ ] `ruff check .` passes.
- [ ] `ruff format --check .` passes.
- [ ] The deployed app starts from a clean Git checkout using only documented commands.

---

## 11. Build Order

Each phase must be independently verifiable. Do not start the next phase until the current phase's tests and acceptance criteria pass.

### Phase 0 — Repository skeleton and deterministic configuration

- Create folder structure.
- Pin dependencies.
- Configure Ruff and pytest.
- Add app configuration, timezone, enums, and constants.
- Add locked theme tokens and bilingual translation skeleton.
- Add welcome choice and empty Streamlit navigation.
- Add `.gitignore`.
- Verification: app starts and all four screens render placeholders.

### Phase 1 — Data contracts, SQLite schema, repositories, and demo seed

- Implement Pydantic domain models.
- Implement idempotent schema initialization.
- Implement parameterized repository methods.
- Implement seed and reset behavior.
- Implement temporary-database tests.
- Verification: seed loads deterministically and CRUD repository tests pass.

### Phase 2 — Harvest management flow

- Build Rencana Panen screen.
- Implement create/edit/cancel.
- Implement CSV template, preview, validation, duplicate detection, and import.
- Verification: manual and CSV acceptance criteria pass.

### Phase 3 — Buyer, demand, and transport-capacity flow

- Build Buyer & Kapasitas screen.
- Implement buyer and demand CRUD.
- Implement accepted-grade handling.
- Implement seven-day capacity editor.
- Verification: compatibility and validation tests pass.

### Phase 4 — Explainable risk engine

- Implement normalized factor calculations.
- Implement score and thresholds.
- Implement critical-date logic.
- Implement plain-language factor explanations.
- Add deterministic unit tests including boundary cases.
- Verification: risk acceptance criteria pass without Streamlit.

### Phase 5 — Allocation optimizer and fallback

- Build optimization input from repository data.
- Implement linear-program matrix construction.
- Implement solver-result normalization.
- Implement deterministic greedy fallback.
- Add invariant tests for all constraints.
- Verification: optimizer tests prove no over-allocation, deadline, grade, or capacity violation.

### Phase 6 — Radar screen

- Add KPI calculations.
- Add daily chart.
- Add data-provenance and partial-data warnings.
- Add latest risk summary and critical dates.
- Verification: seeded Radar matches known fixture totals.

### Phase 7 — Analysis and scenario simulation

- Build analysis-run persistence.
- Build allocation and exception views.
- Implement temporary scenario changes.
- Implement before/after comparison and saved snapshots.
- Verification: scenarios change results without changing canonical records.

### Phase 8 — BMKG adapter and offline fallback

- Implement external adapter.
- Implement normalization.
- Implement cache read/write.
- Add live/cache/unavailable statuses.
- Mock all network behavior in tests.
- Verification: timeout, malformed response, stale cache, and no-cache tests pass.

### Phase 9 — UX polish, accessibility, and demo hardening

- Implement all empty/loading/error states.
- Verify complete Bahasa Indonesia and English labels.
- Verify locked visual color tokens and responsive states.
- Verify source labels and disclaimers.
- Test 1366×768 layout.
- Test full demo with and without internet.
- Record known limitations.
- Verification: manual demo checklist passes twice from a fresh reset.

### Phase 10 — Deployment and submission freeze

- Deploy to Streamlit Community Cloud.
- Verify clean install from GitHub.
- Remove secrets and generated files.
- Capture screenshots and demo backup.
- Freeze new features.
- Verification: public URL, local fallback, tests, lint, and demo reset all work.
