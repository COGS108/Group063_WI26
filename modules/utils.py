import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, box
import numpy as np
from shapely.ops import transform
import pyproj
from functools import partial
from matplotlib import pyplot as plt

#Finds and returns the stations nearest the taxi zone
def find_stations_near_taxi_zone(taxi_zone_id:(int | str),
                                buffer_miles:int,
                                subway_gdf,
                                taxi_zones_gdf):
    """
    Find subway stations that are within a taxi zone or within a buffer around it
    
    Parameters:
    -----------
    taxi_zone_id : int or str
        The ID of the taxi zone to search around
    buffer_miles : float
        Buffer distance in miles to expand the zone
    subway_gdf : GeoDataFrame
        GeoDataFrame containing subway stations with point geometries
    taxi_zones_gdf : GeoDataFrame
        GeoDataFrame containing taxi zones with polygon geometries
    
    Returns:
    --------
    GeoDataFrame with stations within the zone+buffer, including distance info
    """
    
    # 1. Find the target taxi zone
    taxi_zone_id_str = str(taxi_zone_id)
    target_zone = taxi_zones_gdf[taxi_zones_gdf['locationid'] == taxi_zone_id_str].copy()
    
    if len(target_zone) == 0:
        print(f"❌ Taxi zone ID {taxi_zone_id} not found")
        return None
    
    zone_name = target_zone.iloc[0].get('zone', f'Zone {taxi_zone_id}')
    print(f"📍 Searching around: {zone_name} (ID: {taxi_zone_id})")
    
    # 2. Get the zone geometry
    zone_geom = target_zone.geometry.iloc[0]
    
    # 3. Create a projected version for accurate buffering
    # Project to UTM zone 18N (appropriate for NYC)
    proj = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True).transform
    
    # Project the zone geometry
    zone_geom_proj = transform(proj, zone_geom)
    
    # 4. Create buffer in meters (convert miles to meters)
    buffer_meters = buffer_miles * 1609.34
    buffered_zone_proj = zone_geom_proj.buffer(buffer_meters)
    
    # 5. Project back to lat/lon for searching
    proj_back = pyproj.Transformer.from_crs("EPSG:32618", "EPSG:4326", always_xy=True).transform
    buffered_zone = transform(proj_back, buffered_zone_proj)
    
    # 6. Create a bounding box for faster initial filtering
    minx, miny, maxx, maxy = buffered_zone.bounds
    possible_stations = subway_gdf.cx[minx:maxx, miny:maxy].copy()
    
    print(f"   Initial filter: {len(possible_stations)} stations in bounding box")
    
    # 7. Find stations within the buffered zone
    stations_within = possible_stations[possible_stations.geometry.within(buffered_zone)].copy()
    
    # 8. Categorize and calculate distances
    def categorize_and_distance(point):
        # Check if point is actually inside the original zone
        point_proj = transform(proj, point)
        
        if zone_geom_proj.contains(point_proj):
            category = "INSIDE ZONE"
            distance = 0
        else:
            category = "IN BUFFER"
            # Calculate distance to zone boundary
            distance = point_proj.distance(zone_geom_proj) * 0.000621371  # meters to miles
        
        return pd.Series({'location_type': category, 'distance_to_zone_miles': distance})
    
    # Apply the categorization
    stations_within[['location_type', 'distance_to_zone_miles']] = stations_within.geometry.apply(
        categorize_and_distance
    )
    
    # 9. Sort: first by inside/outside, then by distance
    stations_within = stations_within.sort_values(
        ['location_type', 'distance_to_zone_miles'], 
        ascending=[False, True]  # 'INSIDE ZONE' comes first (False sorts alphabetically? Actually we'll fix this)
    )
    
    # Better sorting: inside zone first, then by distance
    stations_within['sort_order'] = stations_within['location_type'].map({'INSIDE ZONE': 0, 'IN BUFFER': 1})
    stations_within = stations_within.sort_values(['sort_order', 'distance_to_zone_miles'])
    stations_within = stations_within.drop('sort_order', axis=1)
    
    return stations_within

