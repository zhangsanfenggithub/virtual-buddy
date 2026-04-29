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
