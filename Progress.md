# Virtual Buddy — Progress

A desktop health companion that combines a **Bayesian network meal predictor**, **T1D blood glucose simulation**, and a **3D desktop pet avatar** (Electron + Vue 3 + TresJS). The avatar reacts in real time to the simulated patient's blood glucose state.

---

## Project Structure

```
virtual-buddy/
├── py-project/              # Python backend — simulation + prediction
│   ├── simulation/          # SimState, SimulationEngine (T1DSimEnv wrapper)
│   ├── meal_model/          # Bayesian network trainer + predictor
│   ├── alert/               # AlertEngine (threshold-based alerts)
│   ├── prediction/          # Legacy scripts (reference only)
│   ├── data/                # Patient data (HUPA0001P.csv)
│   ├── run_simulation.py    # CLI integration loop
│   └── requirements.txt
│
├── visual-project/          # Electron + Vue 3 frontend (3D desktop pet)
│   ├── electron/            # Main process, tray, IPC
│   ├── src/
│   │   ├── composable/      # useModel, useReminder
│   │   ├── components/      # Pet3D, ContextMenu, Toast, etc.
│   │   ├── views/           # Home, ReminderPopup, TodoView, PetView
│   │   ├── router/          # Vue Router (hash-based)
│   │   └── db/              # Dexie/IndexedDB reminder storage
│   └── public/              # GLB models (rabbit, space buddy, sample)
│
├── virtual_buddy_complete_plan.md   # Full development plan
└── Progress.md                      # This file
```

---

## Current Status (2026-04-28)

### Phase 1 — Backend Simulation Core ✅ COMPLETE

| Task | Status |
|------|--------|
| `SimState` dataclass | ✅ [simulation/state.py](file:///d:/Projects%20Python/virtual-buddy/py-project/simulation/state.py) |
| `SimulationEngine` class | ✅ [simulation/engine.py](file:///d:/Projects%20Python/virtual-buddy/py-project/simulation/engine.py) |
| Bayesian network training | ✅ [meal_model/train.py](file:///d:/Projects%20Python/virtual-buddy/py-project/meal_model/train.py) |
| Trained model file | ✅ `meal_model/model.pkl` (generated from HUPA0001P.csv) |
| `MealPredictor` class | ✅ [meal_model/predictor.py](file:///d:/Projects%20Python/virtual-buddy/py-project/meal_model/predictor.py) |
| `AlertEngine` class | ✅ [alert/rules.py](file:///d:/Projects%20Python/virtual-buddy/py-project/alert/rules.py) |
| CLI integration loop | ✅ [run_simulation.py](file:///d:/Projects%20Python/virtual-buddy/py-project/run_simulation.py) |
| `requirements.txt` | ✅ [requirements.txt](file:///d:/Projects%20Python/virtual-buddy/py-project/requirements.txt) |

**How to run:**

```bash
cd py-project/
pip install -r requirements.txt
python meal_model/train.py        # train and save model.pkl
python run_simulation.py          # 288 steps (24h), prints glucose, meals, alerts
```

**Key details:**
- T1D simulation via `simglucose` (`T1DSimEnv` + `BBController`)
- Patient: `adult#001`, Dexcom CGM (5-min intervals), Insulet pump
- Bayesian network: `DiscreteBayesianNetwork` with 6 nodes (`GL_State_Prev → GL_State`, `TC_5m + GL_State + TP_State → TUN_State → SN_State`), trained on real patient data
- Alerts: `low_glucose` (2 consecutive < 70 mg/dL), `high_glucose` (3 consecutive > 180 mg/dL), `timeout_reminder` (6h without meal)
- Rescue meals: auto-injected when glucose drops (30g at < 70, 45g at < 55)

**Verification:** 288 steps run without error, glucose stays within plan boundaries, meals fire at predicted times.

---

### Phase 2 — FastAPI Server ✅ COMPLETE

| Task | Status |
|------|--------|
| `main.py` (REST + WebSocket) | ✅ [main.py](file:///d:/Projects%20Python/virtual-buddy/py-project/main.py) |
| `POST /step`, `POST /reset`, `GET /state`, `PATCH /config` | ✅ All verified |
| `WS /ws?speed=10` broadcast loop | ✅ Verified: 3 messages received |

**How to run:**

```bash
cd py-project/
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/state` | Current SimState JSON |
| `POST` | `/step` | Advance 1 step, return SimState |
| `POST` | `/reset` | Reset simulation to t=0 |
| `PATCH` | `/config` | Update thresholds (low_threshold, high_threshold, meal_probability_cutoff) |
| `WS` | `/ws?speed=N` | Streaming broadcast (default speed=10) |

---

### Phase 3 — Frontend Glucose Integration ❌ NOT STARTED

| Task | Status |
|------|--------|
| `useGlucose.ts` (WebSocket singleton) | ❌ Not created |
| `GlucoseOverlay.vue` (glucose badge + tint) | ❌ Not created |
| `GlucoseDashboard.vue` (sub-window chart + config) | ❌ Not created |
| Modify `useModel.ts` (glucoseStatus + applyGlucoseState) | ❌ Not done |
| Modify `Home.vue` (WebSocket lifecycle + overlay) | ❌ Not done |
| Modify `ContextMenu.vue` (glucose menu item) | ❌ Not done |
| Modify `router/index.ts` (/glucose route) | ❌ Not done |
| Modify `electron/main.ts` (glucose-alert IPC) | ❌ Not done |
| Modify `ReminderPopup.vue` (glucose alert card) | ❌ Not done |

**Current visual-project state:** 3D desktop pet app fully functional — transparent always-on-top window, 3 GLB models (space buddy, rabbit, sample), animation control, reminder popup system, sub-window infrastructure. All glucose features are yet to be added.

---

## Bayesian Model Architecture

```
GL_State_Prev ──→ GL_State
TC_5m ──────────→ TUN_State ──→ SN_State
GL_State ───────→ TUN_State
TP_State ───────→ TUN_State
```

| Node | Meaning | Values |
|------|---------|--------|
| `GL_State_Prev` | Previous glucose state | 1: < 70, 2: 70–140, 3: 140+ mg/dL |
| `TC_5m` | Time of day (5-min bins) | 0–287 |
| `GL_State` | Current glucose state | 1: < 70, 2: 70–140, 3: 140+ mg/dL |
| `TP_State` | Time since last meal | 1: < 30m, 2: 30m–2h, 3: 2–4h, 4: 4h+ |
| `TUN_State` | Time until next meal | 1: < 1h, 2: 1–3h, 3: 3h+ |
| `SN_State` | Next meal size | 1: snack (≤ 3 units), 2: normal meal (> 3 units) |

---

## Known Limitations

1. **Evening hypoglycemia**: The Bayesian model (trained on `HUPA0001P.csv`) predicts fewer evening meals. Rescue meal rules help but glucose can still dip. More training data with evening meal patterns would improve this.
2. **CGM sensor floor**: Dexcom CGM reports a minimum of 39 mg/dL by default. We lowered this to 20 in the engine for debugging. Real CGMs report "LOW" below 40.
3. **Patient specificity**: The model is trained on a single patient's data. Cross-patient generalization is not tested.

---

## Next Steps

1. **Phase 2**: Build `main.py` — FastAPI server with REST endpoints and WebSocket broadcast
2. **Phase 3**: Integrate glucose features into the 3D desktop pet frontend
3. **Data improvement**: Add more evening/night meal patterns to training data
4. **Cross-validation**: Formal evaluation of model accuracy across time splits
