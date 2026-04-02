from simglucose.simulation.env import T1DSimEnv
from simglucose.patient.t1dpatient import T1DPatient
from simglucose.sensor.cgm import CGMSensor
from simglucose.actuator.pump import InsulinPump
from simglucose.simulation.scenario import CustomScenario
from simglucose.controller.basal_bolus_ctrller import BBController
from datetime import datetime
import pandas as pd

start_time = datetime(2026, 1, 1, 0, 0, 0)
meals = [(7.0, 45), (12.5, 60), (18.0, 50)]

patient  = T1DPatient.withName('adult#001')
sensor   = CGMSensor.withName('Dexcom', seed=42)
pump     = InsulinPump.withName('Insulet')
scenario = CustomScenario(start_time=start_time, scenario=meals)
ctrl     = BBController()

env = T1DSimEnv(patient, sensor, pump, scenario)
obs, _, done, info = env.reset()

records = []
MAX_STEPS = 480   # 最多480步 = 24小时
LOG_EVERY  = 5    # 每5步打印一次（15分钟）
step = 0

while not done and step < MAX_STEPS:
    t = info['time']
    action = ctrl.policy(
        observation=obs,
        reward=0,
        done=False,
        patient_name='adult#001',
        meal=info.get('meal', 0),
        t=t
    )
    obs, reward, done, info = env.step(action)
    cgm = obs.CGM
    insulin = float(action.basal) + float(action.bolus)
    records.append({'time': t, 'CGM': cgm, 'insulin': insulin})

    if step % LOG_EVERY == 0:
        status = "🔴 低血糖" if cgm < 70 else ("🟡 高血糖" if cgm > 180 else "🟢 正常")
        print(f"{t.strftime('%H:%M')} | CGM: {cgm:.1f} mg/dL | {status}")

    step += 1

df = pd.DataFrame(records)
df.to_csv('simglucose_result.csv', index=False)
print(f"\n✅ 共 {len(df)} 条记录，已保存到 simglucose_result.csv")