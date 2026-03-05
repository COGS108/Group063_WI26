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

def plot_transit_map2(subway_stations_gdf, taxi_zones_gdf, subway_lines_gdf=None,
                    highlight_zones=None, highlight_stations=None,
                    buffer_miles=0.25, figsize=(15, 12), save_path=None):
    """
    Plot NYC transit map with option to highlight specific taxi zones and stations.
    
    Parameters:
    -----------
    subway_stations_gdf : GeoDataFrame
        Subway stations with point geometries and Complex ID
    taxi_zones_gdf : GeoDataFrame
        NYC taxi zones with polygon geometries and locationid
    subway_lines_gdf : GeoDataFrame, optional
        Subway lines to display
    highlight_zones : list or int/str, optional
        Taxi zone ID(s) to highlight in red
    highlight_stations : list or int/str, optional
        Complex ID(s) to highlight in green
    buffer_miles : float
        Buffer distance to show around highlighted areas
    figsize : tuple
        Figure size
    save_path : str, optional
        Path to save the figure
    """
    
    import matplotlib.patches as mpatches
    from shapely.ops import transform
    import pyproj
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Convert single IDs to lists
    if highlight_zones and not isinstance(highlight_zones, (list, tuple)):
        highlight_zones = [highlight_zones]
    if highlight_stations and not isinstance(highlight_stations, (list, tuple)):
        highlight_stations = [highlight_stations]
    
    # Convert to strings for matching
    if highlight_zones:
        highlight_zones = [str(z) for z in highlight_zones]
    if highlight_stations:
        highlight_stations = [str(s) for s in highlight_stations]
    
    print(f"🔍 Looking for stations with Complex ID: {highlight_stations}")
    
    # Set up projection for buffering
    proj = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True).transform
    proj_back = pyproj.Transformer.from_crs("EPSG:32618", "EPSG:4326", always_xy=True).transform
    
    # Determine map bounds based on highlights
    if highlight_zones or highlight_stations:
        bounds_list = []
        
        if highlight_zones:
            highlighted_zones = taxi_zones_gdf[taxi_zones_gdf['locationid'].astype(str).isin(highlight_zones)]
            print(f"Found {len(highlighted_zones)} matching zones")
            if len(highlighted_zones) > 0:
                # Create buffer around highlighted zones
                combined_geom = highlighted_zones.geometry.unary_union
                combined_proj = transform(proj, combined_geom)
                buffer_proj = combined_proj.buffer(buffer_miles * 1609.34)
                buffered = transform(proj_back, buffer_proj)
                bounds_list.append(buffered.bounds)
        
        if highlight_stations:
            highlighted_stations = subway_stations_gdf[
                subway_stations_gdf['Complex ID'].astype(str).isin(highlight_stations)
            ]
            print(f"Found {len(highlighted_stations)} matching stations")
            if len(highlighted_stations) > 0:
                # Create buffer around highlighted stations
                points = highlighted_stations.geometry.unary_union
                points_proj = transform(proj, points)
                buffer_proj = points_proj.buffer(buffer_miles * 1609.34)
                buffered = transform(proj_back, buffer_proj)
                bounds_list.append(buffered.bounds)
        
        # Set map bounds to encompass all highlights with padding
        if bounds_list:
            minx = min(b[0] for b in bounds_list)
            miny = min(b[1] for b in bounds_list)
            maxx = max(b[2] for b in bounds_list)
            maxy = max(b[3] for b in bounds_list)
            
            # Add padding
            x_pad = (maxx - minx) * 0.1
            y_pad = (maxy - miny) * 0.1
            ax.set_xlim(minx - x_pad, maxx + x_pad)
            ax.set_ylim(miny - y_pad, maxy + y_pad)
    
    # 1️⃣ Plot all taxi zones (background)
    taxi_zones_gdf.plot(
        ax=ax,
        color='lightgray',
        edgecolor='black',
        linewidth=0.5,
        alpha=0.3,
        label='Other Taxi Zones'
    )
    
    # 2️⃣ Plot subway lines if provided
    if subway_lines_gdf is not None:
        subway_lines_gdf.plot(
            ax=ax,
            color='gray',
            linewidth=0.8,
            alpha=0.5,
            label='Subway Lines'
        )
    
    # 3️⃣ Plot all subway stations (background)
    subway_stations_gdf.plot(
        ax=ax,
        color='lightblue',
        markersize=5,
        alpha=0.3,
        label='Other Stations'
    )
    
    # 4️⃣ Highlight specific taxi zones
    if highlight_zones:
        highlighted_zones = taxi_zones_gdf[taxi_zones_gdf['locationid'].astype(str).isin(highlight_zones)]
        
        if len(highlighted_zones) > 0:
            # Plot highlighted zones
            highlighted_zones.plot(
                ax=ax,
                color='red',
                edgecolor='darkred',
                linewidth=2,
                alpha=0.7,
                label=f'Highlighted Zones: {", ".join(highlight_zones)}'
            )
            
            # Add zone ID labels
            for idx, row in highlighted_zones.iterrows():
                centroid = row.geometry.centroid
                ax.annotate(
                    row['locationid'],
                    xy=(centroid.x, centroid.y),
                    xytext=(3, 3),
                    textcoords="offset points",
                    fontsize=10,
                    weight='bold',
                    color='darkred',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.7, edgecolor='none')
                )
    
    # 5️⃣ Highlight specific stations using Complex ID
    if highlight_stations:
        highlighted_stations = subway_stations_gdf[
            subway_stations_gdf['Complex ID'].astype(str).isin(highlight_stations)
        ]
        
        if len(highlighted_stations) > 0:
            # Plot highlighted stations
            highlighted_stations.plot(
                ax=ax,
                color='green',
                markersize=50,
                edgecolor='darkgreen',
                linewidth=1,
                alpha=0.9,
                label=f'Highlighted Stations: {", ".join(highlight_stations)}'
            )
            
            # Add station name labels
            for idx, row in highlighted_stations.iterrows():
                ax.annotate(
                    row['Stop Name'],
                    xy=(row.geometry.x, row.geometry.y),
                    xytext=(5, 5),
                    textcoords="offset points",
                    fontsize=9,
                    weight='bold',
                    color='darkgreen',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8, edgecolor='none')
                )
    
    # 6️⃣ Add buffer circles around highlighted areas
    if (highlight_zones or highlight_stations) and buffer_miles > 0:
        
        # Add buffer circles around highlighted stations
        if highlight_stations and 'highlighted_stations' in locals() and len(highlighted_stations) > 0:
            for idx, row in highlighted_stations.iterrows():
                point_proj = transform(proj, row.geometry)
                buffer_proj = point_proj.buffer(buffer_miles * 1609.34)
                buffer = transform(proj_back, buffer_proj)
                
                gpd.GeoSeries([buffer]).plot(
                    ax=ax,
                    color='green',
                    alpha=0.1,
                    linewidth=1,
                    edgecolor='darkgreen'
                )
        
        # Add buffer around highlighted zones
        if highlight_zones and 'highlighted_zones' in locals() and len(highlighted_zones) > 0:
            combined_geom = highlighted_zones.geometry.unary_union
            combined_proj = transform(proj, combined_geom)
            buffer_proj = combined_proj.buffer(buffer_miles * 1609.34)
            buffer = transform(proj_back, buffer_proj)
            
            gpd.GeoSeries([buffer]).plot(
                ax=ax,
                color='red',
                alpha=0.1,
                linewidth=1,
                edgecolor='darkred'
            )
    
    # Create legend patches
    legend_patches = [
        mpatches.Patch(color='lightgray', label='Other Taxi Zones', alpha=0.3),
        mpatches.Patch(color='lightblue', label='Other Stations', alpha=0.3)
    ]
    
    if subway_lines_gdf is not None:
        legend_patches.append(mpatches.Patch(color='gray', label='Subway Lines', alpha=0.5))
    
    if highlight_zones and 'highlighted_zones' in locals() and len(highlighted_zones) > 0:
        legend_patches.append(mpatches.Patch(color='red', label=f'Zone(s): {", ".join(highlight_zones)}', alpha=0.7))
    
    if highlight_stations and 'highlighted_stations' in locals() and len(highlighted_stations) > 0:
        legend_patches.append(mpatches.Patch(color='green', label=f'Station(s): {", ".join(highlight_stations)}', alpha=0.9))
    
    ax.legend(handles=legend_patches, loc='upper right')
    
    # Title
    title = 'NYC Transit Map'
    if highlight_zones or highlight_stations:
        title += ' - Highlighted Features'
    ax.set_title(title, fontsize=16, fontweight='bold')
    
    ax.set_axis_off()
    plt.tight_layout()
    
    # Save
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    else:
        plt.savefig('nyc_transit_map_highlighted.png', dpi=300, bbox_inches='tight')
    
    plt.show()
    
    # Print summary
    print("\n📊 Map Summary:")
    if highlight_zones and 'highlighted_zones' in locals():
        print(f"   • Highlighted zones: {', '.join(highlight_zones)} ({len(highlighted_zones)} features)")
    if highlight_stations and 'highlighted_stations' in locals():
        print(f"   • Highlighted stations: {', '.join(highlight_stations)} ({len(highlighted_stations)} stations)")
    if buffer_miles > 0:
        print(f"   • Buffer radius: {buffer_miles} miles")

