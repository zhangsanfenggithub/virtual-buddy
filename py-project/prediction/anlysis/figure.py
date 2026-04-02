
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_csv('../prediction_mock/meal_history.csv')

fig = plt.figure(figsize=(18, 14))
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

# 1. 每小时进食概率
ax1 = fig.add_subplot(gs[0, :2])
hourly_rate = df.groupby('hour')['meal_happened'].mean() * 100
colors = ['#2ecc71' if v > 60 else '#3498db' if v > 30 else '#95a5a6' for v in hourly_rate]
ax1.bar(hourly_rate.index, hourly_rate.values, color=colors)
ax1.set_title('每小时进食概率')
ax1.set_xlabel('小时')
ax1.set_ylabel('进食概率 (%)')
ax1.set_xticks(range(24))

# 3. 碳水量分布（按餐次类型）
ax3 = fig.add_subplot(gs[1, 0])
meal_only = df[df['meal_happened'] == 1]
breakfast = meal_only[meal_only['hour'].between(6, 10)]['carb_amount']
lunch     = meal_only[meal_only['hour'].between(11, 14)]['carb_amount']
dinner    = meal_only[meal_only['hour'].between(17, 21)]['carb_amount']
ax3.hist([breakfast, lunch, dinner], bins=15, label=['早餐', '午餐', '晚餐'],
         color=['#f39c12', '#3498db', '#9b59b6'], alpha=0.7, edgecolor='white')
ax3.set_title('三餐碳水量分布')
ax3.set_xlabel('碳水量 (g)')
ax3.set_ylabel('频次')
ax3.legend()

# 4. 热力图：小时 × 星期 的进食概率
ax4 = fig.add_subplot(gs[1, 1:])
pivot = df.groupby(['day_of_week', 'hour'])['meal_happened'].mean().unstack()
im = ax4.imshow(pivot.values, aspect='auto', cmap='YlOrRd', vmin=0, vmax=1)
ax4.set_xticks(range(24))
ax4.set_xticklabels(range(24), fontsize=8)
ax4.set_yticks(range(7))
ax4.set_yticklabels(['周一','周二','周三','周四','周五','周六','周日'])
ax4.set_title('进食热力图（星期 × 小时）')
ax4.set_xlabel('小时')
plt.colorbar(im, ax=ax4, label='进食概率')

# 5. 每日总碳水趋势（30天）
ax5 = fig.add_subplot(gs[2, :2])
daily_carb = df.groupby('day')['carb_amount'].sum()
ax5.plot(daily_carb.index, daily_carb.values, color='#3498db', linewidth=1.5, marker='o', markersize=3)
ax5.fill_between(daily_carb.index, daily_carb.values, alpha=0.2, color='#3498db')
ax5.axhline(daily_carb.mean(), color='#e74c3c', linestyle='--', label=f'均值: {daily_carb.mean():.0f}g')
ax5.set_title('每日总碳水摄入趋势')
ax5.set_xlabel('天')
ax5.set_ylabel('总碳水 (g)')
ax5.legend()

# 6. 箱线图：各时间段碳水量分布
ax6 = fig.add_subplot(gs[2, 2])
def get_period(h):
    if h < 6:    return '深夜'
    elif h < 10: return '早晨'
    elif h < 14: return '中午'
    elif h < 18: return '下午'
    else:        return '晚上'

meal_only = df[df['meal_happened'] == 1].copy()
meal_only['period'] = meal_only['hour'].apply(get_period)
order = ['深夜', '早晨', '中午', '下午', '晚上']
data_by_period = [meal_only[meal_only['period'] == p]['carb_amount'].values for p in order]
bp = ax6.boxplot(data_by_period, labels=order, patch_artist=True)
colors_box = ['#2c3e50','#f39c12','#3498db','#95a5a6','#9b59b6']
for patch, color in zip(bp['boxes'], colors_box):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
ax6.set_title('各时段碳水量箱线图')
ax6.set_ylabel('碳水量 (g)')

plt.suptitle('进食历史数据多维分析', fontsize=15, fontweight='bold', y=1.01)
plt.savefig('meal_analysis.png', dpi=150, bbox_inches='tight')
plt.show()
