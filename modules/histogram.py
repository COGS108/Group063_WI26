import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime
df_hvfhv = pd.read_csv("data/01-interim/2023_High_Volume_FHV_Trip_Data_cleaned.csv")
df_mta = pd.read_csv("data/01-interim/MTA_Subway_Daily_Manhattan.csv")


def create_popularity_histogram(df_hvfhv, df_mta, month):
    """
    Create histograms comparing the most popular FHV zones and MTA stations for a given month.
    
    Parameters:
    df_hvfhv (DataFrame): High Volume FHV data
    df_mta (DataFrame): MTA subway data
    month (int): Month to analyze (1-12)
    """
    
    # Process FHV data
    df_hvfhv['by_day_pickup_datetime'] = pd.to_datetime(df_hvfhv['by_day_pickup_datetime'])
    df_hvfhv['month'] = df_hvfhv['by_day_pickup_datetime'].dt.month
    df_hvfhv['trip_count'] = df_hvfhv['trip_count'].astype(str).str.replace(',', '').astype(int)
    
    # Filter for specific month
    fhv_month = df_hvfhv[df_hvfhv['month'] == month]
    
    # Process MTA data
    df_mta['date'] = pd.to_datetime(df_mta['date'])
    df_mta['month'] = df_mta['date'].dt.month
    
    # Filter for specific month
    mta_month = df_mta[df_mta['month'] == month]
    
    # Get top 10 locations for each
    fhv_top = fhv_month.groupby('PULocationID')['trip_count'].sum().sort_values(ascending=False).head(10)
    mta_top = mta_month.groupby('station_complex_id')['ridership'].sum().sort_values(ascending=False).head(10)
    
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # FHV histogram
    ax1.bar(range(len(fhv_top)), fhv_top.values, color='skyblue', edgecolor='navy')
    ax1.set_xlabel('Pickup Location ID')
    ax1.set_ylabel('Total Trip Count')
    ax1.set_title(f'Top 10 FHV Pickup Zones - Month {month}')
    ax1.set_xticks(range(len(fhv_top)))
    ax1.set_xticklabels(fhv_top.index, rotation=45)
    
    # Add value labels
    for i, (idx, val) in enumerate(fhv_top.items()):
        ax1.text(i, val + max(fhv_top.values)*0.01, f'{val:,.0f}', 
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
    print(f"Total FHV trips: {fhv_month['trip_count'].sum():,.0f}")
    print(f"Total MTA ridership: {mta_month['ridership'].sum():,.0f}")
    print(f"Busiest FHV zone: Zone {fhv_top.index[0]} ({fhv_top.values[0]:,.0f} trips)")
    print(f"Busiest MTA station: Station {mta_top.index[0]} ({mta_top.values[0]:,.0f} riders)")

def compare_daily_patterns(df_hvfhv, df_mta, zone_id, station_id, 
                          start_date=None, end_date=None,
                          figsize=(15, 8), save_path=None):
    """
    Create daily time series comparison for a specific taxi zone and MTA station.
    
    Parameters:
    -----------
    df_hvfhv (DataFrame): High Volume FHV data with columns:
                         by_day_pickup_datetime, PULocationID, trip_count
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
    hvfhv = df_hvfhv.copy()
    mta = df_mta.copy()
    
    # Process FHV data
    hvfhv['by_day_pickup_datetime'] = pd.to_datetime(hvfhv['by_day_pickup_datetime'])
    hvfhv['date'] = hvfhv['by_day_pickup_datetime'].dt.date
    hvfhv['trip_count'] = hvfhv['trip_count'].astype(str).str.replace(',', '').astype(int)
    
    # Filter for specific zone
    zone_data = hvfhv[hvfhv['PULocationID'].astype(str) == str(zone_id)].copy()
    
    # Process MTA data
    mta['date'] = pd.to_datetime(mta['date'])
    mta['date_only'] = mta['date'].dt.date
    
    # Filter for specific station
    station_data = mta[mta['station_complex_id'].astype(str) == str(station_id)].copy()
    
    # Apply date filters if provided
    if start_date:
        start_date = pd.to_datetime(start_date).date()
        zone_data = zone_data[pd.to_datetime(zone_data['date']) >= pd.to_datetime(start_date)]
        station_data = station_data[pd.to_datetime(station_data['date_only']) >= pd.to_datetime(start_date)]
    
    if end_date:
        end_date = pd.to_datetime(end_date).date()
        zone_data = zone_data[pd.to_datetime(zone_data['date']) <= pd.to_datetime(end_date)]
        station_data = station_data[pd.to_datetime(station_data['date_only']) <= pd.to_datetime(end_date)]
    
    # Aggregate by date (in case of multiple entries per day)
    zone_daily = zone_data.groupby('date')['trip_count'].sum().reset_index()
    zone_daily['date'] = pd.to_datetime(zone_daily['date'])
    zone_daily = zone_daily.sort_values('date')
    
    station_daily = station_data.groupby('date_only')['ridership'].sum().reset_index()
    station_daily.rename(columns={'date_only': 'date'}, inplace=True)
    station_daily['date'] = pd.to_datetime(station_daily['date'])
    station_daily = station_daily.sort_values('date')
    
    # Check if we have data
    if len(zone_daily) == 0:
        print(f"Warning: No FHV data found for zone {zone_id}")
    if len(station_daily) == 0:
        print(f"Warning: No MTA data found for station {station_id}")
    
    # Create the plot
    fig, axes = plt.subplots(3, 1, figsize=figsize, height_ratios=[2, 2, 1])
    fig.suptitle(f'Daily Comparison: Taxi Zone {zone_id} vs MTA Station {station_id}', 
                 fontsize=16, fontweight='bold', y=0.95)
    
    # Colors
    color_fhv = '#1f77b4'  # Blue
    color_mta = '#ff7f0e'  # Orange
    
    # 1️⃣ Top plot: FHV trips
    ax1 = axes[0]
    if len(zone_daily) > 0:
        ax1.plot(zone_daily['date'], zone_daily['trip_count'], 
                color=color_fhv, linewidth=2, marker='o', markersize=4,
                label=f'Zone {zone_id} Trips')
        
        # Add moving average (7-day)
        zone_daily['ma_7'] = zone_daily['trip_count'].rolling(window=7, center=True).mean()
        ax1.plot(zone_daily['date'], zone_daily['ma_7'], 
                color='darkblue', linewidth=2, linestyle='--',
                label='7-day Moving Average')
        
        # Fill between to show variation
        ax1.fill_between(zone_daily['date'], 0, zone_daily['trip_count'], 
                        alpha=0.3, color=color_fhv)
    
    ax1.set_ylabel('Number of Trips', fontsize=12)
    ax1.set_title(f'Daily FHV Trips - Zone {zone_id}', fontsize=12, fontweight='bold')
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
                label=f'Station {station_id} Ridership')
        
        # Add moving average (7-day)
        station_daily['ma_7'] = station_daily['ridership'].rolling(window=7, center=True).mean()
        ax2.plot(station_daily['date'], station_daily['ma_7'], 
                color='darkorange', linewidth=2, linestyle='--',
                label='7-day Moving Average')
        
        # Fill between
        ax2.fill_between(station_daily['date'], 0, station_daily['ridership'], 
                        alpha=0.3, color=color_mta)
    
    ax2.set_ylabel('Number of Riders', fontsize=12)
    ax2.set_title(f'Daily MTA Ridership - Station {station_id}', fontsize=12, fontweight='bold')
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
            merged['fhv_norm'] = merged['trip_count'] / merged['trip_count'].max() * 100
            merged['mta_norm'] = merged['ridership'] / merged['ridership'].max() * 100
            
            ax3.plot(merged['date'], merged['fhv_norm'], 
                    color=color_fhv, linewidth=2, label=f'Zone {zone_id} (normalized)')
            ax3.plot(merged['date'], merged['mta_norm'], 
                    color=color_mta, linewidth=2, label=f'Station {station_id} (normalized)')
            
            # Find correlation
            correlation = merged['fhv_norm'].corr(merged['mta_norm'])
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
        print(f"\n🚕 FHV Zone {zone_id}:")
        print(f"  - Total trips: {zone_daily['trip_count'].sum():,.0f}")
        print(f"  - Daily average: {zone_daily['trip_count'].mean():,.1f}")
        print(f"  - Peak day: {zone_daily.loc[zone_daily['trip_count'].idxmax(), 'date'].strftime('%Y-%m-%d')} "
              f"({zone_daily['trip_count'].max():,.0f} trips)")
        print(f"  - Lowest day: {zone_daily.loc[zone_daily['trip_count'].idxmin(), 'date'].strftime('%Y-%m-%d')} "
              f"({zone_daily['trip_count'].min():,.0f} trips)")
        print(f"  - Standard deviation: {zone_daily['trip_count'].std():,.1f}")
    
    if len(station_daily) > 0:
        print(f"\n🚇 MTA Station {station_id}:")
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
        
        print(f"\n  Day        | Zone {zone_id} (avg) | Station {station_id} (avg)")
        print("-" * 50)
        for i, day in enumerate(days):
            print(f"  {day:<10} | {zone_dow[i]:>12,.0f} | {station_dow[i]:>12,.0f}")
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\n💾 Figure saved to: {save_path}")
    
    plt.show()
    
    return fig, (ax1, ax2, ax3)


# Additional function to compare multiple zones/stations
def compare_multiple_daily(df_hvfhv, df_mta, zone_ids, station_ids,
                          start_date=None, end_date=None,
                          figsize=(15, 10), save_path=None):
    """
    Compare multiple zones and stations on the same plot.
    
    Parameters:
    -----------
    df_hvfhv, df_mta: DataFrames
    zone_ids: list - List of zone IDs to compare
    station_ids: list - List of station IDs to compare
    """
    
    # Process data similarly
    hvfhv = df_hvfhv.copy()
    mta = df_mta.copy()
    
    hvfhv['by_day_pickup_datetime'] = pd.to_datetime(hvfhv['by_day_pickup_datetime'])
    hvfhv['date'] = hvfhv['by_day_pickup_datetime'].dt.date
    hvfhv['trip_count'] = hvfhv['trip_count'].astype(str).str.replace(',', '').astype(int)
    
    mta['date'] = pd.to_datetime(mta['date'])
    mta['date_only'] = mta['date'].dt.date
    
    fig, axes = plt.subplots(2, 1, figsize=figsize)
    
    # Color maps
    colors_fhv = plt.cm.Blues(np.linspace(0.4, 0.9, len(zone_ids)))
    colors_mta = plt.cm.Oranges(np.linspace(0.4, 0.9, len(station_ids)))
    
    # Plot FHV zones
    ax1 = axes[0]
    for i, zone_id in enumerate(zone_ids):
        zone_data = hvfhv[hvfhv['PULocationID'].astype(str) == str(zone_id)]
        zone_daily = zone_data.groupby('date')['trip_count'].sum().reset_index()
        zone_daily['date'] = pd.to_datetime(zone_daily['date'])
        zone_daily = zone_daily.sort_values('date')
        
        if len(zone_daily) > 0:
            ax1.plot(zone_daily['date'], zone_daily['trip_count'], 
                    color=colors_fhv[i], linewidth=2, 
                    label=f'Zone {zone_id}')
    
    ax1.set_ylabel('Number of Trips')
    ax1.set_title('FHV Zones Comparison')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # Plot MTA stations
    ax2 = axes[1]
    for i, station_id in enumerate(station_ids):
        station_data = mta[mta['station_complex_id'].astype(str) == str(station_id)]
        station_daily = station_data.groupby('date_only')['ridership'].sum().reset_index()
        station_daily.rename(columns={'date_only': 'date'}, inplace=True)
        station_daily['date'] = pd.to_datetime(station_daily['date'])
        station_daily = station_daily.sort_values('date')
        
        if len(station_daily) > 0:
            ax2.plot(station_daily['date'], station_daily['ridership'], 
                    color=colors_mta[i], linewidth=2, 
                    label=f'Station {station_id}')
    
    ax2.set_ylabel('Number of Riders')
    ax2.set_xlabel('Date')
    ax2.set_title('MTA Stations Comparison')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    plt.show()
    
    return fig, (ax1, ax2)


# Example usage:
if __name__ == "__main__":
    # Assuming you have your data loaded
    # df_hvfhv = pd.read_csv('your_hvfhv_data.csv')
    # df_mta = pd.read_csv('your_mta_data.csv')
    
    # Compare one zone and one station
    fig, axes = compare_daily_patterns(
         df_hvfhv, df_mta,
         zone_id=132,
         station_id=611,
         start_date='2023-01-01',
         end_date='2023-01-31',
         #save_path='daily_comparison_zone2_station8.png'
     )
    
    # Compare multiple
    # fig, axes = compare_multiple_daily(
    #     df_hvfhv, df_mta,
    #     zone_ids=[2, 3, 4],
    #     station_ids=[8, 9, 10],
    #     start_date='2023-01-01',
    #     end_date='2023-01-31'
    # )
    pass


    create_popularity_histogram(df_hvfhv, df_mta, month=1)
