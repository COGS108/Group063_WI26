import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from modules import graph, utils, maps

"""
Simple histogram: Average ridership by day of week
"""

# Load and aggregate the data
df_hvfhv, df_mta = utils.prepare_ridership_data()

# Aggregate by date
mta_agg = df_mta.groupby('date').agg({'ridership': 'sum'}).reset_index()
hvfhv_agg = df_hvfhv.groupby('date').agg({'trip_count': 'sum'}).reset_index()


# Merge the datasets
merged_df = pd.merge(mta_agg, hvfhv_agg, on='date', how='inner')
merged_df.columns = ['date', 'mta_ridership', 'hvfhv_trips']
merged_df['date'] = pd.to_datetime(merged_df['date'])

# Add day of week
merged_df['day_of_week'] = merged_df['date'].dt.day_name()

# Order days correctly
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Calculate average ridership by day of week
dow_avg = merged_df.groupby('day_of_week')[['mta_ridership', 'hvfhv_trips']].mean().reindex(day_order)

print("=" * 60)
print("AVERAGE RIDERSHIP BY DAY OF WEEK")
print("=" * 60)
print("\nAverage daily ridership:")
print(dow_avg.round(0).astype(int))
print()

# Create the histogram
fig, ax = plt.subplots(figsize=(12, 6))

x = np.arange(len(day_order))
width = 0.35

# Create bars
bars1 = ax.bar(x - width/2, dow_avg['mta_ridership'], width, 
               label='MTA', color='blue', alpha=0.7, edgecolor='black')
bars2 = ax.bar(x + width/2, dow_avg['hvfhv_trips'], width, 
               label='HVFHV', color='orange', alpha=0.7, edgecolor='black')

# Customize the plot
ax.set_xlabel('Day of Week', fontsize=12)
ax.set_ylabel('Average Daily Ridership', fontsize=12)
ax.set_title('Average Ridership by Day of Week: MTA vs HVFHV', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(day_order)
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height/1000)}K', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.show()

# Calculate percentage of weekly ridership by day
print("\n" + "=" * 60)
print("PERCENTAGE OF WEEKLY RIDERSHIP BY DAY")
print("=" * 60)

dow_pct = (dow_avg / dow_avg.sum()) * 100
print("\nPercentage of weekly ridership:")
for day in day_order:
    print(f"  {day:10}: MTA: {dow_pct.loc[day, 'mta_ridership']:.1f}% | HVFHV: {dow_pct.loc[day, 'hvfhv_trips']:.1f}%")

"""
Correlation matrix between public transit and hvfhv with normalized values
"""

# Load and aggregate the data
df_hvfhv, df_mta = utils.prepare_ridership_data()

# Aggregate by date
mta_agg = df_mta.groupby('date').agg({'ridership': 'sum'}).reset_index()
hvfhv_agg = df_hvfhv.groupby('date').agg({'trip_count': 'sum'}).reset_index()

# Merge the datasets
merged_df = pd.merge(mta_agg, hvfhv_agg, on='date', how='inner')
merged_df.columns = ['date', 'mta_ridership', 'hvfhv_trips']

# Normalize the values (z-score normalization)
from scipy import stats

merged_df['mta_normalized'] = (merged_df['mta_ridership'] - merged_df['mta_ridership'].mean()) / merged_df['mta_ridership'].std()
merged_df['hvfhv_normalized'] = (merged_df['hvfhv_trips'] - merged_df['hvfhv_trips'].mean()) / merged_df['hvfhv_trips'].std()

print("=" * 60)
print("CORRELATION ANALYSIS WITH NORMALIZED VALUES")
print("=" * 60)

# Calculate correlation matrix with original values
print("\nOriginal Values Correlation Matrix:")
corr_original = merged_df[['mta_ridership', 'hvfhv_trips']].corr()
print(corr_original.round(4))

# Calculate correlation matrix with normalized values (should be identical)
print("\nNormalized Values Correlation Matrix:")
corr_normalized = merged_df[['mta_normalized', 'hvfhv_normalized']].corr()
print(corr_normalized.round(4))

corr_value = corr_normalized.loc['mta_normalized', 'hvfhv_normalized']
print(f"\nCorrelation between normalized MTA and HVFHV: {corr_value:.4f}")

# Create scatter plot with normalized values
plt.figure(figsize=(10, 8))

# Scatter plot with regression line
sns.regplot(data=merged_df, 
            x='hvfhv_normalized', 
            y='mta_normalized',
            scatter_kws={'alpha':0.5, 's':30, 'color': 'steelblue'},
            line_kws={'color': 'red', 'linewidth': 2})

# Add reference lines
plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
plt.axvline(x=0, color='gray', linestyle='--', alpha=0.5)

