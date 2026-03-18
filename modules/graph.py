import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime

#Archive
def create_popularity_histogram(df_combined, df_mta, month):
    """
    Create histograms comparing the most popular pickup zones and MTA stations for a given month.
    
    Parameters:
    df_combined (DataFrame): Combined ridership data with columns ['date', 'PULocationID', 'trip_count']
    df_mta (DataFrame): MTA subway data
    month (int): Month to analyze (1-12)
    """
    
    # Process combined TLC data
    df_combined['date'] = pd.to_datetime(df_combined['date'])
    df_combined['month'] = df_combined['date'].dt.month
    
    # Filter for specific month
    tlc_month = df_combined[df_combined['month'] == month]
    
    # Process MTA data
    df_mta['date'] = pd.to_datetime(df_mta['date'])
    df_mta['month'] = df_mta['date'].dt.month
    
    # Filter for specific month
    mta_month = df_mta[df_mta['month'] == month]
    
    # Get top 10 locations for each
    tlc_top = tlc_month.groupby('PULocationID')['trip_count'].sum().sort_values(ascending=False).head(10)
    mta_top = mta_month.groupby('station_complex_id')['ridership'].sum().sort_values(ascending=False).head(10)
    
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # TLC histogram
    ax1.bar(range(len(tlc_top)), tlc_top.values, color='skyblue', edgecolor='navy')
    ax1.set_xlabel('Pickup Location ID')
    ax1.set_ylabel('Total Trip Count')
    ax1.set_title(f'Top 10 Pickup Zones (All TLC Services) - Month {month}')
    ax1.set_xticks(range(len(tlc_top)))
    ax1.set_xticklabels(tlc_top.index, rotation=45)
    
    # Add value labels
    for i, (idx, val) in enumerate(tlc_top.items()):
        ax1.text(i, val + max(tlc_top.values)*0.01, f'{val:,.0f}', 
                ha='center', va='bottom', fontsize=9)
    
    # MTA histogram
    ax2.bar(range(len(mta_top)), mta_top.values, color='lightcoral', edgecolor='darkred')
    ax2.set_xlabel('Station Complex ID')
    ax2.set_ylabel('Total Ridership')
    ax2.set_title(f'Top 10 MTA Stations - Month {month}')
    ax2.set_xticks(range(len(mta_top)))
    ax2.set_xticklabels(mta_top.index, rotation=45)
    
    # Add value labels
    for i, (idx, val) in enumerate(mta_top.items()):
        ax2.text(i, val + max(mta_top.values)*0.01, f'{val:,.0f}', 
                ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.show()
    
    # Print summary
    print(f"\n=== Month {month} Summary ===")
    print(f"Total TLC trips: {tlc_month['trip_count'].sum():,.0f}")
    print(f"Total MTA ridership: {mta_month['ridership'].sum():,.0f}")
    print(f"Busiest pickup zone: Zone {tlc_top.index[0]} ({tlc_top.values[0]:,.0f} trips)")
    print(f"Busiest MTA station: Station {mta_top.index[0]} ({mta_top.values[0]:,.0f} riders)")

#Archive
def compare_daily_patterns(df_combined, df_mta, zone_id, station_complex_id, 
                          start_date=None, end_date=None,
                          figsize=(15, 8), save_path=None):
    """
    Create daily time series comparison for a specific taxi zone and MTA station.
    
    Parameters:
    -----------
    df_combined (DataFrame): Combined TLC data with columns:
                             date, PULocationID, trip_count
    df_mta (DataFrame): MTA subway data with columns:
                       station_complex_id, date, ridership
    zone_id (int/str): Taxi zone ID to analyze
    station_id (int/str): MTA station complex ID to analyze
    start_date (str, optional): Start date in 'YYYY-MM-DD' format
    end_date (str, optional): End date in 'YYYY-MM-DD' format
    figsize (tuple): Figure size
    save_path (str, optional): Path to save the figure
    
    Returns:
    --------
    fig, (ax1, ax2, ax3): matplotlib figure and axes objects
    """
    
    # Create copies to avoid modifying original data
    tlc = df_combined.copy()
    mta = df_mta.copy()
    
    # Process TLC data
    tlc['date'] = pd.to_datetime(tlc['date'])
    
    # Filter for specific zone (PULocationID is already string)
    zone_data = tlc[tlc['PULocationID'] == str(zone_id)].copy()
    
    # Process MTA data
    mta['date'] = pd.to_datetime(mta['date'])
    
    # Filter for specific station
    station_data = mta[mta['station_complex_id'].astype(str) == str(station_complex_id)].copy()
    
    # Apply date filters if provided
    if start_date:
        start_date = pd.to_datetime(start_date)
        zone_data = zone_data[zone_data['date'] >= start_date]
        station_data = station_data[station_data['date'] >= start_date]
    
    if end_date:
        end_date = pd.to_datetime(end_date)
        zone_data = zone_data[zone_data['date'] <= end_date]
        station_data = station_data[station_data['date'] <= end_date]
    
    # Aggregate by date (in case of multiple entries per day)
    zone_daily = zone_data.groupby('date')['trip_count'].sum().reset_index()
    zone_daily = zone_daily.sort_values('date')
    
    station_daily = station_data.groupby('date')['ridership'].sum().reset_index()
    station_daily = station_daily.sort_values('date')
    
    # Check if we have data
    if len(zone_daily) == 0:
        print(f"Warning: No TLC data found for zone {zone_id}")
    if len(station_daily) == 0:
        print(f"Warning: No MTA data found for station {station_complex_id}")
    
    # Create the plot
    fig, axes = plt.subplots(3, 1, figsize=figsize, height_ratios=[2, 2, 1])
    fig.suptitle(f'Daily Comparison: Taxi Zone {zone_id} vs MTA Station {station_complex_id}', 
                 fontsize=16, fontweight='bold', y=0.95)
    
    # Colors
    color_tlc = '#1f77b4'  # Blue
    color_mta = '#ff7f0e'  # Orange
    
    # 1️⃣ Top plot: TLC trips
    ax1 = axes[0]
    if len(zone_daily) > 0:
        ax1.plot(zone_daily['date'], zone_daily['trip_count'], 
                color=color_tlc, linewidth=2, marker='o', markersize=4,
                label=f'Zone {zone_id} Trips')
        
        # Add moving average (7-day)
        zone_daily['ma_7'] = zone_daily['trip_count'].rolling(window=7, center=True).mean()
        ax1.plot(zone_daily['date'], zone_daily['ma_7'], 
                color='darkblue', linewidth=2, linestyle='--',
                label='7-day Moving Average')
        
        # Fill between to show variation
        ax1.fill_between(zone_daily['date'], 0, zone_daily['trip_count'], 
                        alpha=0.3, color=color_tlc)
    
    ax1.set_ylabel('Number of Trips', fontsize=12)
    ax1.set_title(f'Daily TLC Trips (All Services) - Zone {zone_id}', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # Format x-axis dates
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax1.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    
    # 2️⃣ Middle plot: MTA ridership
    ax2 = axes[1]
    if len(station_daily) > 0:
        ax2.plot(station_daily['date'], station_daily['ridership'], 
                color=color_mta, linewidth=2, marker='s', markersize=4,
                label=f'Station {station_complex_id} Ridership')
        
        # Add moving average (7-day)
        station_daily['ma_7'] = station_daily['ridership'].rolling(window=7, center=True).mean()
        ax2.plot(station_daily['date'], station_daily['ma_7'], 
                color='darkorange', linewidth=2, linestyle='--',
                label='7-day Moving Average')
        
        # Fill between
        ax2.fill_between(station_daily['date'], 0, station_daily['ridership'], 
                        alpha=0.3, color=color_mta)
    
    ax2.set_ylabel('Number of Riders', fontsize=12)
    ax2.set_title(f'Daily MTA Ridership - Station {station_complex_id}', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax2.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    
    # 3️⃣ Bottom plot: Normalized comparison
    ax3 = axes[2]
    
    if len(zone_daily) > 0 and len(station_daily) > 0:
        # Merge the two datasets
        merged = pd.merge(zone_daily[['date', 'trip_count']], 
                         station_daily[['date', 'ridership']], 
                         on='date', how='inner')
        
        if len(merged) > 0:
            # Normalize to percentage of max
            merged['tlc_norm'] = merged['trip_count'] / merged['trip_count'].max() * 100
            merged['mta_norm'] = merged['ridership'] / merged['ridership'].max() * 100
            
            ax3.plot(merged['date'], merged['tlc_norm'], 
                    color=color_tlc, linewidth=2, label=f'Zone {zone_id} (normalized)')
            ax3.plot(merged['date'], merged['mta_norm'], 
                    color=color_mta, linewidth=2, label=f'Station {station_complex_id} (normalized)')
            
            # Find correlation
            correlation = merged['tlc_norm'].corr(merged['mta_norm'])
            ax3.text(0.02, 0.95, f'Correlation: {correlation:.3f}', 
                    transform=ax3.transAxes, fontsize=11,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
    
    ax3.set_ylabel('Normalized Value (% of max)', fontsize=12)
    ax3.set_xlabel('Date', fontsize=12)
    ax3.set_title('Normalized Comparison (100% = max value)', fontsize=12, fontweight='bold')
    ax3.legend(loc='upper right')
    ax3.grid(True, alpha=0.3)
    
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax3.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    
    # Rotate date labels for all subplots
    for ax in axes:
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Print statistics
    print(f"\n📊 Daily Comparison Statistics: Zone {zone_id} vs Station {station_id}")
    print("=" * 60)
    
    if len(zone_daily) > 0:
        print(f"\n🚕 TLC Zone {zone_id} (All Services):")
        print(f"  - Total trips: {zone_daily['trip_count'].sum():,.0f}")
        print(f"  - Daily average: {zone_daily['trip_count'].mean():,.1f}")
        print(f"  - Peak day: {zone_daily.loc[zone_daily['trip_count'].idxmax(), 'date'].strftime('%Y-%m-%d')} "
              f"({zone_daily['trip_count'].max():,.0f} trips)")
        print(f"  - Lowest day: {zone_daily.loc[zone_daily['trip_count'].idxmin(), 'date'].strftime('%Y-%m-%d')} "
              f"({zone_daily['trip_count'].min():,.0f} trips)")
        print(f"  - Standard deviation: {zone_daily['trip_count'].std():,.1f}")
    
    if len(station_daily) > 0:
        print(f"\n🚇 MTA Station {station_complex_id}:")
        print(f"  - Total ridership: {station_daily['ridership'].sum():,.0f}")
        print(f"  - Daily average: {station_daily['ridership'].mean():,.1f}")
        print(f"  - Peak day: {station_daily.loc[station_daily['ridership'].idxmax(), 'date'].strftime('%Y-%m-%d')} "
              f"({station_daily['ridership'].max():,.0f} riders)")
        print(f"  - Lowest day: {station_daily.loc[station_daily['ridership'].idxmin(), 'date'].strftime('%Y-%m-%d')} "
              f"({station_daily['ridership'].min():,.0f} riders)")
        print(f"  - Standard deviation: {station_daily['ridership'].std():,.1f}")
    
    # Day of week analysis
    if len(zone_daily) > 0 and len(station_daily) > 0:
        print(f"\n📅 Day of Week Patterns:")
        
        zone_daily['dayofweek'] = zone_daily['date'].dt.dayofweek
        station_daily['dayofweek'] = station_daily['date'].dt.dayofweek
        
        zone_dow = zone_daily.groupby('dayofweek')['trip_count'].mean()
        station_dow = station_daily.groupby('dayofweek')['ridership'].mean()
        
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        print(f"\n  Day        | Zone {zone_id} (avg) | Station {station_complex_id} (avg)")
        print("-" * 50)
        for i, day in enumerate(days):
            print(f"  {day:<10} | {zone_dow[i]:>12,.0f} | {station_dow[i]:>12,.0f}")
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\n💾 Figure saved to: {save_path}")
    
    plt.show()
    
    return fig, (ax1, ax2, ax3)

#Archive
def compare_multiple_daily(df_combined, df_mta, zone_ids, station_ids,
                          start_date=None, end_date=None,
                          figsize=(15, 10), save_path=None):
    """
    Compare multiple zones and stations on the same plot.
    
    Parameters:
    -----------
    df_combined (DataFrame): Combined TLC data with columns:
                             date, PULocationID, trip_count
    df_mta (DataFrame): MTA subway data with columns:
                       station_complex_id, date, ridership
    zone_ids: list - List of zone IDs to compare
    station_ids: list - List of station IDs to compare
    start_date (str, optional): Start date in 'YYYY-MM-DD' format
    end_date (str, optional): End date in 'YYYY-MM-DD' format
    figsize (tuple): Figure size
    save_path (str, optional): Path to save the figure
    """
    
    # Process data
    tlc = df_combined.copy()
    mta = df_mta.copy()
    
    # Convert dates
    tlc['date'] = pd.to_datetime(tlc['date'])
    mta['date'] = pd.to_datetime(mta['date'])
    
    # Apply date filters if provided
    if start_date:
        start_date = pd.to_datetime(start_date)
        tlc = tlc[tlc['date'] >= start_date]
        mta = mta[mta['date'] >= start_date]
    
    if end_date:
        end_date = pd.to_datetime(end_date)
        tlc = tlc[tlc['date'] <= end_date]
        mta = mta[mta['date'] <= end_date]
    
    fig, axes = plt.subplots(2, 1, figsize=figsize)
    
    # Color maps
    colors_tlc = plt.cm.Blues(np.linspace(0.4, 0.9, len(zone_ids)))
    colors_mta = plt.cm.Oranges(np.linspace(0.4, 0.9, len(station_ids)))
    
    # Plot TLC zones
    ax1 = axes[0]
    for i, zone_id in enumerate(zone_ids):
        zone_data = tlc[tlc['PULocationID'] == str(zone_id)]
        zone_daily = zone_data.groupby('date')['trip_count'].sum().reset_index()
        zone_daily = zone_daily.sort_values('date')
        
        if len(zone_daily) > 0:
            ax1.plot(zone_daily['date'], zone_daily['trip_count'], 
                    color=colors_tlc[i], linewidth=2, 
                    label=f'Zone {zone_id}')
    
    ax1.set_ylabel('Number of Trips', fontsize=12)
    ax1.set_title('TLC Zones Comparison (All Services)', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # Format dates
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax1.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    
    # Plot MTA stations
    ax2 = axes[1]
    for i, station_id in enumerate(station_ids):
        station_data = mta[mta['station_complex_id'].astype(str) == str(station_id)]
        station_daily = station_data.groupby('date')['ridership'].sum().reset_index()
        station_daily = station_daily.sort_values('date')
        
        if len(station_daily) > 0:
            ax2.plot(station_daily['date'], station_daily['ridership'], 
                    color=colors_mta[i], linewidth=2, 
                    label=f'Station {station_id}')
    
    ax2.set_ylabel('Number of Riders', fontsize=12)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_title('MTA Stations Comparison', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax2.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    
    # Rotate date labels
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Print summary
    print(f"\n📊 Multiple Comparison Summary")
    print("=" * 60)
    
    for zone_id in zone_ids:
        zone_total = tlc[tlc['PULocationID'] == str(zone_id)]['trip_count'].sum()
        print(f"🚕 Zone {zone_id}: {zone_total:,.0f} total trips")
    
    print()
    for station_id in station_ids:
        station_total = mta[mta['station_complex_id'].astype(str) == str(station_id)]['ridership'].sum()
        print(f"🚇 Station {station_id}: {station_total:,.0f} total riders")
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\n💾 Figure saved to: {save_path}")
    
    plt.show()
    
    return fig, (ax1, ax2)


def plot_ridership_histogram(mta_df, ridehail_df, plot_type='both'):
    """
    Plot ridership analysis with option to choose plot type
    
    Parameters:
    -----------
    plot_type: str - 'bar', 'correlation', or 'both'
    """
    from scipy import stats
    
    # Data preparation (same for both)
    mta_agg = mta_df.groupby('date').agg({'ridership': 'sum'}).reset_index()
    hvfhv_agg = ridehail_df.groupby('date').agg({'trip_count': 'sum'}).reset_index()

    merged_df = pd.merge(mta_agg, hvfhv_agg, on='date', how='inner')
    merged_df.columns = ['date', 'mta_ridership', 'hvfhv_trips']
    merged_df['date'] = pd.to_datetime(merged_df['date'])
    merged_df['day_of_week'] = merged_df['date'].dt.day_name()
    
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    if plot_type == 'bar' or plot_type == 'both':
        # Bar chart
        dow_avg = merged_df.groupby('day_of_week')[['mta_ridership', 'hvfhv_trips']].mean().reindex(day_order)
        
        bar_fig, ax = plt.subplots(figsize=(12, 6))
        x = np.arange(len(day_order))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, dow_avg['mta_ridership'], width, 
                       label='MTA', color='blue', alpha=0.7, edgecolor='black')
        bars2 = ax.bar(x + width/2, dow_avg['hvfhv_trips'], width, 
                       label='HVFHV', color='orange', alpha=0.7, edgecolor='black')
        
        ax.set_xlabel('Day of Week', fontsize=12)
        ax.set_ylabel('Average Daily Ridership', fontsize=12)
        ax.set_title('Average Ridership by Day of Week', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(day_order, rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height/1000)}K', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        #plt.show()
    
    if plot_type == 'correlation' or plot_type == 'both':
        # Correlation plot with p-values
        dow_corr = {}
        dow_pvalue = {}
        for day in day_order:
            day_data = merged_df[merged_df['day_of_week'] == day]
            if len(day_data) > 1:
                corr, pval = stats.pearsonr(day_data['hvfhv_trips'], day_data['mta_ridership'])
                dow_corr[day] = corr
                dow_pvalue[day] = pval
        
        corr_fig, ax = plt.subplots(figsize=(14, 7))  # Slightly wider for p-value annotations
        x = np.arange(len(day_order))
        corr_values = [dow_corr.get(day, np.nan) for day in day_order]
        
        # Color bars based on correlation strength and significance
        colors = []
        for i, day in enumerate(day_order):
            if day in dow_corr:
                pval = dow_pvalue[day]
                corr = dow_corr[day]
                # Dark green for strong significant correlation, lighter for non-significant
                if pval < 0.01:
                    colors.append('darkgreen' if abs(corr) > 0.5 else 'lightgreen')
                elif pval < 0.05:
                    colors.append('green' if abs(corr) > 0.5 else 'limegreen')
                elif pval < 0.1:
                    colors.append('orange' if abs(corr) > 0.3 else 'gold')
                else:
                    colors.append('lightcoral' if abs(corr) < 0.3 else 'salmon')
            else:
                colors.append('gray')
        
        bars = ax.bar(x, corr_values, color=colors, alpha=0.7, edgecolor='black')
        
        # Reference lines
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.axhline(y=0.3, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
        ax.axhline(y=-0.3, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
        
        ax.set_xlabel('Day of Week', fontsize=12)
        ax.set_ylabel('Correlation Coefficient', fontsize=12)
        ax.set_title('Correlation by Day of Week with P-Values', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(day_order, rotation=45)
        ax.set_ylim([-1.2, 1.3])  # Extra space at top for p-values
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add correlation values and p-values
        for i, (bar, day) in enumerate(zip(bars, day_order)):
            if day in dow_corr:
                height = bar.get_height()
                corr_val = dow_corr[day]
                p_val = dow_pvalue[day]
                
                # Format p-value with scientific notation for very small values
                if p_val < 0.001:
                    p_text = f'p={p_val:.2e}'
                else:
                    p_text = f'p={p_val:.3f}'
                
                # Add correlation value on the bar
                ax.text(bar.get_x() + bar.get_width()/2., 
                        height + (0.08 if height >= 0 else -0.15),
                        f'r={corr_val:.2f}', ha='center', fontsize=10, fontweight='bold')
                
                # Add p-value below or above correlation value based on bar height
                if height >= 0:
                    y_pos = height + 0.15
                else:
                    y_pos = height - 0.08
                
                ax.text(bar.get_x() + bar.get_width()/2., y_pos,
                        p_text, ha='center', fontsize=9, 
                        style='italic', color='darkgray' if p_val < 0.05 else 'darkred')
        
        
        
        plt.tight_layout()
        #plt.show()
        
        if plot_type == 'both':
            return bar_fig, corr_fig
        if plot_type == 'correlation':
            return corr_fig
        if plot_type == 'bar':
            return bar_fig



def plot_mta_vs_ridehail_daily(mta_df, ridehail_df, summary = False):
    """
    Plot 1: Daily time series comparison of MTA vs HVFHV
    """
    from scipy import stats
    
    # Aggregate by date
    ridehail_daily = ridehail_df.groupby('date')['trip_count'].sum().reset_index()
    mta_daily = mta_df.groupby('date')['ridership'].sum().reset_index()

    # Merge
    daily_df = pd.merge(ridehail_daily, mta_daily, on='date')
    daily_df['date'] = pd.to_datetime(daily_df['date'])
    daily_df = daily_df.sort_values('date')
    
    # Calculate overall correlation
    overall_corr, overall_p = stats.pearsonr(daily_df['trip_count'], daily_df['ridership'])

    # FIRST PLOT: Daily time series
    fig1, ax1 = plt.subplots(figsize=(15, 6))

    # Plot MTA on primary axis (left)
    color1 = 'tab:blue'
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('MTA Ridership', color=color1, fontsize=12)
    line1 = ax1.plot(daily_df['date'], daily_df['ridership'], color=color1, 
                     linewidth=1.5, alpha=0.8, label='MTA')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3)

    # Create secondary axis for HVFHV (right)
    ax1_twin = ax1.twinx()
    color2 = 'tab:orange'
    ax1_twin.set_ylabel('HVFHV Trips', color=color2, fontsize=12)
    line2 = ax1_twin.plot(daily_df['date'], daily_df['trip_count'], color=color2, 
                          linewidth=1.5, alpha=0.8, label='HVFHV')
    ax1_twin.tick_params(axis='y', labelcolor=color2)

    # Add title and legend
    ax1.set_title(f'MTA vs HVFHV Daily Ridership\nOverall Correlation: {overall_corr:.3f} (p-value: {overall_p:.4f})', 
                  fontsize=14, fontweight='bold', pad=20)

    # Combine legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')

    plt.tight_layout()
    #plt.show()
    
    if summary:
        # Print statistics for first plot
        print(f"\n📊 Daily Time Series Analysis:")
        print("=" * 50)
        print(f"Overall Pearson correlation: {overall_corr:.4f}")
        print(f"P-value: {overall_p:.4f}")
        
        if overall_p < 0.001:
            print("Significance: *** (p < 0.001)")
        elif overall_p < 0.01:
            print("Significance: ** (p < 0.01)")
        elif overall_p < 0.05:
            print("Significance: * (p < 0.05)")
        else:
            print("Significance: Not significant (p >= 0.05)")
    
    return fig1


def plot_rolling_correlation(mta_df, ridehail_df, window=30, summary = False):
    """
    Plot 2: Rolling correlation between MTA and HVFHV
    
    Parameters:
    -----------
    window: int - Number of days for rolling window (default=30)
    """
    from scipy import stats
    
    # Aggregate by date
    ridehail_daily = ridehail_df.groupby('date')['trip_count'].sum().reset_index()
    mta_daily = mta_df.groupby('date')['ridership'].sum().reset_index()

    # Merge
    daily_df = pd.merge(ridehail_daily, mta_daily, on='date')
    daily_df['date'] = pd.to_datetime(daily_df['date'])
    daily_df = daily_df.sort_values('date')
    
    # Calculate rolling correlation
    daily_df['rolling_corr'] = daily_df['trip_count'].rolling(window=window).corr(daily_df['ridership'])
    
    # Calculate overall correlation
    overall_corr, overall_p = stats.pearsonr(daily_df['trip_count'], daily_df['ridership'])

    # SECOND PLOT: Rolling correlation
    fig2, ax2 = plt.subplots(figsize=(15, 6))

    ax2.plot(daily_df['date'], daily_df['rolling_corr'], color='purple', linewidth=2)
    ax2.axhline(y=overall_corr, color='gray', linestyle='--', alpha=0.7, label=f'Overall: {overall_corr:.3f}')
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    # Add colored fills for positive/negative correlation
    ax2.fill_between(daily_df['date'], 0, daily_df['rolling_corr'], 
                     where=(daily_df['rolling_corr'] > 0), color='green', alpha=0.3, 
                     label='Positive correlation')
    ax2.fill_between(daily_df['date'], 0, daily_df['rolling_corr'], 
                     where=(daily_df['rolling_corr'] < 0), color='red', alpha=0.3,
                     label='Negative correlation')
    
    # Add reference lines for correlation strength
    ax2.axhline(y=0.5, color='gray', linestyle=':', alpha=0.5, label='Strong correlation (0.5)')
    ax2.axhline(y=-0.5, color='gray', linestyle=':', alpha=0.5)
    ax2.axhline(y=0.3, color='lightgray', linestyle='--', alpha=0.5, label='Moderate correlation (0.3)')
    ax2.axhline(y=-0.3, color='lightgray', linestyle='--', alpha=0.5)
    
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel(f'{window}-Day Rolling Correlation', fontsize=12)
    ax2.set_title(f'Rolling Correlation: MTA vs HVFHV ({window}-day window)', 
                  fontsize=14, fontweight='bold')
    ax2.set_ylim([-1, 1])
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper right', ncol=2)

    plt.tight_layout()
    #plt.show()

    if summary:
        # Print statistics for second plot
        print(f"\n📊 Rolling Correlation Analysis ({window}-day window):")
        print("=" * 50)
        print(f"Rolling correlation statistics:")
        print(f"  - Mean: {daily_df['rolling_corr'].mean():.4f}")
        print(f"  - Std: {daily_df['rolling_corr'].std():.4f}")
        print(f"  - Min: {daily_df['rolling_corr'].min():.4f}")
        print(f"  - Max: {daily_df['rolling_corr'].max():.4f}")
        print(f"  - % time positive: {(daily_df['rolling_corr'] > 0).mean() * 100:.1f}%")
        print(f"  - % time strong (>0.5): {(daily_df['rolling_corr'].abs() > 0.5).mean() * 100:.1f}%")
    
    return fig2


# Optional: Combined function that calls both
def plot_mta_vs_ridehail_both(mta_df, ridehail_df, window=30):
    """
    Generate both plots: daily time series and rolling correlation
    """
    #print("PLOT 1: Daily Time Series Comparison")
    fig1 = plot_mta_vs_ridehail_daily(mta_df, ridehail_df)
    
    #print(f"PLOT 2: Rolling Correlation ({window}-day window)")
    fig2 = plot_rolling_correlation(mta_df, ridehail_df, window)
    
    return fig1, fig2

    
def scatterplot_mta_vs_ridehail_daily(mta_df, ridehail_df, summary = False):
    from scipy import stats
    import numpy as np
    
    # Aggregate by date
    ridehail_daily = ridehail_df.groupby('date')['trip_count'].sum().reset_index()
    mta_daily = mta_df.groupby('date')['ridership'].sum().reset_index()

    # Merge datasets
    df = pd.merge(ridehail_daily, mta_daily, on='date')
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    # Define variables
    x = df['trip_count']      # Ride-hailing
    y = df['ridership']      # MTA
    
    # Calculate correlation and p-value
    corr, p_value = stats.pearsonr(x, y)
    
    # Calculate regression line with confidence intervals
    slope, intercept, r_value, p_value_reg, std_err = stats.linregress(x, y)
    
    # Create scatter plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # First subplot: Scatter with regression
    ax1.scatter(x, y, alpha=0.5, edgecolor='black', s=50)
    
    # Regression line
    x_line = np.array([x.min(), x.max()])
    y_line = slope * x_line + intercept
    ax1.plot(x_line, y_line, 'r-', linewidth=2, label=f'Regression (R²={r_value**2:.3f})')
    
    # Add confidence interval (95%)
    n = len(x)
    x_mean = x.mean()
    t_value = stats.t.ppf(0.975, n-2)  # 95% confidence
    
    # Calculate prediction interval
    x_pred = np.linspace(x.min(), x.max(), 100)
    y_pred = slope * x_pred + intercept
    
    # Standard error of prediction
    se_pred = std_err * np.sqrt(1/n + (x_pred - x_mean)**2 / np.sum((x - x_mean)**2))
    ci_upper = y_pred + t_value * se_pred
    ci_lower = y_pred - t_value * se_pred
    
    ax1.fill_between(x_pred, ci_lower, ci_upper, color='red', alpha=0.1, label='95% CI')
    
    # Labels and title
    ax1.set_xlabel('Ride-Hailing Trips (Daily)', fontsize=12)
    ax1.set_ylabel('MTA Ridership (Daily)', fontsize=12)
    ax1.set_title('Ride Hailing vs MTA Scatter Plot', fontsize=14, fontweight='bold')
    
    # Add statistics box
    stats_text = f'Correlation: {corr:.3f}\nP-value: {p_value:.4f}\nR²: {r_value**2:.3f}\nSlope: {slope:.2f}'
    if p_value < 0.001:
        stats_text += '\nSignificance: ***'
    elif p_value < 0.01:
        stats_text += '\nSignificance: **'
    elif p_value < 0.05:
        stats_text += '\nSignificance: *'
    
    ax1.text(0.05, 0.95, stats_text,
             transform=ax1.transAxes,
             fontsize=10,
             verticalalignment='top',
             bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
    
    ax1.legend(loc='lower right')
    ax1.grid(True, alpha=0.3)
    
    # Second subplot: Residuals
    residuals = y - (slope * x + intercept)
    ax2.scatter(x, residuals, alpha=0.5, edgecolor='black', s=50)
    ax2.axhline(y=0, color='red', linestyle='-', linewidth=2)
    ax2.axhline(y=2*residuals.std(), color='orange', linestyle='--', alpha=0.7, label='±2σ')
    ax2.axhline(y=-2*residuals.std(), color='orange', linestyle='--', alpha=0.7)
    
    ax2.set_xlabel('Ride-Hailing Trips (Daily)', fontsize=12)
    ax2.set_ylabel('Residuals', fontsize=12)
    ax2.set_title('Residual Plot', fontsize=14, fontweight='bold')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    
    # Add residual statistics
    residual_text = f'Residuals:\nMean: {residuals.mean():.2f}\nStd: {residuals.std():.2f}\nNormality test p: {stats.shapiro(residuals[:5000])[1]:.4f}'
    ax2.text(0.05, 0.95, residual_text,
             transform=ax2.transAxes,
             fontsize=10,
             verticalalignment='top',
             bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    #plt.show()

    if summary:
        # Print detailed statistics
        print(f"\n📊 Detailed Correlation Analysis:")
        print("=" * 50)
        print(f"Pearson correlation coefficient: {corr:.4f}")
        print(f"P-value: {p_value:.4f}")
        print(f"R-squared: {r_value**2:.4f}")
        print(f"\nRegression equation: MTA = {slope:.2f} × HVFHV + {intercept:.2f}")
        print(f"Standard error: {std_err:.4f}")
        
        # Significance interpretation
        print(f"\nSignificance level:")
        if p_value < 0.001:
            print("  *** p < 0.001 (Highly significant)")
        elif p_value < 0.01:
            print("  ** p < 0.01 (Very significant)")
        elif p_value < 0.05:
            print("  * p < 0.05 (Significant)")
        else:
            print("  Not significant (p >= 0.05)")
        
        print(f"\nResidual analysis:")
        print(f"  Mean: {residuals.mean():.4f} (should be close to 0)")
        print(f"  Standard deviation: {residuals.std():.4f}")
        print(f"  Normality test p-value: {stats.shapiro(residuals[:5000])[1]:.4f}")


    return fig