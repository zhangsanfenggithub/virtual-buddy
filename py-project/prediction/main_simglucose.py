from simglucose.simulation.env import T1DSimEnv
from simglucose.patient.t1dpatient import T1DPatient
from simglucose.sensor.cgm import CGMSensor
from simglucose.actuator.pump import InsulinPump
from simglucose.simulation.scenario import CustomScenario
from simglucose.controller.basal_bolus_ctrller import BBController
from datetime import datetime
from datetime import timedelta
from collections import deque
import pandas as pd

start_time = datetime(2026, 1, 1, 0, 0, 0)
meals = [(7.0, 45), (12.5, 60), (18.0, 50)]

patient  = T1DPatient.withName('adult#001')
sensor   = CGMSensor.withName('Dexcom', seed=42)
pump     = InsulinPump.withName('Insulet')
scenario = CustomScenario(start_time=start_time, scenario=meals)
ctrl     = BBController()

env = T1DSimEnv(patient, sensor, pump, scenario)
obs, _, done, info = env.reset() #  Reset the environment


records = []
MAX_STEPS = 480   # Maximum 480 steps = 24 hours
LOG_EVERY  = 5    
step = 0

LOW_GLUCOSE = 70.0  ##### question 2 and 3
HIGH_GLUCOSE = 180.0
PREDICT_INTERVAL_MIN = 30.0
ALERT_EVERY_MIN = 5.0
SLOPE_LENGTH = 6

recent = deque(maxlen=SLOPE_LENGTH)
next_alert_time = start_time
last_low_alert_time = None
last_high_alert_time = None

while not done and step < MAX_STEPS:
    t = info['time']
    action = ctrl.policy(
        observation=obs,
        patient_name='adult#001', 
        meal=info.get('meal', 0), #whether eat or not 
        t=t 
    )
    # update environment 
    obs, _, _, info = env.step(action)
    t = info['time']
    cgm = obs.CGM 
    insulin = float(action.basal)
    time_cgm_pair = (t, float(cgm))
    recent.append(time_cgm_pair) 

    slope = None
    pred = None

    if len(recent) >= 2:
        time_cgm_pair0 = recent[0]
        time_cgm_pair1 = recent[-1]
        dt_min = (time_cgm_pair1[0] - time_cgm_pair0[0]).total_seconds() / 60.0
        slope = (time_cgm_pair1[1] - time_cgm_pair0[1]) / dt_min if dt_min > 0 else 0.0
        pred = float(cgm) + slope * PREDICT_INTERVAL_MIN  #### question1

    step += 1
