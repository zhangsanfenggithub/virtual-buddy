import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_csv('meal_history.csv')

# 生成睡眠数据（深眠时段通常 23:00-6:00）
np.random.seed(42)
def get_sleep_depth(hour):
    if 0 <= hour <= 2:   return np.random.uniform(0.6, 1.0)   # 深眠
    elif 3 <= hour <= 5: return np.random.uniform(0.3, 0.8)   # 中度睡眠
    elif hour == 6:      return np.random.uniform(0.1, 0.4)   # 浅睡/醒来
    elif 23 == hour:     return np.random.uniform(0.1, 0.5)   # 入睡初期
    else:                return 0.0                            # 清醒

df['sleep_depth'] = df['hour'].apply(get_sleep_depth)
df['period'] = pd.cut(df['hour'], bins=[-1,5,9,13,17,21,23],
                       labels=['深夜','早晨','中午','下午','晚上','夜间'])

fig = plt.figure(figsize=(18, 14))

# ── 1. 3D柱状图：小时 × 星期 × 进食概率 ──
ax1 = fig.add_subplot(221, projection='3d')
pivot = df.groupby(['day_of_week', 'hour'])['meal_happened'].mean().reset_index()
xpos = pivot['hour'].values
ypos = pivot['day_of_week'].values
zpos = np.zeros(len(pivot))
dz   = pivot['meal_happened'].values
colors = plt.cm.RdYlGn(dz)
ax1.bar3d(xpos, ypos, zpos, dx=0.6, dy=0.6, dz=dz, color=colors, alpha=0.8)
ax1.set_xlabel('小时', fontsize=9)
ax1.set_ylabel('星期', fontsize=9)
ax1.set_zlabel('进食概率', fontsize=9)
ax1.set_yticks(range(7))
ax1.set_yticklabels(['一','二','三','四','五','六','日'], fontsize=8)
ax1.set_title('3D 进食概率\n(小时×星期)', fontsize=10)

# ── 2. 3D散点图：小时 × 碳水量 × 睡眠深度 ──
ax2 = fig.add_subplot(222, projection='3d')
meal_df = df[df['meal_happened'] == 1]
sc = ax2.scatter(meal_df['hour'], meal_df['carb_amount'], meal_df['sleep_depth'],
                 c=meal_df['sleep_depth'], cmap='coolwarm', s=15, alpha=0.6)
plt.colorbar(sc, ax=ax2, label='睡眠深度', shrink=0.5)
ax2.set_xlabel('小时', fontsize=9)
ax2.set_ylabel('碳水量(g)', fontsize=9)
ax2.set_zlabel('睡眠深度', fontsize=9)
ax2.set_title('3D 进食×睡眠关系\n(小时×碳水×睡眠)', fontsize=10)

# ── 3. 3D曲面图：小时 × 星期 → 平均碳水量 ──
ax3 = fig.add_subplot(223, projection='3d')
pivot_carb = df[df['meal_happened']==1].groupby(['day_of_week','hour'])['carb_amount'].mean().unstack(fill_value=0)
X, Y = np.meshgrid(pivot_carb.columns, pivot_carb.index)
Z = pivot_carb.values
surf = ax3.plot_surface(X, Y, Z, cmap='viridis', alpha=0.85)
plt.colorbar(surf, ax=ax3, label='碳水量(g)', shrink=0.5)
ax3.set_xlabel('小时', fontsize=9)
ax3.set_ylabel('星期', fontsize=9)
ax3.set_zlabel('碳水量(g)', fontsize=9)
ax3.set_yticks(range(7))
ax3.set_yticklabels(['一','二','三','四','五','六','日'], fontsize=8)
ax3.set_title('3D 碳水曲面\n(小时×星期)', fontsize=10)

# ── 4. 3D柱状图：时间段 × 睡眠深度 × 进食次数 ──
ax4 = fig.add_subplot(224, projection='3d')
sleep_bins = [0, 0.2, 0.5, 0.8, 1.01]
sleep_labels = ['清醒','浅睡','中睡','深眠']
df['sleep_level'] = pd.cut(df['sleep_depth'], bins=sleep_bins, labels=sleep_labels)
period_order = ['深夜','早晨','中午','下午','晚上','夜间']
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
ax4.set_zlabel('进食次数', fontsize=9)
ax4.set_title('3D 时间段×睡眠深度\n×进食次数', fontsize=10)

plt.suptitle('进食 & 睡眠 多维3D分析', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('meal_3d_analysis.png', dpi=150, bbox_inches='tight')
plt.show()
print("✅ 已保存到 meal_3d_analysis.png")