def find_taxi_zone_for_station(station_complex_id, subway_gdf, taxi_zones_gdf):
    """
    Find the taxi zone that contains a given subway station
    
    Parameters:
    -----------
    station_complex_id : str
        The unique identifier for the subway station (e.g., 'GTFS Stop ID')
    subway_gdf : GeoDataFrame
        GeoDataFrame containing subway stations with point geometries
    taxi_zones_gdf : GeoDataFrame
        GeoDataFrame containing taxi zones with polygon geometries
    
    Returns:
    --------
    GeoDataFrame with the taxi zone containing the station, or None if not found
    """
    
    # 1. Find the target station
    target_station = subway_gdf[subway_gdf['Complex ID'] == station_complex_id].copy()
    
    if len(target_station) == 0:
        print(f"❌ Station Complex ID {station_complex_id} not found")
        return None
    
    station_name = target_station.iloc[0].get('Stop Name', f'Station {station_complex_id}')
    print(f"📍 Searching for taxi zone containing: {station_name} (ID: {station_complex_id})")
    
    # 2. Get the station geometry
    station_geom = target_station.geometry.iloc[0]
    
    # 3. Check which taxi zone contains this station
    containing_zone = taxi_zones_gdf[taxi_zones_gdf.geometry.contains(station_geom)].copy()
    
    if len(containing_zone) == 0:
        print(f"⚠️ No taxi zone contains station {station_name}")
        return None
    
    return containing_zone

#Prepares the ridership dataframes
def prepare_ridership_data(
    hvfhv_csv_path = "data/02-processed/total_ridership.csv",
    mta_csv_path = "data/01-interim/MTA_subway/MTA_Subway_Daily_Manhattan.csv"
    ):

    """
    Prepare ridership data for analysis
    
    Parameters:
    -----------
    hvfhv_csv_path : str
        Path to the HVFHV ridership CSV file
    mta_csv_path : str
        Path to the MTA ridership CSV file

    Returns:
    --------
    Tuple of GeoDataFrames (hvfhv_data, mta_data)
    """
    # Load data
    df_hvfhv = pd.read_csv(hvfhv_csv_path)
    df_mta = pd.read_csv(mta_csv_path)
    
    #Convert date columns to datetime
    #df_hvfhv['pickup_datetime'] = pd.to_datetime(df_hvfhv['pickup_datetime'])
    #df_mta['date'] = pd.to_datetime(df_mta['date'])
    
    
    return df_hvfhv, df_mta

