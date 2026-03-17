"""
Correlation Analysis: HVFHV vs MTA Ridership
============================================
This script analyzes correlations between HVFHV trips and MTA ridership at different time scales:
1. Overall daily correlation
2. Day-of-week correlation  
3. Weekday vs weekend correlation
4. Monthly/seasonal correlation
5. Rolling correlation over time
6. Correlation by borough/zone (optional)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from modules import utils

# =============================================================================
# 1. LOAD AND PREPARE DATA
# =============================================================================

def load_and_prepare_data():
    """Load and prepare the data for analysis"""
    
    print("=" * 70)
    print("LOADING AND PREPARING DATA")
    print("=" * 70)
    
    # Load data
    #hvfhv_df, mta_df = utils.prepare_ridership_data()
    mta_df = pd.read_csv('data/02-processed/MTA_Ridership_cleaned.csv')
    #print(mta_df.columns)
    hvfhv_df = pd.read_csv('data/02-processed/ridehailing_daily_cleaned.csv')
    # Convert date columns
    hvfhv_df['date'] = pd.to_datetime(hvfhv_df['date'])
    mta_df['date'] = pd.to_datetime(mta_df['date'])
    
    # Add time features
    hvfhv_df['day_of_week'] = hvfhv_df['date'].dt.day_name()
    hvfhv_df['month'] = hvfhv_df['date'].dt.month
    hvfhv_df['year'] = hvfhv_df['date'].dt.year
    hvfhv_df['is_weekend'] = hvfhv_df['date'].dt.dayofweek.isin([5, 6])
    
    mta_df['day_of_week'] = mta_df['date'].dt.day_name()
    mta_df['month'] = mta_df['date'].dt.month
    mta_df['year'] = mta_df['date'].dt.year
    mta_df['is_weekend'] = mta_df['date'].dt.dayofweek.isin([5, 6])
    
    # Aggregate daily totals
    print("\nAggregating daily totals...")
    hvfhv_daily = hvfhv_df.groupby("date")["trip_count"].sum().reset_index()
    mta_daily = mta_df.groupby("date")["ridership"].sum().reset_index()
    
    # Merge into single dataframe
    daily_df = pd.merge(hvfhv_daily, mta_daily, on="date")
    daily_df = daily_df.sort_values('date')
    
    # Add time features to daily dataframe
    daily_df['day_of_week'] = daily_df['date'].dt.day_name()
    daily_df['month'] = daily_df['date'].dt.month
    daily_df['year'] = daily_df['date'].dt.year
    daily_df['is_weekend'] = daily_df['date'].dt.dayofweek.isin([5, 6])
    daily_df['quarter'] = daily_df['date'].dt.quarter
    
    print(f"Daily data shape: {daily_df.shape}")
    print(f"Date range: {daily_df['date'].min().date()} to {daily_df['date'].max().date()}")
    print(f"Total days: {len(daily_df)}")
    
    return hvfhv_df, mta_df, daily_df


# =============================================================================
# 2. OVERALL CORRELATION
# =============================================================================

def overall_correlation(daily_df):
    """Calculate overall daily correlation"""
    
    print("\n" + "=" * 70)
    print("OVERALL DAILY CORRELATION")
    print("=" * 70)
    
    corr = daily_df["trip_count"].corr(daily_df["ridership"])
    
    print(f"\nPearson correlation coefficient: {corr:.4f}")
    print(f"R-squared: {corr**2:.4f} ({corr**2*100:.1f}% of variance explained)")
    
    # Interpretation
    if abs(corr) < 0.3:
        strength = "weak"
    elif abs(corr) < 0.5:
        strength = "moderate"
    else:
        strength = "strong"
    
    direction = "positive" if corr > 0 else "negative"
    print(f"\nInterpretation: {strength} {direction} correlation")
    
    return corr


# =============================================================================
# 3. DAY OF WEEK CORRELATION
# =============================================================================

def day_of_week_correlation(daily_df):
    """Calculate correlation for each day of week"""
    
    print("\n" + "=" * 70)
    print("DAY OF WEEK CORRELATION")
    print("=" * 70)
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_correlations = {}
    
    print("\nCorrelation by day of week:")
    print("-" * 50)
    
    for day in days:
        day_data = daily_df[daily_df['day_of_week'] == day]
        if len(day_data) > 5:  # Need minimum data points
            corr = day_data['trip_count'].corr(day_data['ridership'])
            dow_correlations[day] = corr
            print(f"  {day:10}: {corr:.4f} (n={len(day_data)} days)")
        else:
            print(f"  {day:10}: Insufficient data")
    
    # Visualize
    fig, ax = plt.subplots(figsize=(10, 6))
    
    days_list = list(dow_correlations.keys())
    corr_list = list(dow_correlations.values())
    colors = ['green' if c > 0 else 'red' for c in corr_list]
    
    bars = ax.bar(days_list, corr_list, color=colors, alpha=0.7)
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
    ax.axhline(y=daily_df['trip_count'].corr(daily_df['ridership']), 
               color='blue', linestyle='--', label=f"Overall: {daily_df['trip_count'].corr(daily_df['ridership']):.3f}")
    
    ax.set_ylabel('Correlation Coefficient')
    ax.set_title('Correlation by Day of Week: HVFHV vs MTA', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
    return dow_correlations


# =============================================================================
# 4. WEEKDAY VS WEEKEND CORRELATION
# =============================================================================

def weekday_weekend_correlation(daily_df):
    """Compare weekday vs weekend correlation"""
    
    print("\n" + "=" * 70)
    print("WEEKDAY VS WEEKEND CORRELATION")
    print("=" * 70)
    
    weekday_data = daily_df[~daily_df['is_weekend']]
    weekend_data = daily_df[daily_df['is_weekend']]
    
    weekday_corr = weekday_data['trip_count'].corr(weekday_data['ridership'])
    weekend_corr = weekend_data['trip_count'].corr(weekend_data['ridership'])
    
    print(f"\nWeekday correlation (Mon-Fri): {weekday_corr:.4f} (n={len(weekday_data)} days)")
    print(f"Weekend correlation (Sat-Sun): {weekend_corr:.4f} (n={len(weekend_data)} days)")
    print(f"Difference: {weekend_corr - weekday_corr:+.4f}")
    
    # Visualize
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Weekdays scatter
    axes[0].scatter(weekday_data['ridership'], weekday_data['trip_count'], 
                    alpha=0.5, color='blue', s=30)
    axes[0].set_xlabel('MTA Ridership')
    axes[0].set_ylabel('HVFHV Trips')
    axes[0].set_title(f'Weekdays (Mon-Fri)\nCorrelation: {weekday_corr:.3f}', fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    
    # Add regression line
    z = np.polyfit(weekday_data['ridership'], weekday_data['trip_count'], 1)
    p = np.poly1d(z)
    axes[0].plot(weekday_data['ridership'].sort_values(), 
                p(weekday_data['ridership'].sort_values()), 
                color='red', linewidth=2)
    
    # Weekends scatter
    axes[1].scatter(weekend_data['ridership'], weekend_data['trip_count'], 
                    alpha=0.5, color='orange', s=30)
    axes[1].set_xlabel('MTA Ridership')
    axes[1].set_ylabel('HVFHV Trips')
    axes[1].set_title(f'Weekends (Sat-Sun)\nCorrelation: {weekend_corr:.3f}', fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    
    # Add regression line
    if len(weekend_data) > 1:
        z = np.polyfit(weekend_data['ridership'], weekend_data['trip_count'], 1)
        p = np.poly1d(z)
        axes[1].plot(weekend_data['ridership'].sort_values(), 
                    p(weekend_data['ridership'].sort_values()), 
                    color='red', linewidth=2)
    
    plt.suptitle('Weekday vs Weekend Relationship', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()
    
    return {'weekday': weekday_corr, 'weekend': weekend_corr}


# =============================================================================
# 5. MONTHLY/SEASONAL CORRELATION
# =============================================================================

def monthly_correlation(daily_df):
    """Calculate correlation by month"""
    
    print("\n" + "=" * 70)
    print("MONTHLY CORRELATION")
    print("=" * 70)
    
    monthly_corrs = {}
    
    for month in range(1, 13):
        month_data = daily_df[daily_df['month'] == month]
        if len(month_data) > 10:  # Need minimum data
            corr = month_data['trip_count'].corr(month_data['ridership'])
            month_name = pd.to_datetime(f'2023-{month}-01').strftime('%B')
            monthly_corrs[month_name] = corr
    
    # Display
    print("\nCorrelation by month:")
    print("-" * 50)
    for month, corr in monthly_corrs.items():
        print(f"  {month:10}: {corr:.4f}")
    
    # Visualize
    fig, ax = plt.subplots(figsize=(14, 5))
    
    months = list(monthly_corrs.keys())
    corrs = list(monthly_corrs.values())
    
    colors = ['green' if c > 0 else 'red' for c in corrs]
    ax.bar(months, corrs, color=colors, alpha=0.7)
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
    ax.axhline(y=daily_df['trip_count'].corr(daily_df['ridership']), 
               color='blue', linestyle='--', label=f"Overall: {daily_df['trip_count'].corr(daily_df['ridership']):.3f}")
    
    ax.set_ylabel('Correlation Coefficient')
    ax.set_title('Monthly Correlation: HVFHV vs MTA', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
    return monthly_corrs


# =============================================================================
# 6. ROLLING CORRELATION
# =============================================================================

def rolling_correlation(daily_df, window=30):
    """Calculate rolling correlation over time"""
    
    print("\n" + "=" * 70)
    print(f"ROLLING CORRELATION ({window}-DAY WINDOW)")
    print("=" * 70)
    
    daily_df = daily_df.sort_values('date')
    daily_df['rolling_corr'] = daily_df['trip_count'].rolling(window).corr(daily_df['ridership'])
    
    # Visualize
    fig, axes = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    
    # Rolling correlation
    axes[0].plot(daily_df['date'], daily_df['rolling_corr'], color='purple', linewidth=2)
    axes[0].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    axes[0].axhline(y=daily_df['trip_count'].corr(daily_df['ridership']), 
                    color='red', linestyle='--', label=f'Overall: {daily_df["trip_count"].corr(daily_df["ridership"]):.3f}')
    axes[0].fill_between(daily_df['date'], 0, daily_df['rolling_corr'], 
                         where=daily_df['rolling_corr']>0, color='green', alpha=0.3)
    axes[0].fill_between(daily_df['date'], daily_df['rolling_corr'], 0, 
                         where=daily_df['rolling_corr']<0, color='red', alpha=0.3)
    axes[0].set_ylabel(f'{window}-Day Rolling Correlation')
    axes[0].set_title(f'Rolling Correlation Over Time', fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Ridership trends
    axes[1].plot(daily_df['date'], daily_df['trip_count']/1e6, label='HVFHV (millions)', color='orange', alpha=0.7)
    axes[1].plot(daily_df['date'], daily_df['ridership']/1e6, label='MTA (millions)', color='blue', alpha=0.7)
    axes[1].set_xlabel('Date')
    axes[1].set_ylabel('Ridership (millions)')
    axes[1].set_title('Ridership Trends', fontweight='bold')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    # Summary stats
    valid_corr = daily_df['rolling_corr'].dropna()
    print(f"\nRolling correlation statistics:")
    print(f"  Mean: {valid_corr.mean():.4f}")
    print(f"  Std: {valid_corr.std():.4f}")
    print(f"  Min: {valid_corr.min():.4f}")
    print(f"  Max: {valid_corr.max():.4f}")
    print(f"  % positive: {(valid_corr > 0).sum() / len(valid_corr) * 100:.1f}%")
    
    return daily_df


# =============================================================================
# 7. CORRELATION BY BOROUGH (requires spatial data)
# =============================================================================

def correlation_by_borough(hvfhv_df, mta_df, taxi_zones_gdf, subway_stations_gdf):
    """Calculate correlation by borough (if spatial data available)"""
    
    print("\n" + "=" * 70)
    print("CORRELATION BY BOROUGH")
    print("=" * 70)
    
    # This would require mapping stations to boroughs and HVFHV zones to boroughs
    # Simplified version - just print placeholder
    print("\nTo calculate borough-level correlation, you would need to:")
    print("  1. Map subway stations to boroughs")
    print("  2. Map HVFHV zones to boroughs") 
    print("  3. Aggregate ridership by borough and date")
    print("  4. Calculate correlation for each borough")
    
    # Placeholder return
    return {}


# =============================================================================
# 8. SUMMARY AND VISUALIZATION
# =============================================================================

def summary_visualization(daily_df, dow_corrs, ww_corrs, monthly_corrs):
    """Create a summary visualization of all correlations"""
    
    print("\n" + "=" * 70)
    print("SUMMARY VISUALIZATION")
    print("=" * 70)
    
    fig = plt.figure(figsize=(16, 10))
    
    # 1. Overall correlation (text)
    ax1 = plt.subplot(3, 3, 1)
    overall = daily_df['trip_count'].corr(daily_df['ridership'])
    ax1.text(0.5, 0.5, f'Overall\nCorrelation\n{overall:.3f}', 
             ha='center', va='center', fontsize=20, fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    ax1.set_axis_off()
    
    # 2. Day of week heatmap
    ax2 = plt.subplot(3, 3, 2)
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_values = [dow_corrs.get(day, 0) for day in days_order]
    
    # Create a horizontal bar chart
    y_pos = np.arange(len(days_order))
    colors = ['green' if c > 0 else 'red' for c in dow_values]
    ax2.barh(y_pos, dow_values, color=colors, alpha=0.7)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(days_order)
    ax2.axvline(x=0, color='black', linewidth=0.5)
    ax2.set_xlabel('Correlation')
    ax2.set_title('By Day of Week', fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='x')
    
    # 3. Weekday/Weekend comparison
    ax3 = plt.subplot(3, 3, 3)
    categories = ['Weekday', 'Weekend']
    values = [ww_corrs.get('weekday', 0), ww_corrs.get('weekend', 0)]
    colors = ['green' if v > 0 else 'red' for v in values]
    ax3.bar(categories, values, color=colors, alpha=0.7)
    ax3.axhline(y=0, color='black', linewidth=0.5)
    ax3.set_ylabel('Correlation')
    ax3.set_title('Weekday vs Weekend', fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. Monthly correlation line plot
    ax4 = plt.subplot(3, 1, 2)
    months = list(monthly_corrs.keys())
    month_corrs = list(monthly_corrs.values())
    ax4.plot(months, month_corrs, marker='o', color='purple', linewidth=2)
    ax4.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax4.axhline(y=overall, color='red', linestyle='--', label=f'Overall: {overall:.3f}')
    ax4.set_ylabel('Correlation')
    ax4.set_title('Monthly Correlation Trend', fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    
    # 5. Distribution of daily values
    ax5 = plt.subplot(3, 3, 7)
    ax5.hist(daily_df['trip_count']/1000, bins=30, alpha=0.7, color='orange', edgecolor='black')
    ax5.set_xlabel('HVFHV Trips (thousands)')
    ax5.set_ylabel('Frequency')
    ax5.set_title('HVFHV Distribution', fontweight='bold')
    ax5.grid(True, alpha=0.3)
    
    ax6 = plt.subplot(3, 3, 8)
    ax6.hist(daily_df['ridership']/1000, bins=30, alpha=0.7, color='blue', edgecolor='black')
    ax6.set_xlabel('MTA Ridership (thousands)')
    ax6.set_ylabel('Frequency')
    ax6.set_title('MTA Distribution', fontweight='bold')
    ax6.grid(True, alpha=0.3)
    
    ax7 = plt.subplot(3, 3, 9)
    ax7.scatter(daily_df['ridership'], daily_df['trip_count'], alpha=0.5, s=20)
    ax7.set_xlabel('MTA Ridership')
    ax7.set_ylabel('HVFHV Trips')
    ax7.set_title(f'Scatter Plot (r={overall:.3f})', fontweight='bold')
    ax7.grid(True, alpha=0.3)
    
    plt.suptitle('HVFHV vs MTA Correlation Analysis Summary', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.show()


# =============================================================================
# 9. MAIN FUNCTION
# =============================================================================

def main():
    """Main function to run all analyses"""
    
    print("\n" + "=" * 70)
    print("HVFHV vs MTA RIDERSHIP CORRELATION ANALYSIS")
    print("=" * 70)
    
    # Load data
    hvfhv_df, mta_df, daily_df = load_and_prepare_data()


    
    # Run analyses
    overall = overall_correlation(daily_df)
    dow_corrs = day_of_week_correlation(daily_df)
    ww_corrs = weekday_weekend_correlation(daily_df)
    monthly_corrs = monthly_correlation(daily_df)
    daily_df_with_rolling = rolling_correlation(daily_df, window=30)
    
    # Summary
    summary_visualization(daily_df, dow_corrs, ww_corrs, monthly_corrs)
    
    # Save results to CSV
    results_df = pd.DataFrame({
        'analysis': ['Overall'] + list(dow_corrs.keys()) + ['Weekday', 'Weekend'] + list(monthly_corrs.keys()),
        'correlation': [overall] + list(dow_corrs.values()) + [ww_corrs['weekday'], ww_corrs['weekend']] + list(monthly_corrs.values())
    })
    results_df.to_csv('correlation_results.csv', index=False)
    print("\nResults saved to 'correlation_results.csv'")
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    
    return {
        'overall': overall,
        'day_of_week': dow_corrs,
        'weekday_weekend': ww_corrs,
        'monthly': monthly_corrs,
        'daily_df': daily_df_with_rolling
    }


# =============================================================================
# 10. RUN THE ANALYSIS
# =============================================================================

if __name__ == "__main__":
    results = main()