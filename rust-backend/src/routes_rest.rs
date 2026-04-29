use std::sync::Arc;
use axum::{extract::State, Json};

use crate::models::{ConfigUpdate, ConfigResponse, SimState};
use crate::state::AppState;

pub async fn step(State(state): State<Arc<AppState>>) -> Json<SimState> {
    let mut bridge = state.bridge.lock().await;
    let sim = bridge.step().await;
    state.broadcast_state(sim.clone());
    Json(sim)
}

pub async fn reset(State(state): State<Arc<AppState>>) -> Json<SimState> {
    let mut bridge = state.bridge.lock().await;
    let sim = bridge.reset().await;
    state.broadcast_state(sim.clone());
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
