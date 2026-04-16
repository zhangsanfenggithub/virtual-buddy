import pandas as pd
df = pd.read_csv('../data/HUPA0001P.csv', sep=';', parse_dates=['time'])
df = df.sort_values('time').reset_index(drop=True)
df['carb_input'] = df['carb_input'].fillna(0.0)
df['time'] = pd.to_datetime(df['time'])

# time
#
# glucose
#
# calories
#
# heart_rate
#
# steps
#
# basal_rate
#
# bolus_volume_delivered
#
# carb_input

import numpy as np
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.estimators import BayesianEstimator, MaximumLikelihoodEstimator
from pgmpy.inference import VariableElimination
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, classification_report
import warnings

warnings.filterwarnings('ignore')

df = pd.read_csv('../data/HUPA0001P.csv', sep=';', parse_dates=['time'])
df = df.sort_values('time').reset_index(drop=True)

df['carb_input'] = df['carb_input'].fillna(0.0)
df['TC_Hour'] = df['time'].dt.hour
df['glucose'] = df['glucose'].ffill().bfill()
df["GL_State"] = pd.cut(df['glucose'], bins=[-1, 70, 140, 999], labels=[1, 2, 3]).astype(int)

df['last_meal_time'] = df.apply(lambda row: row['time'] if row['carb_input'] > 0 else pd.NaT, axis=1).ffill()
df['hours_since_last'] = (df['time'] - df['last_meal_time']).dt.total_seconds() / 3600
df['hours_since_last'] = df['hours_since_last'].fillna(999)
df['TP_State'] = pd.cut(df['hours_since_last'], bins=[-1, 2, 4, 999], labels=[1, 2, 3]).astype(int)

df['next_meal_time'] = df.apply(lambda row: row['time'] if row['carb_input'] > 0 else pd.NaT, axis=1).bfill()
df['next_meal_amount'] = df.apply(lambda row: row['carb_input'] if row['carb_input'] > 0 else pd.NA, axis=1).bfill()
df['hours_until_next'] = (df['next_meal_time'] - df['time']).dt.total_seconds() / 3600

df['GL_State_Prev'] = df['GL_State'].shift(1)
df['TUN_State_Prev'] = pd.cut(df['hours_until_next'].shift(1), bins=[-0.1, 1, 3, 999], labels=[1, 2, 3])

train_df = df.dropna(subset=['hours_until_next', 'GL_State_Prev', 'TUN_State_Prev']).copy()
train_df['TUN_State'] = pd.cut(train_df['hours_until_next'], bins=[-0.1, 1, 3, 999], labels=[1, 2, 3]).astype(int)
train_df['SN_State'] = pd.cut(train_df['next_meal_amount'], bins=[0, 3, 999], labels=[1, 2]).astype(int)
train_df['GL_State_Prev'] = train_df['GL_State_Prev'].astype(int)
train_df['TUN_State_Prev'] = train_df['TUN_State_Prev'].astype(int)

train_df = train_df.reset_index(drop=True)

features = ['GL_State_Prev', 'TUN_State_Prev', 'TC_Hour', 'GL_State', 'TP_State']
targets = ['TUN_State', 'SN_State']
all_cols = features + targets

#split
tscv = TimeSeriesSplit(n_splits=5)

fragment_index = 1
tun_accuracies = []
sn_accuracies = []

for train_index, test_index in tscv.split(train_df):
    train_fragment = train_df.iloc[train_index]
    test_fragment = train_df.iloc[test_index]

    model = DiscreteBayesianNetwork([
        ('GL_State_Prev', 'GL_State'),
        ('TUN_State_Prev', 'TUN_State'),
        ('TC_Hour', 'TUN_State'),
        ('GL_State', 'TUN_State'),
        ('TP_State', 'TUN_State'),
        ('TUN_State', 'SN_State'),
    ])

    model.fit(
        train_fragment[all_cols],
        estimator=BayesianEstimator,
        equivalent_sample_size=10
    )

    X_test = test_fragment[features]
    y_test_tun = test_fragment['TUN_State'].values
    y_test_sn = test_fragment['SN_State'].values

    predictions = model.predict(X_test)

    acc_tun = accuracy_score(y_test_tun, predictions['TUN_State'])
    acc_sn = accuracy_score(y_test_sn, predictions['SN_State'])

    tun_accuracies.append(acc_tun)
    sn_accuracies.append(acc_sn)

    print(f"Index: {fragment_index}")
    print(f"Train indices: [{train_index[0]} to {train_index[-1]}] (Size: {len(train_fragment)})")
    print(f"Test indices:  [{test_index[0]} to {test_index[-1]}] (Size: {len(test_fragment)})\n")

    print("--- TUN_State (Time Until Next Meal) ---")
    print(f"Accuracy: {acc_tun:.4f}")
    print("Classification report:")
    print(classification_report(y_test_tun, predictions['TUN_State']))
    print("\n")

    print("--- SN_State (Size of Next Meal) ---")
    print(f"Accuracy: {acc_sn:.4f}")
    print("Classification Report:")
    print(classification_report(y_test_sn, predictions['SN_State']))
    print("-" * 60 + "\n")

    fragment_index += 1

print(f"Average TUN_State Accuracy: {np.mean(tun_accuracies):.4f}")
print(f'Avergae SN State Accuracy: {np.mean(sn_accuracies):.4f}')

print("\n" + "="*60)
print("Trainning for hole dataset")
print("="*60 + "\n")

final_model = DiscreteBayesianNetwork([
    ('GL_State_Prev', 'GL_State'),
    ('TUN_State_Prev', 'TUN_State'),
    ('TC_Hour', 'TUN_State'),
    ('GL_State', 'TUN_State'),
    ('TP_State', 'TUN_State'),
    ('TUN_State', 'SN_State'),
])

final_model.fit(
    train_df[all_cols],
    estimator=MaximumLikelihoodEstimator
)

infer = VariableElimination(final_model)

def predict_next_meal(current_hour, current_glucose, hours_since_last_meal):
    print(f"--- evidence ---")
    print(f"current time(hour): {current_hour}")
    print(f"current glucose: {current_glucose}")
    print(f"hours since last meal(hours): {hours_since_last_meal}\n")

    gl_state = 1 if current_glucose < 70 else (2 if current_glucose <= 140 else 3)
    tp_state = 1 if hours_since_last_meal < 2 else (2 if hours_since_last_meal <= 4 else 3)

    evidence_dict = {
        'TC_Hour': current_hour,
        'GL_State': gl_state,
        'TP_State': tp_state
    }

    print(">>> Prediction TUN State (1: within one hours, 2:1-3 hours, 3:above 3 hours)")
    res_tun_state = infer.query(variables=['TUN_State'], evidence=evidence_dict)
    print(res_tun_state)

    print(">>> Prediction SN State (1: <=3 means snacks, 2: >3 means normal meal)")
    res_sn_state = infer.query(variables=['SN_State'], evidence=evidence_dict)
    print(res_sn_state)


predict_next_meal(current_hour=14, current_glucose=105, hours_since_last_meal=4.5)

print("-" * 50)

predict_next_meal(current_hour=21, current_glucose=65, hours_since_last_meal=2.5)