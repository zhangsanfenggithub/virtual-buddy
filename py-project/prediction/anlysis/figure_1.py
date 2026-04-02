import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import RangeSlider
import matplotlib.dates as mdates

plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_csv('../data/HUPA0001P.csv', sep=';', parse_dates=['time'])
df = df.sort_values('time').reset_index(drop=True)

fig = plt.figure(figsize=(16, 13))
gs = gridspec.GridSpec(4, 2, hspace=0.5, wspace=0.3,
                       top=0.93, bottom=0.12)

ax1 = fig.add_subplot(gs[0, :])
ax2 = fig.add_subplot(gs[1, :])
ax3 = fig.add_subplot(gs[2, 0])
ax4 = fig.add_subplot(gs[2, 1])
ax4_twin = ax4.twinx()
slider_ax = fig.add_subplot(gs[3, :])

def draw(start_i, end_i):
    d = df.iloc[int(start_i):int(end_i)]
    for ax in [ax1, ax2, ax3, ax4, ax4_twin]:
        ax.cla()

    # Blood glucose
    ax1.plot(d['time'], d['glucose'], color='#e74c3c', linewidth=1.2)
    ax1.axhline(70,  color='orange', linestyle='--', linewidth=0.8, label='Hypoglycemia 70')
    ax1.axhline(180, color='purple', linestyle='--', linewidth=0.8, label='Hyperglycemia 180')
    ax1.fill_between(d['time'], 70, 180, alpha=0.05, color='green')
    meals = d[d['carb_input'] > 0]
    ax1.scatter(meals['time'], meals['glucose'], color='#2ecc71', s=40, zorder=5, label='Meal')
    ax1.set_title('Blood Glucose Curve'); ax1.set_ylabel('mg/dL'); ax1.legend(fontsize=8)

    # Insulin
    ax2.fill_between(d['time'], d['basal_rate'], alpha=0.5, color='#3498db', label='Basal rate')
    bolus = d[d['bolus_volume_delivered'] > 0]
    ax2.bar(bolus['time'], bolus['bolus_volume_delivered'],
            width=0.003, color='#9b59b6', label='Bolus volume', alpha=0.8)
    ax2.set_title('Insulin'); ax2.set_ylabel('U'); ax2.legend(fontsize=8)

    # Calories
    ax3.bar(d['time'], d['calories'], width=0.003, color='#f39c12', alpha=0.7)
    ax3.set_title('Calories'); ax3.set_ylabel('kcal')
    ax3.tick_params(axis='x', rotation=30)

    # Heart rate & Steps
    ax4.plot(d['time'], d['heart_rate'], color='#e74c3c', linewidth=1)
    ax4_twin.fill_between(d['time'], d['steps'], color='#2ecc71', alpha=0.3)
    ax4.set_title('Heart Rate & Steps')
    ax4.set_ylabel('bpm', color='#e74c3c')
    ax4_twin.set_ylabel('Steps', color='#2ecc71')
    ax4.tick_params(axis='x', rotation=30)

    fig.canvas.draw_idle()

# Slider
slider = RangeSlider(slider_ax, 'Time Range', 0, len(df)-1,
                     valinit=(0, len(df)-1), valstep=1)
slider_ax.set_xlabel('← Drag to select time range →')
slider.on_changed(lambda val: draw(val[0], val[1]))

draw(0, len(df)-1)
plt.suptitle('Multi-dimensional Analysis of Diabetes Patient Data', fontsize=14, fontweight='bold')
plt.show()