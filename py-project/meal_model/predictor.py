import pickle
import random

import numpy as np
from pgmpy.inference import VariableElimination

from meal_model import config


class MealPredictor:
    def __init__(self, model_path: str = config.MODEL_PATH):
        with open(model_path, "rb") as f:
            self._model = pickle.load(f)
        self._infer = VariableElimination(self._model)

    def predict(self, sim_time: str, hours_since_last_meal: float, glucose: float) -> dict:
        tc_5m = self._sim_time_to_tc5m(sim_time)
        tp_state = self._hours_since_meal_to_tp(hours_since_last_meal)
        gl_state = self._glucose_to_gl_state(glucose)

        evidence = {"TC_5m": tc_5m, "TP_State": tp_state, "GL_State": gl_state}

        try:
            tun_result = self._infer.query(variables=["TUN_State"], evidence=evidence)
            sn_result = self._infer.query(variables=["SN_State"], evidence=evidence)
        except Exception:
            return {
                "tun_state": 0,
                "sn_state": 0,
                "should_eat": False,
                "suggested_cho": 0.0,
            }

        tun_prob = tun_result.values
        tun_state = int(tun_result.state_names["TUN_State"][np.argmax(tun_prob)])

        p_meal_in_1h = float(tun_prob[tun_result.state_names["TUN_State"].index(1)])
        p_meal_in_3h = float(
            tun_prob[tun_result.state_names["TUN_State"].index(1)]
            + tun_prob[tun_result.state_names["TUN_State"].index(2)]
        )
        should_eat = (
            p_meal_in_1h > config.MEAL_CUTOFF_1H
            or p_meal_in_3h > config.MEAL_CUTOFF_3H
        )

        sn_prob = sn_result.values
        sn_state = int(sn_result.state_names["SN_State"][np.argmax(sn_prob)])

        if should_eat:
            if sn_state == 2:
                suggested_cho = float(random.choice(config.CHO_OPTIONS_NORMAL))
            else:
                suggested_cho = float(random.choice(config.CHO_OPTIONS_SNACK))
        else:
            suggested_cho = 0.0

        return {
            "tun_state": tun_state,
            "sn_state": sn_state,
            "should_eat": should_eat,
            "suggested_cho": suggested_cho,
        }

    @staticmethod
    def _sim_time_to_tc5m(sim_time: str) -> int:
        parts = sim_time.split(":")
        hour = int(parts[0])
        minute = int(parts[1])
        return (hour * 60 + minute) // 5

    @staticmethod
    def _hours_since_meal_to_tp(hours: float) -> int:
        minutes = hours * 60
        if minutes < 30:
            return 1
        if minutes <= 120:
            return 2
        if minutes <= 240:
            return 3
        return 4

    @staticmethod
    def _glucose_to_gl_state(glucose: float) -> int:
        if glucose < 70:
            return 1
        if glucose <= 140:
            return 2
        return 3
