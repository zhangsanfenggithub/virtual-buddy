# Virtual Buddy

A desktop health companion system — a **3D desktop pet** that reacts in real time to a **simulated T1D patient's blood glucose** driven by a **Bayesian network meal prediction model**.

---

## Architecture

```
┌──────────────────────┐         WebSocket (ws://localhost:8000/ws)
│   visual-project/     │◄────────── JSON SimState ───────────  ┌──────────────────────┐
│  Electron + Vue 3     │                                         │   rust-backend/      │
│  3D Desktop Pet       │─── REST (localhost:8000) ──────►       │   Rust + Axum        │
│                       │    PATCH /config                       │   HTTP + WS server   │
└──────────────────────┘                                         └──────────┬───────────┘
                                                                           │
                                                                  stdin JSON│ stdout JSON
                                                                           │
                                                                 ┌──────────▼───────────┐
                                                                 │   py-project/         │
                                                                 │   Python child process │
                                                                 │   bridge.py            │
                                                                 │   (simulation + model) │
                                                                 └───────────────────────┘
```

| Module | Language | Role |
|--------|----------|------|
| **py-project/** | Python | Simulation engine: T1D blood glucose (`simglucose`), Bayesian meal prediction (`pgmpy`), threshold alerts. Runs as child process, driven via stdin/stdout JSON. |
| **rust-backend/** | Rust + Axum | HTTP REST + WebSocket API server. Orchestrates the Python process. Single async broadcast loop. |
| **visual-project/** | Electron + Vue 3 + TresJS | 3D desktop pet. Connects to rust-backend via WebSocket. Zero business logic. Fork of [zlmica/3d-desktop-pet](https://github.com/zlmica/3d-desktop-pet). |

---

## Prerequisites

| Module | Requirement |
|--------|-------------|
| **py-project** | Python 3.9+ (tested 3.12–3.13), pip |
| **rust-backend** | Rust ≥ 1.75, Cargo (install via [rustup.rs](https://rustup.rs)) |
| **visual-project** | Node.js 18+, npm |

---

## Quick Start

### 1. Clone

```bash
git clone <your-repo-url> virtual-buddy
cd virtual-buddy
```

### 2. Train the model + install Python deps (one-time)

```bash
cd py-project/
pip install -r requirements.txt
python meal_model/train.py
# → creates meal_model/model.pkl + training metrics
```

### 3. Start the Rust backend

```bash
cd rust-backend/
cargo run
# → Rust server on http://localhost:8000, Python child spawned automatically
```

### 4. Start the 3D pet (separate terminal)

```bash
cd visual-project/
npm install
npm run dev
```

A transparent 3D pet window appears at the bottom-right of your screen. Right-click for the context menu.

### Optional: Offline simulation test (no server needed)

```bash
cd py-project/
python run_simulation.py    # 288 steps, 24h, stdout output
```

---

## Development Status

| Phase | Status |
|-------|--------|
| Phase 1 — Backend Simulation Core | ✅ Complete |
| Phase 2R — Rust Backend (Axum + child process) | ✅ Complete |
| Phase 3 — Frontend Glucose Integration | ❌ Not started |

See [virtual_buddy_complete_plan.md](virtual_buddy_complete_plan.md) for the full task breakdown.

---

## Project Structure

```
virtual-buddy/
├── README.md
├── Progress.md
├── virtual_buddy_complete_plan.md
│
├── py-project/                           # Python simulation core
│   ├── simulation/
│   │   ├── state.py                      # SimState dataclass + to_dict()
│   │   └── engine.py                     # SimulationEngine (T1DSimEnv wrapper)
│   ├── meal_model/
│   │   ├── config.py                     # All hyperparameters
│   │   ├── train.py                      # Train Bayesian network, save model.pkl
│   │   ├── predictor.py                  # MealPredictor (inference wrapper)
│   │   ├── model.pkl                     # Trained model (generated, gitignored)
│   │   └── prediction_mock_dynamic.py    # Original script (reference)
│   ├── alert/
│   │   └── rules.py                      # AlertEngine (low/high/timeout)
│   ├── data/
│   │   └── HUPA0001P.csv                 # Real patient training data
│   ├── deprecated/
│   │   └── main_simglucose.py            # Legacy script (reference)
│   ├── bridge.py                         # stdin/stdout JSON command handler
│   ├── run_simulation.py                 # CLI integration loop
│   └── requirements.txt
│
├── rust-backend/                         # Rust + Axum API server
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs                       # Entrypoint: spawn Python, mount router
│       ├── models.rs                     # SimState, ConfigUpdate structs
│       ├── python.rs                     # Python subprocess manager
│       ├── state.rs                      # Shared AppState (Arc<Mutex<>>)
│       ├── routes_rest.rs                # REST handlers
│       └── routes_ws.rs                  # WebSocket handler
│
└── visual-project/                       # Electron + Vue 3 3D pet
    ├── electron/
    │   ├── main.ts                       # Main process, IPC, sub-windows
    │   ├── preload.ts
    │   └── tray.ts
    ├── src/
    │   ├── composable/                   # useModel, useReminder
    │   ├── components/                   # Pet3D, ContextMenu, Toast, etc.
    │   ├── views/                        # Home, ReminderPopup, TodoView, PetView
    │   ├── router/                       # Vue Router config
    │   └── db/                           # Dexie/IndexedDB storage
    ├── public/
    │   ├── rabbit.glb                    # Animations: Play, Hello
    │   ├── outhere_space_buddy.glb       # Animation: Space Salsa
    │   └── sample.glb
    └── package.json
```

---

## Rust ↔ Python Bridge

The Python process runs as a long-lived child. Rust sends one JSON command per line to stdin, Python writes one JSON response per line to stdout.

```json
→ {"cmd": "step"}
← {"step":1,"sim_time":"00:05","glucose":142.4,"status":"normal",...}

→ {"cmd": "get_state"}
← {"step":0,"sim_time":"00:00","glucose":95.0,...}

→ {"cmd": "config", "low_threshold": 65}
← {"ok": true}

→ {"cmd": "shutdown"}
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/state` | Current SimState JSON |
| `POST` | `/step` | Advance 1 step, return SimState |
| `POST` | `/reset` | Reset simulation to t=0 |
| `PATCH` | `/config` | Update low_threshold / high_threshold / meal_probability_cutoff |
| `WS` | `/ws?speed=N` | Streaming broadcast (default speed=10, interval = 300/N seconds) |

---

## Running the Simulation (Phase 1)

```bash
cd py-project/

# Train the model first (one-time)
python meal_model/train.py

# Run 288 simulation steps (24 hours, 5-min intervals)
python run_simulation.py
```

Output format:

```
[Step   1] 00:05 | Glucose:   95.3 | Status: normal | Meal: None       | Alert: None
[Step  50] 04:10 | Glucose:  110.2 | Status: normal | Meal: 20g CHO    | Alert: None
[Step 213] 17:45 | Glucose:   62.9 | Status: low    | Meal: None       | Alert: low_glucose
...
[Step 288] 00:00 | Glucose:   51.0 | Status: low    | Meal: None       | Alert: low_glucose

Simulation complete. 7 meals injected over 24 hours.
```

### Simulation Configuration

| Parameter | Value |
|-----------|-------|
| Patient | `adult#001` (simglucose built-in) |
| CGM sensor | Dexcom, 5-min intervals |
| Insulin pump | Insulet |
| Controller | Basal-Bolus (`BBController`) |
| Low glucose threshold | < 70 mg/dL (2 consecutive steps) |
| High glucose threshold | > 180 mg/dL (3 consecutive steps) |
| Meal timeout | 6 hours without meal → alert |

---
## Phase 1 — Implementation Logic

This section explains how the three core components (`SimulationEngine`, `MealPredictor`, `AlertEngine`) are designed and how they interact in the simulation loop.

### Overall Data Flow

```
                        ┌──────────────────────┐
                        │    run_simulation.py  │
                        │     (integration)      │
                        └────┬─────┬──────┬─────┘
                 ┌───────────┘     │      └───────────┐
                 ▼                 ▼                  ▼
┌─────────────────────┐  ┌─────────────────┐  ┌───────────────┐
│  SimulationEngine   │  │  MealPredictor  │  │  AlertEngine  │
│  (simglucose env)   │  │  (Bayesian net) │  │  (thresholds) │
└──────────┬──────────┘  └────────┬────────┘  └───────┬───────┘
           │                      │                   │
           ▼                      ▼                   ▼
     T1DSimEnv.step()    pgmpy VariableElimination    counter-based
     BBController.policy     .query() → evidence       state machine
```

### 1. Data Ingestion & Model Training (`train.py`)

Real patient data (`HUPA0001P.csv`) with columns: `time`, `glucose`, `heart_rate`, `steps`, `basal_rate`, `bolus_volume_delivered`, `carb_input`.

**Preprocessing pipeline:**

| Step | Operation | Purpose |
|------|-----------|---------|
| 1 | `pd.read_csv(sep=";")` | Load semicolon-separated time series |
| 2 | `dt.hour * 60 + dt.minute // 5` → `TC_5m` | Map timestamp to 5-minute time bin (0–287) |
| 3 | `pd.cut(glucose, [0, 70, 140, ∞])` → `GL_State` | Discretize glucose into 3 levels |
| 4 | Track `last_meal_time` via `ffill()` | Compute `TP_State` = time since last meal in 5-min steps |
| 5 | Track `next_meal_time` via `bfill()` | Compute `TUN_State` = time until next meal |
| 6 | Lag `GL_State` by 1 step → `GL_State_Prev` | Enable autoregressive glucose modeling |

**Bayesian network structure** (fixed, not learned from data):

```python
model = DiscreteBayesianNetwork([
    ("GL_State_Prev", "GL_State"),  # glucose autocorrelation
    ("TC_5m",         "TUN_State"), # time of day → meal timing
    ("GL_State",      "TUN_State"), # current glucose → meal urgency
    ("TP_State",      "TUN_State"), # fasting duration → meal likelihood
    ("TUN_State",     "SN_State"),  # when to eat → how much to eat
])
model.fit(train_df, estimator=MaximumLikelihoodEstimator)
```

**Design rationale:**
- The edges are chosen to capture **meal timing causality**: time of day sets the rhythm, fasting duration drives hunger, glucose level signals energy need. The model predicts two things simultaneously: *when* the next meal occurs (`TUN_State`) and *how large* it is (`SN_State`).
- `MaximumLikelihoodEstimator` uses simple conditional probability tables (CPTs) — computationally light, interpretable, and avoids overfitting from Bayesian priors on small datasets.

### 2. Simulation Engine (`engine.py`)

Wraps `simglucose`'s `T1DSimEnv` to provide a clean step-based interface.

**How `step()` works internally:**

1. Read `_pending_cho` — if a meal was scheduled this step, append it to `CustomScenario` dynamically
2. Call `BBController.policy()` — compute insulin dose (basal + bolus) from current observation
3. Call `env.step(action)` — advance the physiological model by one CGM interval (5 min)
4. Read CGM value from observation, push to rolling `glucose_history` (last 50 readings)
5. Map glucose to status string (`"normal"` / `"low"` / `"high"`) via threshold comparison
6. Package everything into a `SimState` dataclass and return

**Key design decisions:**
- **Dynamic meal injection**: Meals are appended to `CustomScenario.scenario` at runtime via `inject_meal()` → `_pending_cho`. The scenario's `get_action()` method matches by wall-clock time, so meals take effect the same step they're scheduled.
- **CGM sample_time = 5 min**: The default Dexcom CGM runs at 3-min intervals; we override `sensor.sample_time = 5` to match the plan's 5-min step cadence (288 steps = 24 hours).
- **Sensor floor lowered to 20 mg/dL**: Real Dexcom caps at 39 mg/dL (`min` parameter); we lower to 20 for debugging true BG values during deep hypoglycemia.
- **Patient `adult#001`**: A built-in simglucose virtual patient with realistic insulin sensitivity and meal response curves.

### 3. Meal Predictor (`predictor.py`)

Bridges the simulation's runtime interface (`sim_time`, `hours_since_last_meal`, `glucose`) with the Bayesian model's feature space (`TC_5m`, `TP_State`, `GL_State`).

**Feature mapping:**

| Runtime input | → | Model feature | Conversion logic |
|---------------|--|---------------|------------------|
| `sim_time` `"14:30"` | → | `TC_5m` = 174 | `(14*60 + 30) // 5 = 174` |
| `hours_since_last_meal` 3.5 | → | `TP_State` = 3 | 210 min → 120–240 bin |
| `glucose` 92.0 | → | `GL_State` = 2 | 70 < 92 ≤ 140 |

**Inference & decision logic:**

1. Build evidence dict `{"TC_5m", "TP_State", "GL_State"}`
2. Query `TUN_State` via `VariableElimination` → get probability distribution `P(meal within 1h, 1–3h, 3h+)`
3. Query `SN_State` → get `P(snack), P(normal meal)`
4. **Dual-threshold decision**: `should_eat = P(within_1h) > 0.55` **OR** `P(within_3h) > 0.75`
5. Sample `suggested_cho` from appropriate distribution (snack: 20–30g, normal: 45–75g)

**Design rationale for dual threshold:**
- Single `P(within_1h) > 0.55` alone produces too few evening meals (training data skews morning-heavy)
- Adding `P(within_3h) > 0.75` as an "any meal soon is good" rule prevents prolonged fasting that triggers pathological hypoglycemia
- This is a **pragmatic tuning** decision, not derived from the model structure

### 4. Alert Engine (`rules.py`)

A simple state machine with counters — no ML, no prediction, purely threshold-based by design constraint.

**State tracking:**

```
_low_count:   consecutive steps where glucose < 70
_high_count:  consecutive steps where glucose > 180
_last_meal_step: step number of most recent meal
```

**Alert priority order** (only one alert per step):

| Priority | Alert | Trigger |
|----------|-------|---------|
| 1 | `"low_glucose"` | `glucose < 70` for **2 consecutive steps** (10 min) |
| 2 | `"high_glucose"` | `glucose > 180` for **3 consecutive steps** (15 min) |
| 3 | `"timeout_reminder"` | `(current_step - last_meal_step) × 5 min > 360 min` |

**Design rationale for hysteresis:**
- Requiring consecutive steps prevents spurious alerts from a single noisy CGM reading
- Different thresholds for low (2) vs high (3) reflect clinical asymmetry: hypoglycemia is more urgent
- Counters reset to 0 the moment glucose crosses back into the normal range — this prevents stale accumulated state

### 5. Integration Loop (`run_simulation.py`)

Ties all three components together in a main loop:

```
for each step (0 → 287):
    1. predictor.predict(sim_time, hours_since_last_meal, glucose)
       → returns {should_eat, suggested_cho}

    2. if should_eat:
         engine.inject_meal(suggested_cho)

    3. if glucose_dangerous and predictor_did_not_act:
         engine.inject_meal(rescue_dose)      # safety net

    4. state = engine.step()                  # advance 5 min

    5. alert_engine.record_meal(step) if meal_event
       state.alert = alert_engine.evaluate(state)

    6. print formatted line
```

**Rescue meal rules (safety net):**

| Condition | Dose | Rationale |
|-----------|------|-----------|
| `glucose < 70` **and** `> 3h since last meal` | 30g CHO | Proactive — prevent slide into severe hypoglycemia |
| `glucose < 55` **and** `> 2h since last meal` | 45g CHO | Reactive — aggressive correction for dangerous lows |

These rescue rules exist because the Bayesian model is trained on one patient's eating pattern and doesn't generalize to all eating schedules. In a real deployment, these would be replaced by better training data.

### Component Dependencies

```
SimState (dataclass)
    ├── SimulationEngine.step() → returns SimState
    ├── AlertEngine.evaluate(SimState) → returns alert string
    └── run_simulation.py passes SimState fields to print

MealPredictor
    └── run_simulation.py calls predict(sim_time, hours, glucose)
        └── returns dict → engine.inject_meal(cho)

AlertEngine
    └── run_simulation.py calls evaluate(state)
        └── returns str → written into state.alert → printed
```

---
## Bayesian Model

Trained on real patient data (`HUPA0001P.csv`) with `MaximumLikelihoodEstimator`:

```
GL_State_Prev ──→ GL_State
TC_5m ──────────→ TUN_State ──→ SN_State
GL_State ───────→ TUN_State
TP_State ───────→ TUN_State
```

| Node | Meaning | Bins |
|------|---------|------|
| `TC_5m` | Time of day (5-min bins) | 0–287 |
| `GL_State` | Current glucose | < 70 / 70–140 / 140+ mg/dL |
| `TP_State` | Time since last meal | < 30m / 30m–2h / 2–4h / 4h+ |
| `TUN_State` | Time until next meal | < 1h / 1–3h / 3h+ |
| `SN_State` | Next meal size | snack / normal |

---

## Frontend Features (visual-project)

- 🐰 3D pet models (rabbit, space buddy, sample) — swappable via right-click menu
- 🎮 Click interaction triggers animation (`Hello` / `Space Salsa`)
- 📝 Task management sub-window
- ⏰ Reminder system with popup notifications and Dexie/IndexedDB persistence
- 🖥️ Transparent always-on-top frameless window, draggable
- 🧭 System tray integration

### Frontend Dev Commands

```bash
cd visual-project/
npm run dev          # Dev mode with HMR
npm run build        # Production build
npm run build:win    # Windows installer
npm run build:mac    # macOS app
npm run format       # Prettier formatting
```

---

## Known Limitations

1. **Evening hypoglycemia**: The Bayesian model predicts fewer evening meals. Rescue rules help but glucose can still dip below target.
2. **CGM sensor floor**: Dexcom CGM reports minimum 39 mg/dL by default (lowered to 20 in engine for debugging).
3. **Single patient**: Model trained on one patient's data; cross-patient generalization not tested.
4. **Frontend not yet connected**: Phase 3 (glucose integration into the 3D pet) is not yet built.

---

## Next Steps

1. **Phase 3**: Add glucose features to visual-project (`useGlucose.ts`, `GlucoseOverlay.vue`, `GlucoseDashboard.vue`)
2. Connect Electron frontend to Rust backend via WebSocket

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Simulation | `simglucose` (T1DSimEnv + BBController) |
| ML / Prediction | `pgmpy` (DiscreteBayesianNetwork, MaximumLikelihoodEstimator, VariableElimination) |
| Data | `pandas`, `numpy` |
| API server | `Rust`, `Axum`, `tokio`, `serde`, `tower-http` |
| Desktop app | `Electron`, `Vue 3`, `TypeScript` |
| 3D rendering | `TresJS` (Three.js for Vue), `@tresjs/cientos` |
| Styling | `Tailwind CSS` |
| Storage | `Dexie.js` (IndexedDB) |
