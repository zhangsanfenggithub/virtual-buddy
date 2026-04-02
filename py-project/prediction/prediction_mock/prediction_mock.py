import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.estimators import MaximumLikelihoodEstimator
from pgmpy.inference import VariableElimination

df = pd.read_csv('meal_history.csv')


def hour_to_period(h):
    if h < 6:
        return 0
    elif h < 10:
        return 1
    elif h < 14:
        return 2
    elif h < 18:
        return 3
    else:
        return 4


df['time_period'] = df['hour'].apply(hour_to_period)
df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
df['meal_happened'] = (df['carb_amount'] > 0).astype(int)
# First, filter records with meals
meal_only = df[df['meal_happened'] == 1].copy()

meal_only['carb_level'] = pd.cut(
    meal_only['carb_amount'],
    bins=[-0.1, 20, 50, 999],
    labels=[1, 2, 3]
).astype(int)

plt.hist(df['hour'], bins=np.linspace(0,24,25), density=True, alpha=0.5, label='meal_only')
plt.show()

df = df.merge(meal_only[['hour', 'carb_level']], on='hour', how='left')
df['carb_level'] = df['carb_level'].fillna(0).astype(int)

carb_means = meal_only.groupby('carb_level')['carb_amount'].mean().to_dict()
carb_means[0] = 0.0

model = DiscreteBayesianNetwork([
    ('time_period', 'meal_happened'),
    ('is_weekend', 'meal_happened'),
    ('meal_happened', 'carb_level'),
])

train_df = df[['time_period', 'is_weekend', 'meal_happened', 'carb_level']]
model.fit(train_df, estimator=MaximumLikelihoodEstimator)

print("done")
print("\n── CPD: meal_happened ──")
print(model.get_cpds('meal_happened'))
print("\n── CPD: carb_level ──")
print(model.get_cpds('carb_level'))

infer = VariableElimination(model)


def predict_meal(hour, is_weekend=0):
    period = hour_to_period(hour)

    meal_result = infer.query(
        variables=['meal_happened'],
        evidence={'time_period': period, 'is_weekend': is_weekend}
    )
    meal_prob = meal_result.values[1]

    carb_result = infer.query(
        variables=['carb_level'],
        evidence={'time_period': period, 'is_weekend': is_weekend, 'meal_happened': 1}
    )

    best_level = int(np.argmax(carb_result.values[1:]))
    predicted_carb = carb_means.get(best_level, 0.0)

    return meal_prob, predicted_carb


# Test prediction
print("\n── Results ──")
for hour in [7, 10, 12, 15, 18, 22]:
    prob, carb = predict_meal(hour)
    print(f"  {hour:02d}:00 | Meal prob: {prob:.2%} | Carb: {carb:.1f}g")