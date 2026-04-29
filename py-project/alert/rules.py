from typing import Optional

from simulation.state import SimState


class AlertEngine:
    LOW_THRESHOLD: float = 70
    HIGH_THRESHOLD: float = 180
    LOW_CONSECUTIVE_STEPS: int = 2
    HIGH_CONSECUTIVE_STEPS: int = 3
    MEAL_TIMEOUT_HOURS: float = 6.0

    def __init__(self):
        self._low_count = 0
        self._high_count = 0
        self._last_meal_step = 0
        self._step_duration_minutes = 5

    def evaluate(self, state: SimState) -> Optional[str]:
        if state.glucose < self.LOW_THRESHOLD:
            self._low_count += 1
        else:
            self._low_count = 0

        if state.glucose > self.HIGH_THRESHOLD:
            self._high_count += 1
        else:
            self._high_count = 0

        if self._low_count >= self.LOW_CONSECUTIVE_STEPS:
            return "low_glucose"

        if self._high_count >= self.HIGH_CONSECUTIVE_STEPS:
            return "high_glucose"

        steps_since_meal = state.step - self._last_meal_step
        timeout_minutes = self.MEAL_TIMEOUT_HOURS * 60
        if steps_since_meal * self._step_duration_minutes > timeout_minutes:
            return "timeout_reminder"

        return None

    def record_meal(self, step: int) -> None:
        self._last_meal_step = step
