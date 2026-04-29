use std::process::Stdio;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::process::Command;

use crate::models::{ConfigUpdate, SimState};

pub struct PythonBridge {
    _child: tokio::process::Child,
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
        Self {
            _child: child,
            stdin,
            stdout: BufReader::new(stdout),
        }
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
        let resp = self.recv().await.expect("Python process died");
        serde_json::from_str(&resp).expect("invalid SimState JSON")
    }

    pub async fn get_state(&mut self) -> SimState {
        self.send(r#"{"cmd":"get_state"}"#).await;
        let resp = self.recv().await.expect("Python process died");
        serde_json::from_str(&resp).expect("invalid SimState JSON")
    }

    pub async fn update_config(&mut self, config: &ConfigUpdate) {
        let mut map = serde_json::Map::new();
        map.insert("cmd".into(), "config".into());
        if let Some(v) = config.low_threshold {
            map.insert("low_threshold".into(), v.into());
        }
        if let Some(v) = config.high_threshold {
            map.insert("high_threshold".into(), v.into());
        }
        if let Some(v) = config.meal_probability_cutoff {
            map.insert("meal_probability_cutoff".into(), v.into());
        }
        let json = serde_json::Value::Object(map);
        self.send(&json.to_string()).await;
        self.recv().await;
    }
}
