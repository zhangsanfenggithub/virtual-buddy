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