# Labels and title
plt.xlabel('HVFHV Trips (Normalized)', fontsize=12)
plt.ylabel('MTA Ridership (Normalized)', fontsize=12)
plt.title(f'MTA vs HVFHV - Normalized Values\nCorrelation: {corr_value:.4f}', 
          fontsize=14, fontweight='bold')

# Add text box with statistics
stats_text = f'Mean MTA: 0\nStd MTA: 1\nMean HVFHV: 0\nStd HVFHV: 1\nn = {len(merged_df)} days'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
plt.text(0.05, 0.95, stats_text, transform=plt.gca().transAxes, fontsize=10,
         verticalalignment='top', bbox=props)

plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# Optional: Create a joint plot with histograms (even nicer visualization)
g = sns.jointplot(data=merged_df, 
                  x='hvfhv_normalized', 
                  y='mta_normalized',
                  kind='reg',
                  height=8,
                  scatter_kws={'alpha':0.5, 's':20},
                  line_kws={'color': 'red'})

g.fig.suptitle(f'MTA vs HVFHV - Normalized Values\nCorrelation: {corr_value:.4f}', 
               y=1.02, fontweight='bold')
g.set_axis_labels('HVFHV Trips (Normalized)', 'MTA Ridership (Normalized)')

# Add reference lines
g.ax_joint.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
g.ax_joint.axvline(x=0, color='gray', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.show()

# Create a comparison of original vs normalized scales
fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# Original scale
axes[0].scatter(merged_df['hvfhv_trips'], merged_df['mta_ridership'], 
                alpha=0.5, s=20, color='steelblue')
axes[0].set_xlabel('HVFHV Trips (Original)', fontsize=11)
axes[0].set_ylabel('MTA Ridership (Original)', fontsize=11)
axes[0].set_title('Original Scale', fontweight='bold')
axes[0].grid(True, alpha=0.3)

# Normalized scale
axes[1].scatter(merged_df['hvfhv_normalized'], merged_df['mta_normalized'], 
                alpha=0.5, s=20, color='steelblue')
axes[1].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
axes[1].axvline(x=0, color='gray', linestyle='--', alpha=0.5)
axes[1].set_xlabel('HVFHV Trips (Normalized)', fontsize=11)
axes[1].set_ylabel('MTA Ridership (Normalized)', fontsize=11)
axes[1].set_title('Normalized Scale (z-scores)', fontweight='bold')
axes[1].grid(True, alpha=0.3)

plt.suptitle(f'Correlation: {corr_value:.4f} (Same in both scales)', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.show()

# Print interpretation
print("\n" + "=" * 60)
print("INTERPRETATION")
print("=" * 60)

# Interpret the correlation
abs_corr = abs(corr_value)
if abs_corr >= 0.7:
    strength = "Strong"
elif abs_corr >= 0.5:
    strength = "Moderate"
elif abs_corr >= 0.3:
    strength = "Weak"
else:
    strength = "Very weak"

direction = "positive" if corr_value > 0 else "negative"
print(f"\n{strength} {direction} correlation ({corr_value:.4f})")

if corr_value > 0:
    print("→ As HVFHV trips increase, MTA ridership tends to increase")
    print("→ This suggests a complementary relationship")
elif corr_value < 0:
    print("→ As HVFHV trips increase, MTA ridership tends to decrease")
    print("→ This suggests a substitution effect")
else:
    print("→ No linear relationship between the two modes")

# Show days with interesting patterns (in normalized space)
print("\nDays with interesting normalized patterns:")
merged_df['abs_diff'] = abs(merged_df['mta_normalized'] - merged_df['hvfhv_normalized'])
interesting_days = merged_df.nlargest(5, 'abs_diff')[['date', 'mta_normalized', 'hvfhv_normalized']]
print("\nTop 5 days with largest divergence (one mode high, other low):")
for _, row in interesting_days.iterrows():
    print(f"  {row['date'].strftime('%Y-%m-%d'):12} | MTA: {row['mta_normalized']:6.2f} | HVFHV: {row['hvfhv_normalized']:6.2f}")



#Map the ebb and flow of both modes across time and space. 
#Maybe generate a gif of thepopularity throughout the day.
#Heatmap of the time of day vs day of week

#Peak Hour comparison
#HVHF might have higher peak at night
#Plot the ratio of HVFHV Trips vs transit ridership on a map of NYC
#Might find areas with high HVFH reliance vs transit

##Identify regions that are accessible to Public transport, and compare inside and outside those regions
#We might see higher hvfh reliance outside the zones

##Quantify how much hvfh usage increases when transit becomes less accessible and vice versa
#Monitor weather and gas

#Do demographic overlay, see if high income areas are more likely to use HVFH



