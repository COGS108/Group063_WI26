import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
from shapely.geometry import Point, box
from shapely.ops import unary_union
from datetime import datetime
from modules import graph, utils, maps

subway_stations_gdf, taxi_zones_gdf, subway_lines_gdf = utils.prepare_gdf_data()
ridehail_df, mta_df = utils.prepare_ridership_data('data/02-processed/ridehailing_daily_cleaned.csv','data/02-processed/MTA_Ridership_cleaned.csv')

def compare_station_with_nearby_zones(complex_id, radius_miles, 
                                               subway_stations_gdf, taxi_zones_gdf, 
                                               mta_df, hvfhv_df):
    """
    Compare ridership of an MTA station with HVFHV trips in nearby Manhattan taxi zones.
    """
    
    # 1. Filter to Manhattan only
    manhattan_zones = taxi_zones_gdf[taxi_zones_gdf['borough'] == 'Manhattan'].copy()
    manhattan_stations = subway_stations_gdf[subway_stations_gdf['Borough'] == 'M'].copy()
    
    # 2. Find the station
    station = manhattan_stations[manhattan_stations['Complex ID'] == complex_id]
    
    if len(station) == 0:
        print(f"Complex ID {complex_id} not found in Manhattan")
        return None
    
    station = station.iloc[0]
    print(f"\n{'='*60}")
    print(f"Station: {station['Stop Name']} (Complex ID: {complex_id})")
    print(f"{'='*60}")
    
    # 3. Get station ridership
    mta_df['date'] = pd.to_datetime(mta_df['date'])
    mta_df['station_complex_id'] = mta_df['station_complex_id'].astype(str)
    
    station_ridership = mta_df[mta_df['station_complex_id'] == str(complex_id)]
    
    if len(station_ridership) == 0:
        print(f"No ridership data found for Complex ID {complex_id}")
        return None
    
    avg_station_ridership = station_ridership['ridership'].mean()
    print(f"\nAverage daily MTA ridership: {avg_station_ridership:,.0f}")
    
    # 4. Find nearby Manhattan taxi zones
    station_gdf = gpd.GeoDataFrame([station], geometry='geometry', crs='EPSG:4326')
    station_gdf = station_gdf.to_crs('EPSG:3857')
    manhattan_zones_proj = manhattan_zones.to_crs('EPSG:3857')
    
    radius_meters = radius_miles * 1609.34
    station_buffer = station_gdf.geometry.iloc[0].buffer(radius_meters)
    
    nearby_zones = manhattan_zones_proj[manhattan_zones_proj.intersects(station_buffer)]
    
    print(f"\nRadius: {radius_miles} miles ({radius_meters:.0f} meters)")
    print(f"Nearby Manhattan taxi zones: {len(nearby_zones)}")
    
    if len(nearby_zones) > 0:
        print("\nNearby zones:")
        for idx, zone in nearby_zones.iterrows():
            print(f"  - {zone['zone']}")
    
    # 5. Get HVFHV ridership in nearby zones
    hvfhv_df['date'] = pd.to_datetime(hvfhv_df['date'])
    hvfhv_df['PULocationID'] = hvfhv_df['PULocationID'].astype(str)
    
    nearby_zone_ids = nearby_zones['locationid'].astype(str).tolist()
    nearby_hvfhv = hvfhv_df[hvfhv_df['PULocationID'].isin(nearby_zone_ids)]
    
    if len(nearby_hvfhv) == 0:
        print("\nNo HVFHV data found for nearby zones")
        return None
    
    daily_nearby_hvfhv = nearby_hvfhv.groupby('date')['trip_count'].sum()
    avg_nearby_hvfhv = daily_nearby_hvfhv.mean()
    
    print(f"\nAverage daily HVFHV trips in nearby zones: {avg_nearby_hvfhv:,.0f}")
    
    # 6. Calculate by day of week
    mta_df['day_of_week'] = mta_df['date'].dt.day_name()
    hvfhv_df['day_of_week'] = hvfhv_df['date'].dt.day_name()
    
    station_by_dow = station_ridership.groupby('day_of_week')['ridership'].mean()
    nearby_hvfhv_by_dow = nearby_hvfhv.groupby('day_of_week')['trip_count'].mean()
    
    # 7. Create Manhattan-only map
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Map view - Manhattan only
    ax1 = axes[0, 0]
    
    # Plot all Manhattan zones lightly
    manhattan_zones_proj.plot(ax=ax1, color='lightgray', edgecolor='white', linewidth=0.3, alpha=0.5)
    
    # Highlight nearby zones
    if len(nearby_zones) > 0:
        nearby_zones.plot(ax=ax1, color='yellow', edgecolor='black', linewidth=0.5, alpha=0.5)
    
    # Plot station buffer
    buffer_gdf = gpd.GeoDataFrame(geometry=[station_buffer], crs='EPSG:3857')
    buffer_gdf.plot(ax=ax1, color='none', edgecolor='blue', linewidth=2, alpha=0.7)
    
    # Plot station
    station_gdf.plot(ax=ax1, color='red', markersize=100, marker='*', label='Station')
    
    ax1.set_title(f'Manhattan: {station["Stop Name"]}\n{radius_miles} mile radius', fontweight='bold')
    ax1.set_axis_off()
    
    # Rest of the plots (same as before)
    # Bar chart comparison
    ax2 = axes[0, 1]
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    mta_vals = [station_by_dow.get(day, 0) for day in days]
    hvfhv_vals = [nearby_hvfhv_by_dow.get(day, 0) for day in days]
    
    x = np.arange(len(days))
    width = 0.35
    
    ax2.bar(x - width/2, mta_vals, width, label='MTA', color='blue', alpha=0.7)
    ax2.bar(x + width/2, hvfhv_vals, width, label='HVFHV', color='orange', alpha=0.7)
    ax2.set_xlabel('Day of Week')
    ax2.set_ylabel('Average Ridership')
    ax2.set_title('Daily Ridership Comparison', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(days, rotation=45)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Scatter plot of daily relationship
    ax3 = axes[1, 0]
    
    station_daily = station_ridership.groupby('date')['ridership'].sum().reset_index()
    nearby_daily = nearby_hvfhv.groupby('date')['trip_count'].sum().reset_index()
    
    merged = pd.merge(station_daily, nearby_daily, on='date', how='inner')
    
    if len(merged) > 0:
        ax3.scatter(merged['ridership'], merged['trip_count'], alpha=0.5)
        ax3.set_xlabel('MTA Ridership')
        ax3.set_ylabel('Nearby HVFHV Trips')
        ax3.set_title(f'Daily Relationship\nCorrelation: {merged["ridership"].corr(merged["trip_count"]):.3f}', 
                     fontweight='bold')
    else:
        ax3.text(0.5, 0.5, 'No overlapping dates', ha='center', va='center')
    ax3.grid(True, alpha=0.3)
    
    # Ratio by day
    ax4 = axes[1, 1]
    
    ratio_vals = []
    for day in days:
        m = station_by_dow.get(day, 0)
        h = nearby_hvfhv_by_dow.get(day, 0)
        if m > 0:
            ratio_vals.append(h / m * 100)
        else:
            ratio_vals.append(0)
    
    ax4.bar(days, ratio_vals, color='purple', alpha=0.7)
    ax4.set_xlabel('Day of Week')
    ax4.set_ylabel('HVFHV as % of MTA Ridership')
    ax4.set_title('HVFHV Relative to MTA by Day', fontweight='bold')
    ax4.tick_params(axis='x', rotation=45)
    ax4.grid(True, alpha=0.3)
    
    plt.suptitle(f'Manhattan: Station vs Nearby Taxi Zones\n{station["Stop Name"]} ({radius_miles} mile radius)', 
                fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.show()
    
    # 8. Return summary statistics
    results = {
        'station_name': station['Stop Name'],
        'complex_id': complex_id,
        'radius_miles': radius_miles,
        'avg_station_ridership': avg_station_ridership,
        'avg_nearby_hvfhv': avg_nearby_hvfhv,
        'hvfhv_to_mta_ratio': avg_nearby_hvfhv / avg_station_ridership if avg_station_ridership > 0 else 0,
        'nearby_zones': nearby_zone_ids,
        'nearby_zone_names': nearby_zones['zone'].tolist() if len(nearby_zones) > 0 else [],
        'correlation': merged['ridership'].corr(merged['trip_count']) if len(merged) > 0 else None
    }
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Station: {results['station_name']}")
    print(f"Avg daily MTA: {results['avg_station_ridership']:,.0f}")
    print(f"Avg daily HVFHV (within {radius_miles} miles): {results['avg_nearby_hvfhv']:,.0f}")
    print(f"HVFHV/MTA ratio: {results['hvfhv_to_mta_ratio']:.3f}")
    if results['correlation'] is not None:
        print(f"Daily correlation: {results['correlation']:.3f}")
    
    return results

# Example usage:
# compare_station_with_nearby_zones_manhattan(611, 0.5, subway_stations_gdf, taxi_zones_gdf, mta_df, ridehail_df)

# Example usage:
compare_station_with_nearby_zones(164, 0.5, subway_stations_gdf, taxi_zones_gdf, mta_df, ridehail_df)  # Times Square
compare_station_with_nearby_zones(150, 0.5, subway_stations_gdf, taxi_zones_gdf, mta_df, ridehail_df)  # Times Square