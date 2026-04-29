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
        Self {
            bridge: Arc::new(Mutex::new(bridge)),
            tx_state: tx,
            rx_state: rx,
        }
    }

    pub fn broadcast_state(&self, state: SimState) {
        let _ = self.tx_state.send(Some(state));
    }
}