def eliminate_ridership_outliers(ridehail_df, mta_df):
    mta_df = pd.read_csv("data/01-interim/MTA_subway/MTA_Subway_Daily_Manhattan_Totals.csv")
    # Convert dates
    ridehail_df['date'] = pd.to_datetime(ridehail_df['date'])
    mta_df['date'] = pd.to_datetime(mta_df['date'])
    
    # Add day of week columns
    ridehail_df['day_of_week'] = ridehail_df['date'].dt.day_name()
    mta_df['day_of_week'] = mta_df['date'].dt.day_name()
    
    # Add weekend column (using dayofweek numbers: 5=Saturday, 6=Sunday)
    ridehail_df['weekend'] = ridehail_df['date'].dt.dayofweek.isin([5, 6])
    mta_df['weekend'] = mta_df['date'].dt.dayofweek.isin([5, 6])
    
    # Split data into weekday and weekend
    weekday_data = mta_df[~mta_df['weekend']]
    weekend_data = mta_df[mta_df['weekend']]
    
    # Calculate statistics for weekdays
    weekday_mean = weekday_data['ridership'].mean()
    weekday_std = weekday_data['ridership'].std()
    weekday_upper_threshold = weekday_mean + (2 * weekday_std)
    weekday_lower_threshold = weekday_mean - (2 * weekday_std)
    weekday_upper_outliers = weekday_data[weekday_data['ridership'] > weekday_upper_threshold]
    weekday_lower_outliers = weekday_data[weekday_data['ridership'] < weekday_lower_threshold]
    
    # Calculate statistics for weekends
    weekend_mean = weekend_data['ridership'].mean()
    weekend_std = weekend_data['ridership'].std()
    weekend_upper_threshold = weekend_mean + (2 * weekend_std)
    weekend_lower_threshold = weekend_mean - (2 * weekend_std)
    weekend_upper_outliers = weekend_data[weekend_data['ridership'] > weekend_upper_threshold]
    weekend_lower_outliers = weekend_data[weekend_data['ridership'] < weekend_lower_threshold]
    
    # Print weekday outliers
    print("=" * 60)
    print("WEEKDAY ANALYSIS")
    print("=" * 60)
    print(f"Mean ridership (Weekdays): {weekday_mean:.2f}")
    print(f"Standard deviation: {weekday_std:.2f}")
    print(f"Upper 3-sigma threshold (+3σ): {weekday_upper_threshold:.2f}")
    print(f"Lower 3-sigma threshold (-3σ): {weekday_lower_threshold:.2f}")
    
    print(f"\n📈 WEEKDAY - HIGH OUTLIERS (above +3σ): {len(weekday_upper_outliers)} days found")
    print("-" * 50)
    if len(weekday_upper_outliers) > 0:
        for idx, row in weekday_upper_outliers.iterrows():
            print(f"Date: {row['date'].strftime('%Y-%m-%d')}, "
                  f"Ridership: {row['ridership']:.0f}, "
                  f"Day: {row['day_of_week']} "
                  f"(+{(row['ridership'] - weekday_mean)/weekday_std:.2f}σ)")
    else:
        print("No weekday high outliers found above +3σ")
    
    print(f"\n📉 WEEKDAY - LOW OUTLIERS (below -3σ): {len(weekday_lower_outliers)} days found")
    print("-" * 50)
    if len(weekday_lower_outliers) > 0:
        for idx, row in weekday_lower_outliers.iterrows():
            print(f"Date: {row['date'].strftime('%Y-%m-%d')}, "
                  f"Ridership: {row['ridership']:.0f}, "
                  f"Day: {row['day_of_week']} "
                  f"({(row['ridership'] - weekday_mean)/weekday_std:.2f}σ)")
    else:
        print("No weekday low outliers found below -3σ")
    
    # Print weekend outliers
    print("\n" + "=" * 60)
    print("WEEKEND ANALYSIS")
    print("=" * 60)
    print(f"Mean ridership (Weekends): {weekend_mean:.2f}")
    print(f"Standard deviation: {weekend_std:.2f}")
    print(f"Upper 3-sigma threshold (+3σ): {weekend_upper_threshold:.2f}")
    print(f"Lower 3-sigma threshold (-3σ): {weekend_lower_threshold:.2f}")
    
    print(f"\n📈 WEEKEND - HIGH OUTLIERS (above +3σ): {len(weekend_upper_outliers)} days found")
    print("-" * 50)
    if len(weekend_upper_outliers) > 0:
        for idx, row in weekend_upper_outliers.iterrows():
            print(f"Date: {row['date'].strftime('%Y-%m-%d')}, "
                  f"Ridership: {row['ridership']:.0f}, "
                  f"Day: {row['day_of_week']} "
                  f"(+{(row['ridership'] - weekend_mean)/weekend_std:.2f}σ)")
    else:
        print("No weekend high outliers found above +3σ")
    
    print(f"\n📉 WEEKEND - LOW OUTLIERS (below -3σ): {len(weekend_lower_outliers)} days found")
    print("-" * 50)
    if len(weekend_lower_outliers) > 0:
        for idx, row in weekend_lower_outliers.iterrows():
            print(f"Date: {row['date'].strftime('%Y-%m-%d')}, "
                  f"Ridership: {row['ridership']:.0f}, "
                  f"Day: {row['day_of_week']} "
                  f"({(row['ridership'] - weekend_mean)/weekend_std:.2f}σ)")
    else:
        print("No weekend low outliers found below -3σ")
    
    # Create histograms
    import matplotlib.pyplot as plt
    
    # Set up the figure
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # Histogram for all days
    axes[0].hist(mta_df['ridership'], bins=30, edgecolor='black', alpha=0.7)
    axes[0].axvline(mta_df['ridership'].mean(), color='red', linestyle='-', linewidth=2, label='Overall Mean')
    axes[0].set_title(f'MTA Ridership - All Days')
    axes[0].set_xlabel('Ridership')
    axes[0].set_ylabel('Frequency')
    axes[0].legend()
    
    # Histogram for weekdays with thresholds
    axes[1].hist(weekday_data['ridership'], bins=30, edgecolor='black', alpha=0.7, color='blue')
    axes[1].axvline(weekday_mean, color='red', linestyle='-', linewidth=2, label='Weekday Mean')
    axes[1].axvline(weekday_upper_threshold, color='orange', linestyle='--', linewidth=2, 
                    label=f'+3σ ({weekday_upper_threshold:.0f})')
    axes[1].axvline(weekday_lower_threshold, color='purple', linestyle='--', linewidth=2, 
                    label=f'-3σ ({weekday_lower_threshold:.0f})')
    axes[1].set_title(f'MTA Ridership - Weekdays\n({len(weekday_upper_outliers)} high, {len(weekday_lower_outliers)} low outliers)')
    axes[1].set_xlabel('Ridership')
    axes[1].set_ylabel('Frequency')
    axes[1].legend()
    
    # Histogram for weekends with thresholds
    axes[2].hist(weekend_data['ridership'], bins=30, edgecolor='black', alpha=0.7, color='green')
    axes[2].axvline(weekend_mean, color='red', linestyle='-', linewidth=2, label='Weekend Mean')
    axes[2].axvline(weekend_upper_threshold, color='orange', linestyle='--', linewidth=2, 
                    label=f'+3σ ({weekend_upper_threshold:.0f})')
    axes[2].axvline(weekend_lower_threshold, color='purple', linestyle='--', linewidth=2, 
                    label=f'-3σ ({weekend_lower_threshold:.0f})')
    axes[2].set_title(f'MTA Ridership - Weekends\n({len(weekend_upper_outliers)} high, {len(weekend_lower_outliers)} low outliers)')
    axes[2].set_xlabel('Ridership')
    axes[2].set_ylabel('Frequency')
    axes[2].legend()
    
    plt.tight_layout()
    plt.show()
    
    return ridehail_df, mta_df

