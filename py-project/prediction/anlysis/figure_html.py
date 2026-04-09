import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title='Analysis', layout='wide')
st.title('Analysis Dashboard')
df = pd.read_csv('../data/HUPA0001P.csv', sep=';', parse_dates=['time'])
df = df.sort_values('time').reset_index(drop=True)

uploaded = st.file_uploader('Upload CSV', type='csv')
if uploaded:
    df = pd.read_csv(uploaded, sep=';', parse_dates=['time'])
    df = df.sort_values('time').reset_index(drop=True)

    # Time range
    col1, col2 = st.columns(2)
    start = col1.date_input('Start Date', df['time'].min())
    end   = col2.date_input('End Date', df['time'].max())
    df = df[(df['time'].dt.date >= start) & (df['time'].dt.date <= end)]

    # Statistical indicators
    meals = df[df['carb_input'] > 0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Average Glucose', f"{df['glucose'].mean():.1f} mg/dL")
    c2.metric('Highest Glucose', f"{df['glucose'].max():.1f} mg/dL")
    c3.metric('Lowest Glucose', f"{df['glucose'].min():.1f} mg/dL")
    c4.metric('Number of Meals', f"{len(meals)}")

    # Blood glucose chart
    st.subheader('blood glucose curve')
    fig1, ax1 = plt.subplots(figsize=(14, 3))
    ax1.plot(df['time'], df['glucose'], color='#e74c3c', linewidth=1)
    ax1.axhline(70,  color='orange', linestyle='--', linewidth=0.8)
    ax1.axhline(180, color='purple', linestyle='--', linewidth=0.8)
    ax1.fill_between(df['time'], 70, 180, alpha=0.05, color='green')
    ax1.scatter(meals['time'], meals['glucose'], color='#3498db', s=30, zorder=5, label='Meal')
    # 1 unit = 10g
    for _, meal in meals.iterrows():
        carb_grams = meal['carb_input'] * 10
        ax1.annotate(f"{carb_grams:.0f}g", 
                    (meal['time'], meal['glucose']),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha='center',
                    fontsize=7,
                    color='#3498db',
                    fontweight='bold')
    ax1.legend(); ax1.set_ylabel('mg/dL')
    st.pyplot(fig1)

    # Insulin
    st.subheader('insulin')
    fig2, ax2 = plt.subplots(figsize=(14, 2.5))
    ax2.fill_between(df['time'], df['basal_rate'], alpha=0.5, color='#3498db', label='Basal rate')
    bolus = df[df['bolus_volume_delivered'] > 0]
    ax2.bar(bolus['time'], bolus['bolus_volume_delivered'], width=0.003, color='#9b59b6', label='Bolus volume')
    ax2.legend(); ax2.set_ylabel('U')
    st.pyplot(fig2)

    # Calories (Energy expenditure rate)
    st.subheader('calorie')
    fig3, ax3 = plt.subplots(figsize=(14, 2.5))
    ax3.bar(df['time'], df['calories'], width=0.003, color='#f39c12')
    ax3.set_ylabel('kcal/5min')
    st.pyplot(fig3)

    # Heart rate & Step count
    st.subheader('heart rate & step count')
    fig4, ax4 = plt.subplots(figsize=(14, 2.5))
    ax4_twin = ax4.twinx()
    ax4.plot(df['time'], df['heart_rate'], color='#e74c3c', linewidth=1, label='Heart Rate')
    ax4_twin.fill_between(df['time'], df['steps'], color='#2ecc71', alpha=0.3, label='Step Count')
    ax4.set_ylabel('bpm', color='#e74c3c')
    ax4_twin.set_ylabel('step count', color='#2ecc71')
    st.pyplot(fig4)