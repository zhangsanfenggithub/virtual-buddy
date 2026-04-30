from datetime import datetime

from simulation.engine import SimulationEngine
from meal_model.predictor import MealPredictor
from alert.rules import AlertEngine

MAX_STEPS = 2016  # 7 days × 24h × 12 steps/h


def main():
    engine = SimulationEngine(patient_name="adult#001")
    predictor = MealPredictor()
    alert_engine = AlertEngine()

    start_time = datetime(2026, 1, 1, 0, 0, 0)
    hours_since_last_meal = 0.0
    total_meal_count = 0

    for _ in range(MAX_STEPS):
        current_state = engine.get_state()
        if current_state is not None:
            sim_time = current_state.sim_time
            glucose = current_state.glucose
        else:
            sim_time = "00:00"
            glucose = 95.0

        prediction = predictor.predict(sim_time, hours_since_last_meal, glucose)

        if prediction["should_eat"]:
            engine.inject_meal(prediction["suggested_cho"])

        if glucose < 70 and hours_since_last_meal > 3 and not prediction["should_eat"]:
            engine.inject_meal(30)
        if glucose < 55 and hours_since_last_meal > 2:
            engine.inject_meal(45)

        state = engine.step()

        if state.meal_event:
            alert_engine.record_meal(state.step)
            hours_since_last_meal = 0.0
            total_meal_count += 1
        else:
            hours_since_last_meal += 5.0 / 60.0

        state.alert = alert_engine.evaluate(state)

        meal_str = f"{int(state.meal_cho)}g CHO" if state.meal_event else "None"
        alert_str = state.alert if state.alert else "None"
        print(
            f"[Step {state.step:>3}] {state.sim_time} | "
            f"Glucose: {state.glucose:>6.1f} | "
            f"Status: {state.status:<6} | "
            f"Meal: {meal_str:<11} | "
            f"Alert: {alert_str}"
        )

    print(f"\nSimulation complete. {total_meal_count} meals injected over 7 days.")


if __name__ == "__main__":
    main()
