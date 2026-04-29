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
        return {
            "step": 0, "sim_time": "00:00", "glucose": 95.0,
            "status": "normal", "meal_event": False, "meal_cho": 0,
            "alert": None, "glucose_history": [],
        }
    return state.to_dict()


def _do_reset() -> dict:
    global _hours_since_last_meal
    _engine.reset()
    _hours_since_last_meal = 0.0
    return _current_state()


def _apply_config(data: dict):
    if "low_threshold" in data:
        _alert_engine.LOW_THRESHOLD = data["low_threshold"]
    if "high_threshold" in data:
        _alert_engine.HIGH_THRESHOLD = data["high_threshold"]
    if "meal_probability_cutoff" in data:
        _predictor.CUTOFF = data["meal_probability_cutoff"]


HANDLERS = {
    "step":      _simulate_one_step,
    "reset":     _do_reset,
    "get_state": _current_state,
}


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


if __name__ == "__main__":
    main()
