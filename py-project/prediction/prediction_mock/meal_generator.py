import pandas as pd
import numpy as np

np.random.seed(42)
records = []

# Simulate 30 days of meal records
for day in range(30):
    for hour in range(24):
        # Breakfast: 7-9 AM, 70% probability
        if 7 <= hour <= 9:
            meal = np.random.choice([0, 1], p=[0.3, 0.7])
            carb = np.random.randint(30, 60) if meal else 0
        # Lunch: 12-14 PM, 80% probability
        elif 12 <= hour <= 14:
            meal = np.random.choice([0, 1], p=[0.2, 0.8])
            carb = np.random.randint(50, 80) if meal else 0
        # Dinner: 18-20 PM, 75% probability
        elif 18 <= hour <= 20:
            meal = np.random.choice([0, 1], p=[0.25, 0.75])
            carb = np.random.randint(40, 70) if meal else 0
        # Other times, rarely eat
        else:
            meal = np.random.choice([0, 1], p=[0.95, 0.05])
            carb = np.random.randint(10, 30) if meal else 0

        records.append({
            'day': day,
            'hour': hour,
            'day_of_week': day % 7,
            'meal_happened': meal,
            'carb_amount': carb
        })

df = pd.DataFrame(records)
df.to_csv('meal_history.csv', index=False)
print(df[df['meal_happened'] == 1].head(10))

