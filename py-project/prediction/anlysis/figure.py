
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_csv('../prediction_mock/meal_history.csv')

fig = plt.figure(figsize=(18, 14))
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

# 1. Hourly meal probability
ax1 = fig.add_subplot(gs[0, :2])
hourly_rate = df.groupby('hour')['meal_happened'].mean() * 100
colors = ['#2ecc71' if v > 60 else '#3498db' if v > 30 else '#95a5a6' for v in hourly_rate]
ax1.bar(hourly_rate.index, hourly_rate.values, color=colors)
ax1.set_title('Hourly Meal Probability')
ax1.set_xlabel('Hour')
ax1.set_ylabel('Meal Probability (%)')
ax1.set_xticks(range(24))

# 3. 碳水量分布（按餐次类型）
ax3 = fig.add_subplot(gs[1, 0])
meal_only = df[df['meal_happened'] == 1]
breakfast = meal_only[meal_only['hour'].between(6, 10)]['carb_amount']
lunch     = meal_only[meal_only['hour'].between(11, 14)]['carb_amount']
dinner    = meal_only[meal_only['hour'].between(17, 21)]['carb_amount']
ax3.hist([breakfast, lunch, dinner], bins=15, label=['Breakfast', 'Lunch', 'Dinner'],
         color=['#f39c12', '#3498db', '#9b59b6'], alpha=0.7, edgecolor='white')
ax3.set_title('Carbohydrate Distribution by Meal Type')
ax3.set_xlabel('Carbohydrate (g)')
ax3.set_ylabel('Frequency')
ax3.legend()

# 4. Heatmap: Hour × Day of Week Meal Probability
ax4 = fig.add_subplot(gs[1, 1:])
pivot = df.groupby(['day_of_week', 'hour'])['meal_happened'].mean().unstack()
im = ax4.imshow(pivot.values, aspect='auto', cmap='YlOrRd', vmin=0, vmax=1)
ax4.set_xticks(range(24))
ax4.set_xticklabels(range(24), fontsize=8)
ax4.set_yticks(range(7))
ax4.set_yticklabels(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])
ax4.set_title('Meal Heatmap (Day of Week × Hour)')
ax4.set_xlabel('Hour')
plt.colorbar(im, ax=ax4, label='Meal Probability')

# 5. Daily total carbohydrate trend (30 days)
ax5 = fig.add_subplot(gs[2, :2])
daily_carb = df.groupby('day')['carb_amount'].sum()
ax5.plot(daily_carb.index, daily_carb.values, color='#3498db', linewidth=1.5, marker='o', markersize=3)
ax5.fill_between(daily_carb.index, daily_carb.values, alpha=0.2, color='#3498db')
ax5.axhline(daily_carb.mean(), color='#e74c3c', linestyle='--', label=f'Average: {daily_carb.mean():.0f}g')
ax5.set_title('Daily Total Carbohydrate Intake Trend')
ax5.set_xlabel('Day')
ax5.set_ylabel('Total Carbohydrate (g)')
ax5.legend()

# 6. Box plot: Carbohydrate distribution by time period
ax6 = fig.add_subplot(gs[2, 2])
def get_period(h):
    if h < 6:    return 'Late Night'
    elif h < 10: return 'Morning'
    elif h < 14: return 'Noon'
    elif h < 18: return 'Afternoon'
    else:        return 'Evening'

meal_only = df[df['meal_happened'] == 1].copy()
meal_only['period'] = meal_only['hour'].apply(get_period)
order = ['Late Night', 'Morning', 'Noon', 'Afternoon', 'Evening']
data_by_period = [meal_only[meal_only['period'] == p]['carb_amount'].values for p in order]
bp = ax6.boxplot(data_by_period, labels=order, patch_artist=True)
colors_box = ['#2c3e50','#f39c12','#3498db','#95a5a6','#9b59b6']
for patch, color in zip(bp['boxes'], colors_box):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
ax6.set_title('Carbohydrate Box Plot by Time Period')
ax6.set_ylabel('Carbohydrate (g)')

plt.suptitle('Multi-dimensional Analysis of Meal History Data', fontsize=15, fontweight='bold', y=1.01)
plt.savefig('meal_analysis.png', dpi=150, bbox_inches='tight')
plt.show()