def plot_heatmap_by_day(ridehail_df, taxi_zones_gdf, day_num, summary=False):
    """
    Plot heatmap of HVFHV ridership by taxi zone for a specific day.
    
    Parameters:
    - ridehail_df: HVFHV dataframe
    - taxi_zones_gdf: Taxi zones geodataframe
    - day_num: 1-7 (1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday, 7=Sunday)
    - summary: If True, print summary stats (default False)
    """
    
    # Map day number to name
    days = {1:'Monday', 2:'Tuesday', 3:'Wednesday', 4:'Thursday', 
            5:'Friday', 6:'Saturday', 7:'Sunday'}
    day_name = days[day_num]
    
    # Prepare data
    ridehail_df['date'] = pd.to_datetime(ridehail_df['date'])
    ridehail_df['day_of_week'] = ridehail_df['date'].dt.day_name()
    ridehail_df['PULocationID'] = ridehail_df['PULocationID'].astype(str)
    taxi_zones_gdf['locationid'] = taxi_zones_gdf['locationid'].astype(str)
    
    # Filter for selected day and calculate averages
    day_data = ridehail_df[ridehail_df['day_of_week'] == day_name]
    day_avg = day_data.groupby('PULocationID')['trip_count'].mean().reset_index()
    day_avg.columns = ['PULocationID', 'avg_trip_count']
    
    # Merge with taxi zones and keep only Manhattan
    zones_day = taxi_zones_gdf.merge(day_avg, left_on='locationid', right_on='PULocationID', how='left')
    zones_day['avg_trip_count'] = zones_day['avg_trip_count'].fillna(0)
    manhattan = zones_day[zones_day['borough'] == 'Manhattan']
    
    # Create map
    fig, ax = plt.subplots(1, 1, figsize=(12, 12))
    
    manhattan.plot(column='avg_trip_count', 
                   ax=ax,
                   legend=True,
                   cmap='YlOrRd',
                   edgecolor='black',
                   linewidth=0.5,
                   alpha=0.7,
                   legend_kwds={'label': 'Avg Trip Count',
                               'shrink': 0.6})
    
    ax.set_title(f'HVFHV Avg Ridership - {day_name} (Manhattan)', fontsize=14, fontweight='bold')
    ax.set_axis_off()
    
    plt.tight_layout()
    plt.show()
    
    # Optional summary
    if summary:
        print(f"\n{day_name} - Manhattan Summary:")
        print(f"Total avg trips: {manhattan['avg_trip_count'].sum():,.0f}")
        print("\nTop 5 zones:")
        top = manhattan.nlargest(5, 'avg_trip_count')[['zone', 'avg_trip_count']]
        for idx, row in top.iterrows():
            print(f"  {row['zone']}: {row['avg_trip_count']:,.0f} avg trips")

    