use std::sync::Arc;
use axum::extract::{ws::{Message, WebSocket}, Query, State, WebSocketUpgrade};
use axum::response::IntoResponse;
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
                state.broadcast_state(sim.clone());
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
