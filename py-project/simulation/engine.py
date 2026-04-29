from datetime import datetime
from typing import Callable, Optional

from simglucose.simulation.env import T1DSimEnv
from simglucose.patient.t1dpatient import T1DPatient
from simglucose.sensor.cgm import CGMSensor
from simglucose.actuator.pump import InsulinPump
from simglucose.simulation.scenario import CustomScenario
from simglucose.controller.basal_bolus_ctrller import BBController

from simulation.state import SimState


class SimulationEngine:
    def __init__(self, patient_name: str = "adult#001", speed: float = 10.0):
        self._patient_name = patient_name
        self._speed = speed
        self._start_time = datetime(2026, 1, 1, 0, 0, 0)

        self._patient = T1DPatient.withName(patient_name)
        self._sensor = CGMSensor.withName("Dexcom", seed=42)
        self._sensor.sample_time = 5
        self._sensor._params["min"] = 20
        self._pump = InsulinPump.withName("Insulet")
        self._scenario = CustomScenario(start_time=self._start_time, scenario=[])
        self._ctrl = BBController()

        self._env = T1DSimEnv(self._patient, self._sensor, self._pump, self._scenario)

        self._obs, self._reward, self._done, self._info = self._env.reset()
        self._current_time = self._info["time"]
        self._step_count = 0
        self._pending_cho = 0.0
        self._glucose_history: list[float] = []
        self._state: Optional[SimState] = None

    def step(self) -> SimState:
        cho = self._pending_cho
        self._pending_cho = 0.0
        meal_event = cho > 0

        if meal_event:
            hours_offset = (self._current_time - self._start_time).total_seconds() / 3600.0
            self._scenario.scenario.append((hours_offset, cho))

        action = self._ctrl.policy(
            observation=self._obs,
            reward=self._reward,
            done=self._done,
            patient_name=self._patient_name,
            meal=cho,
            t=self._current_time,
        )

        self._obs, self._reward, self._done, self._info = self._env.step(action)
        self._current_time = self._info["time"]

        cgm = float(self._obs.CGM)
        self._glucose_history.append(cgm)
        if len(self._glucose_history) > 50:
            self._glucose_history = self._glucose_history[-50:]

        status = self._compute_status(cgm)
        self._step_count += 1

        self._state = SimState(
            step=self._step_count,
            sim_time=self._current_time.strftime("%H:%M"),
            glucose=cgm,
            status=status,
            meal_event=meal_event,
            meal_cho=cho,
            alert=None,
            glucose_history=list(self._glucose_history),
        )
        return self._state

    def inject_meal(self, cho: float) -> None:
        self._pending_cho = cho

    def get_state(self) -> Optional[SimState]:
        return self._state

    def reset(self) -> None:
        self._env = T1DSimEnv(self._patient, self._sensor, self._pump, self._scenario)
        self._obs, self._reward, self._done, self._info = self._env.reset()
        self._current_time = self._info["time"]
        self._step_count = 0
        self._pending_cho = 0.0
        self._glucose_history.clear()
        self._state = None

    def set_external_glucose_source(self, source_fn: Callable[[], float]) -> None:
        raise NotImplementedError("CGM device integration not yet implemented.")

    @staticmethod
    def _compute_status(glucose: float) -> str:
        if glucose < 70:
            return "low"
        if glucose > 180:
            return "high"
        return "normal"
