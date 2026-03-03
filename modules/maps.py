import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, box
import numpy as np
from shapely.ops import transform
import pyproj
from functools import partial
from matplotlib import pyplot as plt


#Allows visualization of stations within subway stations
def plot_stations_near_taxi_zone(stations_gdf, taxi_zones_gdf, taxi_zone_id, buffer_miles):
    """
    Optional: Plot the results to visualize the buffer
    """
    import matplotlib.pyplot as plt
    taxi_zone_id_str = str(taxi_zone_id)
    target = taxi_zones_gdf[taxi_zones_gdf['locationid'] == taxi_zone_id_str]
    if len(target) == 0:
        return
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    # Plot all taxi zones lightly
    taxi_zones_gdf.plot(ax=ax, color='lightgray', edgecolor='gray', alpha=0.3)
    
    # Plot target zone
    target.plot(ax=ax, color='yellow', edgecolor='black', alpha=0.5, label='Target Zone')
    
    # Create and plot buffer
    proj = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True).transform
    proj_back = pyproj.Transformer.from_crs("EPSG:32618", "EPSG:4326", always_xy=True).transform
    
    zone_proj = transform(proj, target.geometry.iloc[0])
    buffer_proj = zone_proj.buffer(buffer_miles * 1609.34)
    buffer = transform(proj_back, buffer_proj)
    
    gpd.GeoSeries([buffer]).plot(ax=ax, color='blue', alpha=0.1, label=f'{buffer_miles} mile buffer')
    
    # Plot stations
    stations_gdf.plot(ax=ax, color='red', markersize=10, label='Subway Stations')
    
    # Highlight stations found
    if len(stations_gdf) > 0:
        stations_gdf.plot(ax=ax, color='green', markersize=20, 
                         edgecolor='black', label='Stations Found')
    
    plt.legend()
    plt.title(f'Taxi Zone {taxi_zone_id} with {buffer_miles} mile buffer')
    plt.show()

#Plots the transit map entirely
#TODO: this function can be expanded to include more features
def plot_transit_map(subway_stations_gdf, taxi_zones_gdf, subway_lines_gdf=None):

    fig, ax = plt.subplots(figsize=(15, 12))

    # 1️⃣ Taxi zones (bottom layer)
    taxi_zones_gdf.plot(
        ax=ax,
        color='lightgray',
        edgecolor='black',
        linewidth=0.5,
        alpha=0.6
    )

    # 2️⃣ Subway lines (middle layer)
    subway_lines_gdf.plot(
        ax=ax,
        color='red',
        linewidth=1,
        alpha=0.8
    )

    # 3️⃣ Subway stations (top layer)
    subway_stations_gdf.plot(
        ax=ax,
        color='blue',
        markersize=10,
        alpha=0.9
    )

    # Clean formatting
    ax.set_title('NYC Taxi Zones, Subway Lines, and Stations',
                fontsize=16,
                fontweight='bold')

    ax.set_axis_off()
    plt.tight_layout()

    # Save BEFORE show (best practice)
    plt.savefig('nyc_taxi_zones_subway_stations.png',
                dpi=300,
                bbox_inches='tight')

    plt.show()