#Prepare the geodataframes for the subway stations and taxi zones, and optionally the subway lines, ensuring they are in the same coordinate reference system (CRS) for spatial analysis and mapping.
def prepare_gdf_data(subway_station_csv_path = 'data/02-processed/map_files/MTA_Subway_Stations_cleaned.csv',
                    taxi_zones_geojson_path = 'data/02-processed/map_files/NYC_Taxi_Zones.geojson',
                    subway_lines_geojson_path ='data/02-processed/map_files/MTA_Subway_Service_Lines.geojson'):
    
        """
    Prepare ridership data for analysis
    
    Parameters:
    -----------
    subway_station_csv_path : str
        Path to the subway station CSV file
    taxi_zones_geojson_path : str
        Path to the taxi zones GeoJSON file
    subway_lines_geojson_path : str
        Path to the subway lines GeoJSON file

    Returns:
    --------
    Tuple of GeoDataFrames (subway_stations_gdf, taxi_zones_gdf, subway_lines_gdf)
    """
    # Load subway data (stations)
        subway_df = pd.read_csv(subway_station_csv_path)
        subway_gdf = gpd.GeoDataFrame(
            subway_df,
            geometry=gpd.points_from_xy(subway_df['GTFS Longitude'], 
                                        subway_df['GTFS Latitude']),
            crs="EPSG:4326"
        )
        
        # Load taxi zones
        taxi_zones_gdf = gpd.read_file(taxi_zones_geojson_path)
        
        # Make sure they're in the same CRS
        if taxi_zones_gdf.crs != subway_gdf.crs:
            taxi_zones_gdf = taxi_zones_gdf.to_crs(subway_gdf.crs)
        
        # Load subway lines if path is provided
        if subway_lines_geojson_path is not None:
            subway_lines_gdf = gpd.read_file(subway_lines_geojson_path)
            
            # Ensure subway lines are in the same CRS
            if subway_lines_gdf.crs != subway_gdf.crs:
                subway_lines_gdf = subway_lines_gdf.to_crs(subway_gdf.crs)
            
            return subway_gdf, taxi_zones_gdf, subway_lines_gdf
        
        return subway_gdf, taxi_zones_gdf