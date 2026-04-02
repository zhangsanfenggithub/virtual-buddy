import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_csv('../prediction_mock/meal_history.csv')

# Generate sleep data (deep sleep period usually 23:00-6:00)
np.random.seed(42)
def get_sleep_depth(hour):
    if 0 <= hour <= 2:   return np.random.uniform(0.6, 1.0)   # Deep sleep
    elif 3 <= hour <= 5: return np.random.uniform(0.3, 0.8)   # Moderate sleep
    elif hour == 6:      return np.random.uniform(0.1, 0.4)   # Light sleep/wake up
    elif 23 == hour:     return np.random.uniform(0.1, 0.5)   # Initial sleep stage
    else:                return 0.0                            # Awake

df['sleep_depth'] = df['hour'].apply(get_sleep_depth)
df['period'] = pd.cut(df['hour'], bins=[-1,5,9,13,17,21,23],
                       labels=['Late Night','Morning','Noon','Afternoon','Evening','Night'])

fig = plt.figure(figsize=(18, 14))

# ── 1. 3D Bar Chart: Hour × Day of Week × Meal Probability ──
ax1 = fig.add_subplot(221, projection='3d')
pivot = df.groupby(['day_of_week', 'hour'])['meal_happened'].mean().reset_index()
xpos = pivot['hour'].values
ypos = pivot['day_of_week'].values
zpos = np.zeros(len(pivot))
dz   = pivot['meal_happened'].values
colors = plt.cm.RdYlGn(dz)
ax1.bar3d(xpos, ypos, zpos, dx=0.6, dy=0.6, dz=dz, color=colors, alpha=0.8)
ax1.set_xlabel('Hour', fontsize=9)
ax1.set_ylabel('Day of Week', fontsize=9)
ax1.set_zlabel('Meal Probability', fontsize=9)
ax1.set_yticks(range(7))
ax1.set_yticklabels(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], fontsize=8)
ax1.set_title('3D Meal Probability\n(Hour×Day of Week)', fontsize=10)

# ── 2. 3D Scatter Plot: Hour × Carbohydrate × Sleep Depth ──
ax2 = fig.add_subplot(222, projection='3d')
meal_df = df[df['meal_happened'] == 1]
sc = ax2.scatter(meal_df['hour'], meal_df['carb_amount'], meal_df['sleep_depth'],
                 c=meal_df['sleep_depth'], cmap='coolwarm', s=15, alpha=0.6)
plt.colorbar(sc, ax=ax2, label='Sleep Depth', shrink=0.5)
ax2.set_xlabel('Hour', fontsize=9)
ax2.set_ylabel('Carbohydrate(g)', fontsize=9)
ax2.set_zlabel('Sleep Depth', fontsize=9)
ax2.set_title('3D Meal×Sleep Relationship\n(Hour×Carb×Sleep)', fontsize=10)

# ── 3. 3D Surface Plot: Hour × Day of Week → Average Carbohydrate ──
ax3 = fig.add_subplot(223, projection='3d')
pivot_carb = df[df['meal_happened']==1].groupby(['day_of_week','hour'])['carb_amount'].mean().unstack(fill_value=0)
X, Y = np.meshgrid(pivot_carb.columns, pivot_carb.index)
Z = pivot_carb.values
surf = ax3.plot_surface(X, Y, Z, cmap='viridis', alpha=0.85)
plt.colorbar(surf, ax=ax3, label='Carbohydrate(g)', shrink=0.5)
ax3.set_xlabel('Hour', fontsize=9)
ax3.set_ylabel('Day of Week', fontsize=9)
ax3.set_zlabel('Carbohydrate(g)', fontsize=9)
ax3.set_yticks(range(7))
ax3.set_yticklabels(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], fontsize=8)
ax3.set_title('3D Carbohydrate Surface\n(Hour×Day of Week)', fontsize=10)

# ── 4. 3D Bar Chart: Time Period × Sleep Depth × Meal Count ──
ax4 = fig.add_subplot(224, projection='3d')
sleep_bins = [0, 0.2, 0.5, 0.8, 1.01]
sleep_labels = ['Awake','Light Sleep','Moderate Sleep','Deep Sleep']
df['sleep_level'] = pd.cut(df['sleep_depth'], bins=sleep_bins, labels=sleep_labels)
period_order = ['Late Night','Morning','Noon','Afternoon','Evening','Night']
cross = df[df['meal_happened']==1].groupby(
    ['period','sleep_level'], observed=True)['meal_happened'].count().unstack(fill_value=0)
cross = cross.reindex(period_order).fillna(0)

_x = np.arange(len(cross.index))
_y = np.arange(len(cross.columns))
_xx, _yy = np.meshgrid(_x, _y)
x_flat, y_flat = _xx.ravel(), _yy.ravel()
z_flat = np.zeros_like(x_flat)
dz_flat = cross.values.T.ravel()
c_map = plt.cm.plasma(dz_flat / max(dz_flat.max(), 1))
ax4.bar3d(x_flat, y_flat, z_flat, 0.5, 0.5, dz_flat, color=c_map, alpha=0.8)
ax4.set_xticks(_x)
ax4.set_xticklabels(period_order, fontsize=7, rotation=15)
ax4.set_yticks(_y)
ax4.set_yticklabels(sleep_labels, fontsize=8)
ax4.set_zlabel('Meal Count', fontsize=9)
ax4.set_title('3D Time Period×Sleep Depth\n×Meal Count', fontsize=10)

plt.suptitle('Multi-dimensional 3D Analysis of Meal & Sleep', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('meal_3d_analysis.png', dpi=150, bbox_inches='tight')
plt.show()
print("✅ Saved to meal_3d_analysis.png")