import pandas as pd
import numpy as np
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.estimators import MaximumLikelihoodEstimator
from pgmpy.inference import VariableElimination

df = pd.read_csv('../data/HUPA0001P.csv', sep=';', parse_dates=['time'])
df = df.sort_values('time').reset_index(drop=True)

def hour_to_period(h):
    if h < 6:     return 0
    elif h < 10:  return 1
    elif h < 14:  return 2
    elif h < 18:  return 3
    else:         return 4

def glucose_level(g):
    if g < 70:    return 0
    elif g < 140: return 1
    elif g < 200: return 2
    else:         return 3

def hr_level(h):
    if h < 60:   return 0
    elif h < 90: return 1
    else:        return 2

def since_meal_level(s):
    if s < 6:    return 0
    elif s < 18: return 1
    elif s < 30: return 2
    else:        return 3

df['hour']          = df['time'].dt.hour
df['time_period']   = df['hour'].apply(hour_to_period)
df['is_weekend']    = df['time'].dt.dayofweek.isin([5, 6]).astype(int)
df['meal_happened'] = (df['carb_input'] > 0).astype(int)
df['glucose_level'] = df['glucose'].apply(glucose_level)
df['hr_level']      = df['heart_rate'].apply(hr_level)

steps_since = 0
since_list = []
for i in range(len(df)):
    if df.loc[i, 'meal_happened'] == 1:
        steps_since = 0
    else:
        steps_since = min(steps_since + 1, 36)
    since_list.append(steps_since)
df['steps_since_meal'] = since_list
df['since_meal'] = df['steps_since_meal'].apply(since_meal_level)

meal_only = df[df['meal_happened'] == 1].copy()
meal_only['carb_level'] = pd.cut(
    meal_only['carb_input'],
    bins=[-0.1, 20, 50, 999],
    labels=[1, 2, 3]
).astype(int)

df = df.merge(meal_only[['time', 'carb_level']], on='time', how='left')
df['carb_level'] = df['carb_level'].fillna(0).astype(int)

carb_means = meal_only.groupby('carb_level')['carb_input'].mean().to_dict()
carb_means[0] = 0.0

model = DiscreteBayesianNetwork([
    ('time_period',   'meal_happened'),
    ('is_weekend',    'meal_happened'),
    ('glucose_level', 'meal_happened'),
    ('since_meal',    'meal_happened'),
    ('hr_level',      'meal_happened'),
    ('meal_happened', 'carb_level'),
])

train_cols = ['time_period', 'is_weekend', 'glucose_level',
              'since_meal', 'hr_level', 'meal_happened', 'carb_level']

model.fit(df[train_cols], estimator=MaximumLikelihoodEstimator)

infer = VariableElimination(model)

print("done")
print("\n── CPD: meal_happened ──")
print(model.get_cpds('meal_happened'))
print("\n── CPD: carb_level ──")
print(model.get_cpds('carb_level'))

def predict_meal(hour, glucose, heart_rate, since_meal_steps, is_weekend=0):
    evidence = {
        'time_period':   hour_to_period(hour),
        'is_weekend':    is_weekend,
        'glucose_level': glucose_level(glucose),
        'since_meal':    since_meal_level(since_meal_steps),
        'hr_level':      hr_level(heart_rate),
    }
    meal_q = infer.query(['meal_happened'], evidence=evidence)
    meal_prob = meal_q.values[1]

    carb_q = infer.query(['carb_level'], evidence={**evidence, 'meal_happened': 1})
    best_level = int(np.argmax(carb_q.values[1:]))
    predicted_carb = carb_means.get(best_level, 0.0)

    return meal_prob, predicted_carb

test_cases = [
    (7,  80,  65, 30, 0, 'Breakfast low glucose after prolonged fasting'),
    (12, 160, 90, 36, 0, 'Lunch high glucose and elevated heart rate'),
    (15, 120, 70, 6,  0, 'Afternoon just after eating'),
    (18, 90,  72, 36, 0, 'Dinner normal glucose'),
    (2,  70,  55, 10, 0, 'Midnight low glucose'),
    (12, 160, 90, 36, 1, 'Lunch weekend'),
]

print("── Prediction ──")
for hour, glu, hr, since, wknd, desc in test_cases:
    prob, carb = predict_meal(hour, glu, hr, since, wknd)
    print(f"  {desc:22s} |  {prob:.2%} | Carb: {carb:.1f}g")