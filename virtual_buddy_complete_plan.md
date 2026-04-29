# Virtual Buddy — Complete Agent Development Plan

---

## Project Overview

Build a desktop health companion with **three** modules:

| Module | Language | Role |
|--------|----------|------|
| **py-project** | Python | Simulation engine: T1D patient (`simglucose`), Bayesian meal prediction (`pgmpy`), threshold alerts. Runs as a **child process**, driven via stdin/stdout JSON commands. No web server. |
| **rust-backend** | Rust + Axum | HTTP REST + WebSocket API server. Orchestrates the Python child process. Exposes `/step`, `/reset`, `/state`, `/config`, `/ws` to the frontend. |
| **visual-project** | Electron + Vue 3 + TresJS | 3D desktop pet. Connects to rust-backend via WebSocket. Zero business logic. Fork of `zlmica/3d-desktop-pet`. |

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

---

## Current Status (as of 2026-04-28)

### ✅ Phase 1 + Phase 2 (Python) — COMPLETE

| Item | File | Status |
|------|------|--------|
| SimState dataclass + `to_dict()` | [simulation/state.py](file:///d:/Projects%20Python/virtual-buddy/py-project/simulation/state.py) | ✅ |
| SimulationEngine | [simulation/engine.py](file:///d:/Projects%20Python/virtual-buddy/py-project/simulation/engine.py) | ✅ |
| Bayesian training + CV | [meal_model/train.py](file:///d:/Projects%20Python/virtual-buddy/py-project/meal_model/train.py) | ✅ |
| model.pkl | [meal_model/model.pkl](file:///d:/Projects%20Python/virtual-buddy/py-project/meal_model/model.pkl) | ✅ |
| MealPredictor | [meal_model/predictor.py](file:///d:/Projects%20Python/virtual-buddy/py-project/meal_model/predictor.py) | ✅ |
| AlertEngine | [alert/rules.py](file:///d:/Projects%20Python/virtual-buddy/py-project/alert/rules.py) | ✅ |
| CLI integration | [run_simulation.py](file:///d:/Projects%20Python/virtual-buddy/py-project/run_simulation.py) | ✅ |
| Hyperparameter config | [meal_model/config.py](file:///d:/Projects%20Python/virtual-buddy/py-project/meal_model/config.py) | ✅ |
| requirements.txt | [requirements.txt](file:///d:/Projects%20Python/virtual-buddy/py-project/requirements.txt) | ✅ |
| FastAPI server (Python) | [main.py](file:///d:/Projects%20Python/virtual-buddy/py-project/main.py) | ✅ — **will be deleted** (replaced by Rust) |

### ✅ visual-project — Base pet app complete, glucose features pending

| Item | Status |
|------|--------|
| 3D pet (3 GLB models, animations, always-on-top) | ✅ |
| Reminder system (Dexie, popup) | ✅ |
| Sub-window infra (hash routing) | ✅ |
| useGlucose.ts, GlucoseOverlay.vue, GlucoseDashboard.vue | ❌ |
| File modifications (6 files) | ❌ |

### ❌ Was Not Started — Rust Backend

| Item | Phase |
|------|-------|
| `bridge.py` — Python stdin/stdout command handler | Phase 2R |
| `rust-backend/` — Cargo project (Axum + tokio + serde) | Phase 2R |
| REST endpoints (`/step`, `/reset`, `/state`, `/config`) | Phase 2R |
| WebSocket `/ws?speed=N` broadcast loop | Phase 2R |
| Python subprocess spawner / lifecycle manager | Phase 2R |
| All frontend glucose features | Phase 3 |

---

## Global Constraints

- Do NOT implement: linear glucose prediction curves, insulin injection UI, real CGM device integration, multi-user/auth systems.
- Alert system uses simple threshold rules only. No predictive modeling of future glucose values.
- visual-project has zero business logic. All state is derived from backend WebSocket pushes.
- All blood glucose values are in **mg/dL**.
- Frontend animations: `'Play'` (idle loop), `'Hello'` (one-shot). For `outhere_space_buddy.glb` use `'Space Salsa'`.
- **Python keeps ALL glucose/simulation/prediction code.** Rust handles only HTTP + WebSocket + process orchestration.

---

## Repository Structure (after Phase 2R)

```
virtual-buddy/
├── py-project/                        # Python simulation core (NO web server)
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── state.py
│   │   └── engine.py
│   ├── meal_model/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── train.py
│   │   ├── predictor.py
│   │   ├── model.pkl
│   │   ├── training_log.txt
│   │   ├── training_metrics.json
│   │   └── prediction_mock_dynamic.py   # preserved as reference
│   ├── alert/
│   │   ├── __init__.py
│   │   └── rules.py
│   ├── data/
│   │   └── HUPA0001P.csv
│   ├── deprecated/
│   │   └── main_simglucose.py           # reference only
│   ├── bridge.py                        # ❌ CREATE — stdin/stdout JSON command loop
│   ├── run_simulation.py                # standalone CLI test (keep)
│   ├── main.py                          # ❌ REMOVE — replaced by Rust
│   ├── .gitignore
│   └── requirements.txt
│
├── rust-backend/                       # ❌ CREATE — Rust + Axum server
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs
│       ├── models.rs                   # SimState, ConfigUpdate structs
│       ├── python.rs                   # Python subprocess manager
│       ├── state.rs                    # Shared AppState (Arc<Mutex<>>)
│       ├── routes_rest.rs              # REST handlers
│       └── routes_ws.rs                # WebSocket handler
│
├── visual-project/                     # Electron + Vue 3 frontend
│   └── (unchanged — see Phase 3)
│
├── README.md
├── Progress.md
└── virtual_buddy_complete_plan.md      # This file
```

---

## Architecture: Rust ↔ Python Bridge

### Why stdin/stdout JSON?

1. **Zero network dependency** — local process IPC, no ports
2. **Simple protocol** — no protobuf/schema in Python, just `json.dumps` / `json.loads`
3. **Rust controls lifecycle** — `tokio::process::Command` spawns child, reads line-delimited stdout
4. **Crash resilience** — Rust detects EOF on stdout and can restart the Python process

### Protocol

**Rust → Python (stdin, one JSON per line):**

```json
{"cmd": "step"}
{"cmd": "reset"}
{"cmd": "get_state"}
{"cmd": "shutdown"}
{"cmd": "config", "low_threshold": 65, "high_threshold": 200, "meal_probability_cutoff": 0.6}
```

**Python → Rust (stdout, one JSON per line):**

```json
{"step": 42, "sim_time": "03:30", "glucose": 112.5, "status": "normal", "meal_event": false, "meal_cho": 0, "alert": null, "glucose_history": [108.2, 109.1, 110.4]}
{"ok": true}
```

On `shutdown`, Python does `break` and exits. Rust restarts process if stdout EOF detected.

---

## Phase 2R — Rust Backend (Axum)

**Goal:** Rust server at `localhost:8000` exposing REST + WebSocket. Manages Python child process internally. Frontend connects and receives live [SimState](#simstate-json) JSON.

### Task 2R.0 — Prerequisites

```bash
# Ensure Rust is installed
rustc --version   # ≥ 1.75
cargo --version
```

### Task 2R.1 — Python bridge script

**File:** `py-project/bridge.py` ❌ CREATE

Rewrite the simulation loop from `run_simulation.py` and `main.py` into a stdin/stdout command handler. No FastAPI, no threads, pure blocking I/O.

```python
import sys
import json
import signal
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.engine import SimulationEngine
from meal_model.predictor import MealPredictor
from alert.rules import AlertEngine

_engine = SimulationEngine(patient_name="adult#001")
_predictor = MealPredictor()
_alert_engine = AlertEngine()
_hours_since_last_meal = 0.0


def _simulate_one_step() -> dict:
    global _hours_since_last_meal
    state = _engine.get_state()
    sim_time = state.sim_time if state else "00:00"
    glucose = state.glucose if state else 95.0

    prediction = _predictor.predict(sim_time, _hours_since_last_meal, glucose)
    if prediction["should_eat"]:
        _engine.inject_meal(prediction["suggested_cho"])
    if glucose < 70 and _hours_since_last_meal > 3 and not prediction["should_eat"]:
        _engine.inject_meal(30)
    if glucose < 55 and _hours_since_last_meal > 2:
        _engine.inject_meal(45)

    state = _engine.step()
    if state.meal_event:
        _alert_engine.record_meal(state.step)
        _hours_since_last_meal = 0.0
    else:
        _hours_since_last_meal += 5.0 / 60.0
    state.alert = _alert_engine.evaluate(state)
    return state.to_dict()


def _current_state() -> dict:
    state = _engine.get_state()
    if state is None:
        return {"step": 0, "sim_time": "00:00", "glucose": 95.0, "status": "normal",
                "meal_event": False, "meal_cho": 0, "alert": None, "glucose_history": []}
    return state.to_dict()


HANDLERS = {
    "step":      _simulate_one_step,
    "reset":     lambda: (_engine.reset(), _set_hours(0.0), _current_state())[-1],
    "get_state": _current_state,
}


def _set_hours(h):
    global _hours_since_last_meal
    _hours_since_last_meal = h


def main():
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        cmd = req.get("cmd")
        if cmd == "shutdown":
            break
        if cmd == "config":
            _apply_config(req)
            result = {"ok": True}
        elif cmd in HANDLERS:
            result = HANDLERS[cmd]()
        else:
            continue
        sys.stdout.write(json.dumps(result, default=str) + "\n")
        sys.stdout.flush()


def _apply_config(data: dict):
    if "low_threshold" in data:
        _alert_engine.LOW_THRESHOLD = data["low_threshold"]
    if "high_threshold" in data:
        _alert_engine.HIGH_THRESHOLD = data["high_threshold"]
    if "meal_probability_cutoff" in data:
        _predictor.CUTOFF = data["meal_probability_cutoff"]


if __name__ == "__main__":
    main()
```

**Acceptance test:**

```bash
cd py-project/
echo '{"cmd":"step"}' | python bridge.py
# → {"step":1,"sim_time":"00:05","glucose":142.4,...}
```

---

### Task 2R.2 — Cargo project

```bash
cd virtual-buddy/
cargo init rust-backend
cd rust-backend/
cargo add axum --features ws
cargo add tokio --features full
cargo add serde --features derive
cargo add serde_json
cargo add tower-http --features cors
cargo add tracing tracing-subscriber
cargo add futures-util
```

**File:** `rust-backend/Cargo.toml` ❌ CREATE

```toml
[package]
name = "virtual-buddy-backend"
version = "0.1.0"
edition = "2021"

[dependencies]
axum = { version = "0.8", features = ["ws"] }
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tower-http = { version = "0.6", features = ["cors"] }
tracing = "0.1"
tracing-subscriber = "0.3"
futures-util = "0.3"
```

---

### Task 2R.3 — Data models (`models.rs`)

**File:** `rust-backend/src/models.rs` ❌ CREATE

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SimState {
    pub step: u32,
    pub sim_time: String,
    pub glucose: f64,
    pub status: String,
    pub meal_event: bool,
    pub meal_cho: f64,
    pub alert: Option<String>,
    pub glucose_history: Vec<f64>,
}

#[derive(Debug, Deserialize)]
pub struct ConfigUpdate {
    pub low_threshold: Option<f64>,
    pub high_threshold: Option<f64>,
    pub meal_probability_cutoff: Option<f64>,
}

#[derive(Debug, Serialize)]
pub struct ConfigResponse {
    pub ok: bool,
}
```

---

### Task 2R.4 — Python subprocess manager (`python.rs`)

**File:** `rust-backend/src/python.rs` ❌ CREATE

```rust
use std::process::Stdio;
use std::sync::Arc;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::process::{Child, Command};
use tokio::sync::Mutex;

use crate::models::{ConfigUpdate, SimState};

pub struct PythonBridge {
    child: Child,
    stdin: tokio::process::ChildStdin,
    stdout: BufReader<tokio::process::ChildStdout>,
}

impl PythonBridge {
    pub async fn spawn() -> Self {
        let mut child = Command::new("python")
            .arg("bridge.py")
            .current_dir("../py-project")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()
            .expect("Failed to spawn Python bridge.py");

        let stdin = child.stdin.take().expect("child stdin");
        let stdout = child.stdout.take().expect("child stdout");
        Self { child, stdin, stdout: BufReader::new(stdout) }
    }

    async fn send(&mut self, json: &str) {
        self.stdin.write_all(json.as_bytes()).await.unwrap();
        self.stdin.write_all(b"\n").await.unwrap();
        self.stdin.flush().await.unwrap();
    }

    async fn recv(&mut self) -> Option<String> {
        let mut line = String::new();
        match self.stdout.read_line(&mut line).await {
            Ok(0) | Err(_) => None,
            Ok(_) => Some(line.trim().to_string()),
        }
    }

    pub async fn step(&mut self) -> SimState {
        self.send(r#"{"cmd":"step"}"#).await;
        let resp = self.recv().await.expect("Python process died");
        serde_json::from_str(&resp).expect("invalid SimState JSON")
    }

    pub async fn reset(&mut self) -> SimState {
        self.send(r#"{"cmd":"reset"}"#).await;
        serde_json::from_str(&self.recv().await.unwrap()).unwrap()
    }

    pub async fn get_state(&mut self) -> SimState {
        self.send(r#"{"cmd":"get_state"}"#).await;
        serde_json::from_str(&self.recv().await.unwrap()).unwrap()
    }

    pub async fn update_config(&mut self, config: &ConfigUpdate) {
        let json = serde_json::json!({
            "cmd": "config",
            "low_threshold": config.low_threshold,
            "high_threshold": config.high_threshold,
            "meal_probability_cutoff": config.meal_probability_cutoff,
        });
        self.send(&json.to_string()).await;
        self.recv().await;
    }
}

pub type SharedBridge = Arc<Mutex<PythonBridge>>;
```

---

### Task 2R.5 — Application state (`state.rs`)

**File:** `rust-backend/src/state.rs` ❌ CREATE

```rust
use std::sync::Arc;
use tokio::sync::{Mutex, watch};
use crate::python::PythonBridge;
use crate::models::SimState;

pub struct AppState {
    pub bridge: Arc<Mutex<PythonBridge>>,
    pub tx_state: watch::Sender<Option<SimState>>,
    pub rx_state: watch::Receiver<Option<SimState>>,
}

impl AppState {
    pub fn new(bridge: PythonBridge) -> Self {
        let (tx, rx) = watch::channel(None);
        Self { bridge: Arc::new(Mutex::new(bridge)), tx_state: tx, rx_state: rx }
    }

    pub async fn broadcast_state(&self, state: SimState) {
        let _ = self.tx_state.send(Some(state));
    }
}
```

---

### Task 2R.6 — REST routes (`routes_rest.rs`)

**File:** `rust-backend/src/routes_rest.rs` ❌ CREATE

```rust
use std::sync::Arc;
use axum::{extract::State, Json};

use crate::models::{ConfigUpdate, ConfigResponse, SimState};
use crate::state::AppState;

pub async fn step(State(state): State<Arc<AppState>>) -> Json<SimState> {
    let mut bridge = state.bridge.lock().await;
    let sim = bridge.step().await;
    state.broadcast_state(sim.clone()).await;
    Json(sim)
}

pub async fn reset(State(state): State<Arc<AppState>>) -> Json<SimState> {
    let mut bridge = state.bridge.lock().await;
    let sim = bridge.reset().await;
    state.broadcast_state(sim.clone()).await;
    Json(sim)
}

pub async fn get_state(State(state): State<Arc<AppState>>) -> Json<SimState> {
    let mut bridge = state.bridge.lock().await;
    Json(bridge.get_state().await)
}

pub async fn update_config(
    State(state): State<Arc<AppState>>,
    Json(config): Json<ConfigUpdate>,
) -> Json<ConfigResponse> {
    let mut bridge = state.bridge.lock().await;
    bridge.update_config(&config).await;
    Json(ConfigResponse { ok: true })
}
```

---

### Task 2R.7 — WebSocket handler (`routes_ws.rs`)

**File:** `rust-backend/src/routes_ws.rs` ❌ CREATE

```rust
use std::sync::Arc;
use axum::extract::{ws::{Message, WebSocket}, Query, State, WebSocketUpgrade};
use axum::response::IntoResponse;
use futures_util::{SinkExt, StreamExt};
use serde::Deserialize;
use tokio::time::{interval, Duration};

use crate::state::AppState;

#[derive(Deserialize)]
pub struct WsParams {
    pub speed: Option<f64>,
}

pub async fn ws_handler(
    ws: WebSocketUpgrade,
    State(state): State<Arc<AppState>>,
    Query(params): Query<WsParams>,
) -> impl IntoResponse {
    let speed = params.speed.unwrap_or(10.0);
    let step_ms = ((5.0 * 60.0) / speed * 1000.0) as u64;
    ws.on_upgrade(move |socket| handle_ws(socket, state, step_ms))
}

async fn handle_ws(mut socket: WebSocket, state: Arc<AppState>, step_ms: u64) {
    let mut ticker = interval(Duration::from_millis(step_ms));
    loop {
        tokio::select! {
            _ = ticker.tick() => {
                let mut bridge = state.bridge.lock().await;
                let sim = bridge.step().await;
                drop(bridge);
                state.broadcast_state(sim.clone()).await;
                let json = serde_json::to_string(&sim).unwrap();
                if socket.send(Message::Text(json.into())).await.is_err() {
                    break;
                }
            }
            msg = socket.recv() => {
                match msg {
                    Some(Ok(Message::Close(_))) | None => break,
                    _ => {}
                }
            }
        }
    }
}
```

---

### Task 2R.8 — Entrypoint (`main.rs`)

**File:** `rust-backend/src/main.rs` ❌ CREATE

```rust
mod models;
mod python;
mod routes_rest;
mod routes_ws;
mod state;

use std::sync::Arc;
use axum::{routing::{get, patch, post}, Router};
use tower_http::cors::{Any, CorsLayer};

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    let bridge = python::PythonBridge::spawn().await;
    let app_state = Arc::new(state::AppState::new(bridge));

    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    let app = Router::new()
        .route("/step", post(routes_rest::step))
        .route("/reset", post(routes_rest::reset))
        .route("/state", get(routes_rest::get_state))
        .route("/config", patch(routes_rest::update_config))
        .route("/ws", get(routes_ws::ws_handler))
        .layer(cors)
        .with_state(app_state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:8000").await.unwrap();
    tracing::info!("Rust backend listening on http://0.0.0.0:8000");
    axum::serve(listener, app).await.unwrap();
}
```

---

### Task 2R.9 — Cleanup

| Action | File |
|--------|------|
| DELETE | `py-project/main.py` — FastAPI server replaced by Rust |
| DELETE | `py-project/test_ws.py` — ad-hoc test script |

### Task 2R.10 — Verify

```bash
# Terminal 1: start Rust server
cd rust-backend/
cargo run

# Terminal 2: REST tests
curl http://localhost:8000/state
curl -X POST http://localhost:8000/step
curl -X POST http://localhost:8000/reset
curl -X PATCH http://localhost:8000/config \
     -H "Content-Type: application/json" \
     -d '{"low_threshold":65}'

# Terminal 3: WebSocket test (use wscat or websocat)
websocat ws://localhost:8000/ws?speed=60
# Should receive {"step":1,...} every 5 seconds
```

**Phase 2R complete when:** `curl GET /state` returns valid JSON AND `websocat ws://localhost:8000/ws` receives messages at expected intervals.

---

## Phase 3 — Frontend: Glucose Integration

**Goal:** The Electron avatar reacts to backend data in real time. Glucose badge appears on pet window, alerts surface via existing popup system.

All code identical to original plan — the frontend does not know or care whether the backend is Rust or Python, as long as the WebSocket/REST API contract is the same.

### Task 3.1 — Create `src/composable/useGlucose.ts` ❌ CREATE

```typescript
import { ref, readonly } from 'vue'

export interface SimState {
  step: number; sim_time: string; glucose: number;
  status: 'normal' | 'low' | 'high'; meal_event: boolean;
  meal_cho: number; alert: string | null; glucose_history: number[];
}

const simState = ref<SimState | null>(null)
const isConnected = ref(false)
const connectionError = ref<string | null>(null)

let ws: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let reconnectAttempts = 0
const MAX_RECONNECT = 5
const RECONNECT_DELAY_MS = 2000

export function useGlucose() {
  function connect(url = 'ws://localhost:8000/ws?speed=10') {
    if (ws?.readyState === WebSocket.OPEN) return
    ws = new WebSocket(url)
    ws.onopen = () => { isConnected.value = true; connectionError.value = null; reconnectAttempts = 0 }
    ws.onmessage = (e: MessageEvent) => {
      try { simState.value = JSON.parse(e.data) } catch { /* ignore */ }
    }
    ws.onerror = () => { connectionError.value = 'WebSocket error' }
    ws.onclose = () => {
      isConnected.value = false; ws = null
      if (reconnectAttempts < MAX_RECONNECT) {
        reconnectAttempts++; reconnectTimer = setTimeout(() => connect(url), RECONNECT_DELAY_MS)
      } else { connectionError.value = `Failed after ${MAX_RECONNECT} attempts` }
    }
  }
  function disconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    reconnectAttempts = MAX_RECONNECT; ws?.close(); ws = null
  }
  return { simState: readonly(simState), isConnected: readonly(isConnected),
           connectionError: readonly(connectionError), connect, disconnect }
}
```

---

### Task 3.2 — Modify `src/composable/useModel.ts` ✅ EXISTS → ❌ MODIFY

After `const clickActionPlay = ref(false)`, add:

```typescript
const glucoseStatus = ref<'normal' | 'low' | 'high'>('normal')
```

Inside `useModel()`, before `return`, add:

```typescript
function applyGlucoseState(status: 'normal' | 'low' | 'high', mealEvent: boolean) {
  glucoseStatus.value = status
  if (mealEvent) { clickActionPlay.value = true; return }
  if (!loopAction.value.isLoop) { loopAction.value = { action: 'Play', isLoop: true } }
}
```

Add to return: `glucoseStatus, applyGlucoseState,`

---

### Task 3.3 — Create `src/components/GlucoseOverlay.vue` ❌ CREATE

```vue
<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ glucose: number | null; status: 'normal' | 'low' | 'high'; isConnected: boolean }>()
const tintClass = computed(() =>
  !props.isConnected ? '' : props.status === 'low' ? 'tint-low' : props.status === 'high' ? 'tint-high' : '')
const glucoseColor = computed(() =>
  props.status === 'low' ? '#FF6B35' : props.status === 'high' ? '#E63946' : '#2DC653')
</script>
<template>
  <div class="absolute inset-0 pointer-events-none transition-all duration-500" :class="tintClass" />
  <div v-if="isConnected && glucose !== null"
       class="absolute bottom-2 left-2 pointer-events-none select-none flex flex-col items-center leading-none"
       :style="{ color: glucoseColor }">
    <span class="text-[13px] font-bold tabular-nums">{{ glucose.toFixed(0) }}</span>
    <span class="text-[8px] opacity-70">mg/dL</span>
  </div>
  <div v-else class="absolute bottom-2 left-2 pointer-events-none select-none">
    <span class="text-[8px] text-gray-400 opacity-60">⚡ offline</span>
  </div>
</template>
<style scoped>
.tint-low  { background: radial-gradient(circle, rgba(255,107,53,0.18) 0%, transparent 70%); }
.tint-high { background: radial-gradient(circle, rgba(230,57,70,0.18) 0%, transparent 70%); }
</style>
```

---

### Task 3.4 — Modify `src/views/Home.vue` ✅ EXISTS → ❌ MODIFY

Add imports:
```javascript
import { watch } from 'vue'
import GlucoseOverlay from '../components/GlucoseOverlay.vue'
import { useGlucose } from '../composable/useGlucose'
```

After `const { clickActionPlayMessage, url } = useModel()`:
```javascript
const { applyGlucoseState } = useModel()
const { simState, isConnected, connect, disconnect } = useGlucose()
watch(simState, (state) => {
  if (!state) return
  applyGlucoseState(state.status, state.meal_event)
  if (state.alert) {
    window.ipcRenderer.send('glucose-alert', { alert: state.alert, glucose: state.glucose, sim_time: state.sim_time })
  }
})
```

In `onMounted`: add `connect()`. In `onUnmounted`: add `disconnect()`.

Wrap root `<div>` with `class="relative w-full h-full"`. Insert `<GlucoseOverlay>` before `<div v-show="showContextMenu">`. Keep `<Pet :key="url" />` and `<Toast>`.

---

### Task 3.5 — Modify `src/components/ContextMenu.vue` ❌ MODIFY

Add to `menuItems` before `exit`:
```javascript
{ id: 'glucose', label: '血糖面板', icon: '💉' },
```

Add to switch:
```javascript
case 'glucose':
  ipcRenderer.send('open-sub-window', { windowId: 'glucose', title: '血糖监控' }); break
```

---

### Task 3.6 — Modify `src/router/index.ts` ❌ MODIFY

Add route:
```typescript
{ path: '/glucose', name: 'Glucose', component: () => import('../views/GlucoseDashboard.vue') },
```

---

### Task 3.7 — Create `src/views/GlucoseDashboard.vue` ❌ CREATE

800×600 sub-window with independent WebSocket. Display: glucose value, time, status, SVG trend chart (last 50 steps). Config panel: low/high thresholds, meal cutoff slider. `PATCH /config` button.

---

### Task 3.8 — Modify `electron/main.ts` ❌ MODIFY

Inside `app.whenReady().then(...)`, after existing `ipcMain.on` handlers:
```typescript
ipcMain.on('glucose-alert', (_event, data: { alert: string; glucose: number; sim_time: string }) => {
  if (reminderWindow && !reminderWindow.isVisible()) reminderWindow.show()
  reminderWindow?.webContents.send('glucose-alert-data', data)
})
```

---

### Task 3.9 — Modify `src/views/ReminderPopup.vue` ❌ MODIFY

Add `glucoseAlert` ref, `ALERT_MESSAGES` map, auto-dismiss timer (8s), IPC listener for `glucose-alert-data`. Template: alert card with Chinese message + glucose value + dismiss button, placed before existing `<TransitionGroup>`.

---

## API Reference

### REST (Rust Axum → port 8000)

| Method | Path | Body | Response |
|--------|------|------|----------|
| `POST` | `/step` | — | `SimState` JSON |
| `POST` | `/reset` | — | `SimState` JSON |
| `GET` | `/state` | — | `SimState` JSON |
| `PATCH` | `/config` | `ConfigUpdate` | `{ "ok": true }` |

### WebSocket

```
ws://localhost:8000/ws?speed=<float>
```

| speed | Step interval |
|-------|---------------|
| `1` | 5 real minutes |
| `10` | 30 real seconds |
| `60` | 5 real seconds |

### SimState JSON

```json
{
  "step": 42, "sim_time": "10:30", "glucose": 112.5,
  "status": "normal", "meal_event": false, "meal_cho": 0,
  "alert": null, "glucose_history": [108.2, 109.1, 110.4]
}
```

---

## Acceptance Criteria

| # | Test | Condition |
|---|------|-----------|
| B1 | `python run_simulation.py` 288 steps | No crash, glucose 40–400, ≥1 meal fires ✅ |
| B2 | `python meal_model/train.py` | `model.pkl` created, log + metrics produced ✅ |
| B3 | Alert engine | low after 2 steps <70, high after 3 steps >180 ✅ |
| R1 | `cargo run` starts | Rust server on :8000, Python child spawned |
| R2 | `curl GET /state` | Returns valid SimState JSON |
| R3 | `curl -X POST /step` | Advances 1 step, returns updated state |
| R4 | `curl -X PATCH /config` | `{"ok":true}`, new thresholds active |
| R5 | `websocat ws://localhost:8000/ws?speed=60` | Receives messages every ~5s |
| F1 | Electron cold start | Avatar renders, glucose badge visible ≤2s after connect |
| F2 | `status: normal` | Green badge, no tint |
| F3 | `status: low` | Amber badge (#FF6B35) + amber radial tint |
| F4 | `status: high` | Red badge (#E63946) + red radial tint |
| F5 | `meal_event: true` | One-shot Hello/Space-Salsa, resumes Play |
| F6 | Non-null `alert` | Popup appears ≤1s, correct Chinese message |
| F7 | Dismiss alert | "知道了" closes; 8s auto-dismiss works |
| F8 | Right-click → 血糖面板 | 800×600 subwindow with live chart + config |
| F9 | Config update | PATCH 200, thresholds apply from next step |
| F10 | Backend offline | "⚡ offline" badge, reconnect every 2s |

---

## File Change Summary

### py-project

| File | Action | Status |
|------|--------|--------|
| `bridge.py` | CREATE | ❌ |
| `main.py` | DELETE | — |
| `test_ws.py` | DELETE | — |
| All other files | KEEP | ✅ |

### rust-backend (all new)

| File | Action | Status |
|------|--------|--------|
| `Cargo.toml` | CREATE | ❌ |
| `src/main.rs` | CREATE | ❌ |
| `src/models.rs` | CREATE | ❌ |
| `src/python.rs` | CREATE | ❌ |
| `src/state.rs` | CREATE | ❌ |
| `src/routes_rest.rs` | CREATE | ❌ |
| `src/routes_ws.rs` | CREATE | ❌ |

### visual-project

| File | Action | Status |
|------|--------|--------|
| `src/composable/useGlucose.ts` | CREATE | ❌ |
| `src/components/GlucoseOverlay.vue` | CREATE | ❌ |
| `src/views/GlucoseDashboard.vue` | CREATE | ❌ |
| `src/composable/useModel.ts` | MODIFY | ❌ (+15 lines) |
| `src/views/Home.vue` | MODIFY | ❌ (+25 lines) |
| `src/components/ContextMenu.vue` | MODIFY | ❌ (+6 lines) |
| `src/router/index.ts` | MODIFY | ❌ (+4 lines) |
| `src/views/ReminderPopup.vue` | MODIFY | ❌ (+45 lines) |
| `electron/main.ts` | MODIFY | ❌ (+8 lines) |
