import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime


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

