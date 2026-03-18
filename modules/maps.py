import pandas as pd
import geopandas as gpd
import seaborn as sns
from scipy import stats
from shapely.geometry import Point, box
import numpy as np
from shapely.ops import transform
import pyproj
from functools import partial
from matplotlib import pyplot as plt
import matplotlib.patches as mpatches


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
    #plt.show()

    return fig

#Plots the transit map entirely

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

    #plt.show()
    return fig

def plot_transit_map2(subway_stations_gdf, taxi_zones_gdf, subway_lines_gdf=None,
                    highlight_zones=None, highlight_stations=None,
                    buffer_miles=0.25, figsize=(15, 12), summary = False, save_path=None):
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
    
    #plt.show()
    
    
    if summary:
        # Print summary
        print("\n📊 Map Summary:")
        if highlight_zones and 'highlighted_zones' in locals():
            print(f"   • Highlighted zones: {', '.join(highlight_zones)} ({len(highlighted_zones)} features)")
        if highlight_stations and 'highlighted_stations' in locals():
            print(f"   • Highlighted stations: {', '.join(highlight_stations)} ({len(highlighted_stations)} stations)")
        if buffer_miles > 0:
            print(f"   • Buffer radius: {buffer_miles} miles")
            
    return fig

def plot_ridehail_heatmap_by_day(ridehail_df, taxi_zones_gdf, day_num, vmax=20000, summary=False, save_path=None):
    """
    Plot heatmap of HVFHV ridership by taxi zone for a specific day.
    
    Parameters:
    - ridehail_df: HVFHV dataframe
    - taxi_zones_gdf: Taxi zones geodataframe
    - day_num: 1-7 (1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday, 7=Sunday)
    - vmax: Maximum value for color scale (default 20000 for ridehail)
    - summary: If True, print summary stats (default False)
    - save_path: If provided, save the figure to this path
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
    
    # Create map with fixed scale
    fig, ax = plt.subplots(1, 1, figsize=(12, 12))
    
    # Create a custom colorbar with fixed limits
    import matplotlib.colors as colors
    
    # Use the same colormap but with fixed vmin/vmax
    norm = colors.Normalize(vmin=0, vmax=vmax)
    
    plot = manhattan.plot(column='avg_trip_count', 
                          ax=ax,
                          norm=norm,
                          cmap='YlOrRd',
                          edgecolor='black',
                          linewidth=0.5,
                          alpha=0.7,
                          legend=True,
                          legend_kwds={'label': f'Avg Trip Count (0-{vmax})',
                                      'shrink': 0.6,
                                      'orientation': 'horizontal',
                                      'pad': 0.02,
                                      'extend': 'max'})  # Add arrow for values > vmax
    
    # Add title with day and max value info
    max_val = manhattan['avg_trip_count'].max()
    ax.set_title(f'Ridehail Avg Ridership - {day_name}', fontsize=14, fontweight='bold')
    ax.set_axis_off()
    
    plt.tight_layout()
    
    # Save if path provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    #plt.show()
    
    # Optional summary
    if summary:
        print(f"\n{day_name} - Manhattan Summary:")
        print(f"Total avg trips: {manhattan['avg_trip_count'].sum():,.0f}")
        print(f"Maximum zone value: {max_val:,.0f}")
        print(f"Zones capped at {vmax}: {(manhattan['avg_trip_count'] > vmax).sum()}")
        print("\nTop 5 zones:")
        top = manhattan.nlargest(5, 'avg_trip_count')[['zone', 'avg_trip_count']]
        for idx, row in top.iterrows():
            capped = " (capped)" if row['avg_trip_count'] > vmax else ""
            print(f"  {row['zone']}: {row['avg_trip_count']:,.0f}{capped}")
    
    return fig

def plot_subway_heatmap_by_day(mta_df, subway_stations_gdf, taxi_zones_gdf, day_num, vmax=100000, summary=False, save_path=None):
    """
    Plot heatmap of subway ridership by taxi zone for a specific day of week.
    
    Parameters:
    - mta_df: MTA subway dataframe with station_complex_id, date, and ridership
    - taxi_zones_gdf: Taxi zones geodataframe
    - day_num: 1-7 (1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 
                     5=Friday, 6=Saturday, 7=Sunday)
    - vmax: Maximum value for color scale (default 100000 for MTA)
    - summary: If True, print summary stats (default False)
    - save_path: If provided, save the figure to this path
    """
    
    # Map day number to name
    days = {1:'Monday', 2:'Tuesday', 3:'Wednesday', 4:'Thursday', 
            5:'Friday', 6:'Saturday', 7:'Sunday'}
    day_name = days[day_num]
    
    # Prepare subway stations with buffer to map to taxi zones
    #print("\nMapping subway stations to taxi zones...")
    
    # Make a copy and ensure CRS
    stations_gdf = subway_stations_gdf.copy()
    if stations_gdf.crs is None:
        stations_gdf = stations_gdf.set_crs('EPSG:4326')
    
    # Convert to projected CRS for buffering
    stations_gdf = stations_gdf.to_crs('EPSG:3857')
    taxi_zones_proj = taxi_zones_gdf.to_crs('EPSG:3857')
    
    # Create buffers (0.5 miles)
    buffer_miles = 0.1
    buffer_meters = buffer_miles * 1609.34
    stations_gdf['buffer_geom'] = stations_gdf.geometry.buffer(buffer_meters)
    
    # Spatial join using buffers
    stations_buffer = stations_gdf[['Complex ID', 'Stop Name', 'Borough']].copy()
    stations_buffer = stations_buffer.set_geometry(stations_gdf['buffer_geom'])
    stations_buffer.crs = stations_gdf.crs
    
    station_zone_mapping = gpd.sjoin(
        stations_buffer,
        taxi_zones_proj,
        how='left',
        predicate='intersects'
    )
    
    # Remove duplicates
    station_zone_mapping = station_zone_mapping.drop_duplicates(subset=['Complex ID', 'locationid'])
    
    # Prepare MTA data
    mta_df['date'] = pd.to_datetime(mta_df['date'])
    mta_df['day_of_week'] = mta_df['date'].dt.day_name()
    mta_df['station_complex_id'] = mta_df['station_complex_id'].astype(str)
    station_zone_mapping['Complex ID'] = station_zone_mapping['Complex ID'].astype(str)
    station_zone_mapping['locationid'] = station_zone_mapping['locationid'].astype(str)
    
    # Filter for selected day
    #print(f"\nFiltering for {day_name}...")
    day_data = mta_df[mta_df['day_of_week'] == day_name]
    
    # Merge ridership with zone mapping
    station_zone_ridership = station_zone_mapping.merge(
        day_data,
        left_on='Complex ID',
        right_on='station_complex_id',
        how='left'
    )
    
    # Calculate average ridership by taxi zone for the selected day
    #print("Calculating average ridership by zone...")
    day_avg = station_zone_ridership.groupby('locationid').agg({
        'ridership': 'mean'
    }).reset_index()
    day_avg.columns = ['locationid', 'avg_ridership']
    day_avg['locationid'] = day_avg['locationid'].astype(str)
    
    # Merge with taxi zones
    taxi_zones_gdf['locationid'] = taxi_zones_gdf['locationid'].astype(str)
    zones_day = taxi_zones_gdf.merge(day_avg, on='locationid', how='left')
    zones_day['avg_ridership'] = zones_day['avg_ridership'].fillna(0)
    
    # Keep only Manhattan zones
    manhattan = zones_day[zones_day['borough'] == 'Manhattan'].copy()
    
    # Create map with fixed scale
    fig, ax = plt.subplots(1, 1, figsize=(12, 12))
    
    import matplotlib.colors as colors
    norm = colors.Normalize(vmin=0, vmax=vmax)
    
    manhattan.plot(column='avg_ridership', 
                   ax=ax,
                   norm=norm,
                   cmap='YlOrRd',
                   edgecolor='black',
                   linewidth=0.5,
                   alpha=0.7,
                   legend=True,
                   legend_kwds={'label': f'Avg Subway Ridership (0-{vmax:,.0f})',
                               'shrink': 0.6,
                               'orientation': 'horizontal',
                               'pad': 0.02,
                               'extend': 'max'})
    
    # Add subway station locations for context
    manhattan_stations = stations_gdf[stations_gdf['Borough'] == 'Manhattan']
    if len(manhattan_stations) > 0:
        manhattan_stations.plot(ax=ax, 
                               color='blue', 
                               markersize=3, 
                               alpha=0.5,
                               label='Subway Stations')
    
    # Add title with day and max value info
    max_val = manhattan['avg_ridership'].max()
    ax.set_title(f'MTA Subway Avg Ridership - {day_name})', fontsize=14, fontweight='bold')
    ax.set_axis_off()
    
    plt.tight_layout()
    
    # Save if path provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    #plt.show()
    
    # Optional summary
    if summary:
        print("\n" + "=" * 60)
        print(f"{day_name} - MANHATTAN SUMMARY")
        print("=" * 60)
        
        total_avg = manhattan['avg_ridership'].sum()
        print(f"\nTotal average ridership: {total_avg:,.0f}")
        print(f"Maximum zone value: {max_val:,.0f}")
        print(f"Zones capped at {vmax:,.0f}: {(manhattan['avg_ridership'] > vmax).sum()}")
        
        print(f"\nTop 5 zones by ridership:")
        top = manhattan.nlargest(5, 'avg_ridership')[['zone', 'avg_ridership']]
        for idx, row in top.iterrows():
            capped = " (capped)" if row['avg_ridership'] > vmax else ""
            print(f"  {row['zone']}: {row['avg_ridership']:,.0f}{capped}")
        
        # Find the complexes in these top zones
        print(f"\nComplex IDs in top zones:")
        top_zone_names = top['zone'].tolist()
        
        # Get the mapping of zones to complexes
        zone_complex_mapping = station_zone_ridership[station_zone_ridership['locationid'].isin(
            manhattan.nlargest(5, 'avg_ridership')['locationid']
        )]
        
        # Group by zone and list unique Complex IDs
        for zone_name in top_zone_names:
            zone_locid = manhattan[manhattan['zone'] == zone_name]['locationid'].values
            if len(zone_locid) > 0:
                complexes = zone_complex_mapping[zone_complex_mapping['locationid'] == zone_locid[0]]
                unique_complexes = complexes[['Complex ID', 'Stop Name']].drop_duplicates()
                if len(unique_complexes) > 0:
                    print(f"\n  {zone_name}:")
                    for _, row in unique_complexes.iterrows():
                        print(f"    Complex {row['Complex ID']}: {row['Stop Name']}")
        
        # Only show bottom if there are zones with positive ridership
        positive = manhattan[manhattan['avg_ridership'] > 0]
        if len(positive) > 5:
            print(f"\nBottom 5 zones (with positive ridership):")
            bottom = positive.nsmallest(5, 'avg_ridership')[['zone', 'avg_ridership']]
            for idx, row in bottom.iterrows():
                capped = " (capped)" if row['avg_ridership'] > vmax else ""
                print(f"  {row['zone']}: {row['avg_ridership']:,.0f}{capped}")
            
            # Find the complexes in these bottom zones
            print(f"\nComplex IDs in bottom zones:")
            bottom_zone_names = bottom['zone'].tolist()
            
            # Get the mapping of zones to complexes
            zone_complex_mapping = station_zone_ridership[station_zone_ridership['locationid'].isin(
                manhattan[manhattan['zone'].isin(bottom_zone_names)]['locationid']
            )]
            
            # Group by zone and list unique Complex IDs
            for zone_name in bottom_zone_names:
                zone_locid = manhattan[manhattan['zone'] == zone_name]['locationid'].values
                if len(zone_locid) > 0:
                    complexes = zone_complex_mapping[zone_complex_mapping['locationid'] == zone_locid[0]]
                    unique_complexes = complexes[['Complex ID', 'Stop Name']].drop_duplicates()
                    if len(unique_complexes) > 0:
                        print(f"\n  {zone_name}:")
                        for _, row in unique_complexes.iterrows():
                            print(f"    Complex {row['Complex ID']}: {row['Stop Name']}")
            
            # Count zones with no ridership
            zero_zones = len(manhattan[manhattan['avg_ridership'] == 0])
            if zero_zones > 0:
                print(f"\nZones with no subway ridership: {zero_zones}")
    
    return fig

def plot_ratio_heatmap_by_day(ridehail_df, mta_df, subway_stations_gdf, taxi_zones_gdf, day_num, vmax=2, save_path=None):
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.colors as colors
    import geopandas as gpd

    # Day mapping
    days = {1:'Monday', 2:'Tuesday', 3:'Wednesday', 4:'Thursday', 
            5:'Friday', 6:'Saturday', 7:'Sunday'}
    day_name = days[day_num]

    # -------------------------
    # RIDEHAIL PROCESSING
    # -------------------------
    ridehail_df['date'] = pd.to_datetime(ridehail_df['date'])
    ridehail_df['day_of_week'] = ridehail_df['date'].dt.day_name()
    ridehail_df['PULocationID'] = ridehail_df['PULocationID'].astype(str)

    rh_day = ridehail_df[ridehail_df['day_of_week'] == day_name]
    rh_avg = rh_day.groupby('PULocationID')['trip_count'].mean().reset_index()
    rh_avg.columns = ['locationid', 'ridehail_avg']

    # -------------------------
    # SUBWAY PROCESSING (reuse your logic)
    # -------------------------
    stations_gdf = subway_stations_gdf.copy()
    stations_gdf = stations_gdf.set_crs('EPSG:4326', allow_override=True).to_crs('EPSG:3857')
    taxi_proj = taxi_zones_gdf.to_crs('EPSG:3857')

    buffer_meters = 0.1 * 1609.34
    stations_gdf['geometry'] = stations_gdf.geometry.buffer(buffer_meters)

    station_zone = gpd.sjoin(
        stations_gdf[['Complex ID', 'geometry']],
        taxi_proj,
        how='left',
        predicate='intersects'
    ).drop_duplicates(subset=['Complex ID', 'locationid'])

    # Prep MTA
    mta_df['date'] = pd.to_datetime(mta_df['date'])
    mta_df['day_of_week'] = mta_df['date'].dt.day_name()
    mta_df['station_complex_id'] = mta_df['station_complex_id'].astype(str)

    station_zone['Complex ID'] = station_zone['Complex ID'].astype(str)
    station_zone['locationid'] = station_zone['locationid'].astype(str)

    mta_day = mta_df[mta_df['day_of_week'] == day_name]

    merged = station_zone.merge(
        mta_day,
        left_on='Complex ID',
        right_on='station_complex_id',
        how='left'
    )

    mta_avg = merged.groupby('locationid')['ridership'].mean().reset_index()
    mta_avg.columns = ['locationid', 'mta_avg']

    # -------------------------
    # COMBINE
    # -------------------------
    zones = taxi_zones_gdf.copy()
    zones['locationid'] = zones['locationid'].astype(str)

    combined = zones.merge(rh_avg, on='locationid', how='left')
    combined = combined.merge(mta_avg, on='locationid', how='left')

    combined['ridehail_avg'] = combined['ridehail_avg'].fillna(0)
    combined['mta_avg'] = combined['mta_avg'].fillna(0)

    # -------------------------
    # RATIO (log)
    # -------------------------
    combined['log_ratio'] = np.log((combined['mta_avg'] + 1) / (combined['ridehail_avg'] + 1))

    # Focus Manhattan
    manhattan = combined[combined['borough'] == 'Manhattan']

    # -------------------------
    # PLOT
    # -------------------------
    fig, ax = plt.subplots(1, 1, figsize=(12, 12))

    norm = colors.TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)

    manhattan.plot(
        column='log_ratio',
        cmap='RdBu',   # red = MTA, blue = ridehail
        norm=norm,
        edgecolor='black',
        linewidth=0.5,
        legend=True,
        legend_kwds={
            'label': 'Log Ratio (MTA / Ridehail)',
            'shrink': 0.6
        },
        ax=ax
    )

    ax.set_title(f'MTA vs Ridehail Ratio - {day_name}', fontsize=14, fontweight='bold')
    ax.set_axis_off()

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    #plt.show()

    return fig

def plot_mode_share_heatmap_by_day(
    ridehail_df, 
    mta_df, 
    subway_stations_gdf, 
    taxi_zones_gdf, 
    day_num, 
    save_path=None,
    summary=False
):
    import numpy as np
    import matplotlib.pyplot as plt
    import geopandas as gpd

    # Day mapping
    days = {1:'Monday', 2:'Tuesday', 3:'Wednesday', 4:'Thursday', 
            5:'Friday', 6:'Saturday', 7:'Sunday'}
    day_name = days[day_num]

    # -------------------------
    # RIDEHAIL PROCESSING
    # -------------------------
    ridehail_df['date'] = pd.to_datetime(ridehail_df['date'])
    ridehail_df['day_of_week'] = ridehail_df['date'].dt.day_name()
    ridehail_df['PULocationID'] = ridehail_df['PULocationID'].astype(str)

    rh_day = ridehail_df[ridehail_df['day_of_week'] == day_name]
    rh_avg = rh_day.groupby('PULocationID')['trip_count'].mean().reset_index()
    rh_avg.columns = ['locationid', 'ridehail_avg']

    # -------------------------
    # SUBWAY PROCESSING
    # -------------------------
    stations_gdf = subway_stations_gdf.copy()
    stations_gdf = stations_gdf.set_crs('EPSG:4326', allow_override=True).to_crs('EPSG:3857')
    taxi_proj = taxi_zones_gdf.to_crs('EPSG:3857')

    buffer_meters = 0.1 * 1609.34
    stations_gdf['geometry'] = stations_gdf.geometry.buffer(buffer_meters)

    station_zone = gpd.sjoin(
        stations_gdf[['Complex ID', 'geometry']],
        taxi_proj,
        how='left',
        predicate='intersects'
    ).drop_duplicates(subset=['Complex ID', 'locationid'])

    # Prep MTA
    mta_df['date'] = pd.to_datetime(mta_df['date'])
    mta_df['day_of_week'] = mta_df['date'].dt.day_name()
    mta_df['station_complex_id'] = mta_df['station_complex_id'].astype(str)

    station_zone['Complex ID'] = station_zone['Complex ID'].astype(str)
    station_zone['locationid'] = station_zone['locationid'].astype(str)

    mta_day = mta_df[mta_df['day_of_week'] == day_name]

    merged = station_zone.merge(
        mta_day,
        left_on='Complex ID',
        right_on='station_complex_id',
        how='left'
    )

    mta_avg = merged.groupby('locationid')['ridership'].mean().reset_index()
    mta_avg.columns = ['locationid', 'mta_avg']

    # -------------------------
    # COMBINE
    # -------------------------
    zones = taxi_zones_gdf.copy()
    zones['locationid'] = zones['locationid'].astype(str)

    combined = zones.merge(rh_avg, on='locationid', how='left')
    combined = combined.merge(mta_avg, on='locationid', how='left')

    combined['ridehail_avg'] = combined['ridehail_avg'].fillna(0)
    combined['mta_avg'] = combined['mta_avg'].fillna(0)

    # -------------------------
    # MODE SHARE
    # -------------------------
    combined['total'] = combined['ridehail_avg'] + combined['mta_avg']

    # Avoid division by zero
    combined['ridehail_share'] = np.where(
        combined['total'] > 0,
        combined['ridehail_avg'] / combined['total'],
        0
    )

    # Focus Manhattan
    manhattan = combined[combined['borough'] == 'Manhattan']

    # -------------------------
    # PLOT
    # -------------------------
    fig, ax = plt.subplots(1, 1, figsize=(12, 12))

    manhattan.plot(
        column='ridehail_share',
        cmap='viridis',   # nice gradient from low → high
        vmin=0,
        vmax=1,
        edgecolor='black',
        linewidth=0.5,
        legend=True,
        legend_kwds={
            'label': 'Ride-hailing Mode Share (0 = MTA, 1 = Ridehail)',
            'shrink': 0.6
        },
        ax=ax
    )

    ax.set_title(f'Ride-hailing Mode Share - {day_name}', fontsize=14, fontweight='bold')
    ax.set_axis_off()

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    #plt.show()

    # -------------------------
    # SUMMARY
    # -------------------------
    if summary:
        print(f"\n{day_name} - Mode Share Summary")
        print("=" * 40)

        print(f"Average ridehail share: {manhattan['ridehail_share'].mean():.2f}")

        print("\nTop 5 ridehail-dominant zones:")
        top = manhattan.nlargest(5, 'ridehail_share')[['zone', 'ridehail_share']]
        for _, row in top.iterrows():
            print(f"  {row['zone']}: {row['ridehail_share']:.2f}")

        print("\nTop 5 MTA-dominant zones:")
        bottom = manhattan.nsmallest(5, 'ridehail_share')[['zone', 'ridehail_share']]
        for _, row in bottom.iterrows():
            print(f"  {row['zone']}: {row['ridehail_share']:.2f}")

    return fig

def plot_zonal_correlation_heatmap(mta_zones_df, ridehail_df, taxi_zones_gdf, min_days=30, summary = False, save_path=None):
    """
    Plot correlation between MTA and ridehail on an actual NYC map.
    Zones with insufficient data appear in light gray.
    """
    
    
    # Prepare data
    ridehail_daily = ridehail_df.groupby(['date', 'PULocationID'])['trip_count'].sum().reset_index()
    ridehail_daily['date'] = pd.to_datetime(ridehail_daily['date'])
    ridehail_daily['PULocationID'] = ridehail_daily['PULocationID'].astype(str)
    
    mta_zones_df['date'] = pd.to_datetime(mta_zones_df['date'])
    mta_zones_df['locationid'] = mta_zones_df['locationid'].astype(str)
    taxi_zones_gdf['locationid'] = taxi_zones_gdf['locationid'].astype(str)
    
    # Calculate correlations for each zone
    zones = mta_zones_df['locationid'].unique()
    corr_data = []
    
    for zone in zones:
        # Merge MTA and ridehail data for this zone
        zone_mta = mta_zones_df[mta_zones_df['locationid'] == zone]
        zone_ride = ridehail_daily[ridehail_daily['PULocationID'] == zone]
        
        merged = pd.merge(
            zone_mta[['date', 'ridership']],
            zone_ride[['date', 'trip_count']],
            on='date',
            how='inner'
        )
        
        if len(merged) >= min_days:
            corr, p_val = stats.pearsonr(merged['trip_count'], merged['ridership'])
            corr_data.append({
                'locationid': zone,
                'correlation': corr,
                'p_value': p_val,
                'days': len(merged)
            })
        else:
            # Include zone but mark as insufficient data
            corr_data.append({
                'locationid': zone,
                'correlation': np.nan,
                'p_value': np.nan,
                'days': len(merged)
            })
    
    # Create DataFrame
    corr_df = pd.DataFrame(corr_data)
    
    # Merge with taxi zones
    zones_with_corr = taxi_zones_gdf.merge(corr_df, on='locationid', how='left')
    
    # Focus Manhattan
    manhattan = zones_with_corr[zones_with_corr['borough'] == 'Manhattan'].copy()
    
    # Create map
    fig, ax = plt.subplots(1, 1, figsize=(14, 12))
    
    # First plot all zones in light gray (basemap)
    manhattan.plot(
        ax=ax,
        color='lightgray',
        edgecolor='black',
        linewidth=0.3,
        alpha=0.5
    )
    
    # Then plot zones with valid correlations on top
    valid_data = manhattan[manhattan['correlation'].notna()]
    valid_data.plot(
        column='correlation',
        cmap='RdYlGn',  # Red (negative) to Yellow (neutral) to Green (positive)
        vmin=-1,
        vmax=1,
        edgecolor='black',
        linewidth=0.5,
        alpha=0.8,
        legend=True,
        legend_kwds={
            'label': 'MTA vs Ridehail Correlation',
            'shrink': 0.6,
            'orientation': 'horizontal',
            'pad': 0.02,
            'extend': 'both'
        },
        ax=ax
    )
    
    # Add labels for extreme correlations
    top_pos = valid_data.nlargest(5, 'correlation')
    top_neg = valid_data.nsmallest(5, 'correlation')
    
    for idx, row in pd.concat([top_pos, top_neg]).iterrows():
        if pd.notna(row['correlation']):
            centroid = row.geometry.centroid
            color = 'darkgreen' if row['correlation'] > 0.3 else 'darkred' if row['correlation'] < -0.3 else 'black'
            
            # Add significance stars
            stars = ""
            if row['p_value'] < 0.001:
                stars = "***"
            elif row['p_value'] < 0.01:
                stars = "**"
            elif row['p_value'] < 0.05:
                stars = "*"
            
            ax.text(
                centroid.x, centroid.y,
                f"{row['zone']}\n{row['correlation']:.2f}{stars}",
                fontsize=7,
                ha='center',
                va='center',
                bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.7, edgecolor=color, linewidth=1)
            )
    
    # Add a legend for insufficient data
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='lightgray', edgecolor='black', alpha=0.5, label=f'Insufficient data (<{min_days} days)')
    ]
    ax.legend(handles=legend_elements, loc='lower right')
    
    ax.set_title(f'MTA vs Ridehail Correlation by Taxi Zone (Manhattan)\nZones with <{min_days} days shown in gray', 
                 fontsize=16, fontweight='bold')
    ax.set_axis_off()
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    #plt.show()
    
    if summary:
        # Summary
        valid = manhattan[manhattan['correlation'].notna()]
        insufficient = manhattan[manhattan['correlation'].isna()]
        
        print(f"\n📊 Correlation Summary (Manhattan):")
        print(f"Zones with sufficient data (≥{min_days} days): {len(valid)}")
        print(f"Zones with insufficient data: {len(insufficient)}")
        print(f"Mean correlation: {valid['correlation'].mean():.3f}")
        print(f"Range: {valid['correlation'].min():.3f} to {valid['correlation'].max():.3f}")
        
        if len(insufficient) > 0:
            print(f"\n⚠️ Zones with insufficient data:")
            for idx, row in insufficient.iterrows():
                print(f"  {row['zone']}: {row['days']} days")
        
        print("\n🔵 Strongest Positive Correlations (move together):")
        for idx, row in top_pos.iterrows():
            stars = ""
            if row['p_value'] < 0.001:
                stars = "***"
            elif row['p_value'] < 0.01:
                stars = "**"
            elif row['p_value'] < 0.05:
                stars = "*"
            print(f"  {row['zone']}: {row['correlation']:.3f}{stars} ({row['days']} days)")
        
        print("\n🔴 Strongest Negative Correlations (move opposite):")
        for idx, row in top_neg.iterrows():
            stars = ""
            if row['p_value'] < 0.001:
                stars = "***"
            elif row['p_value'] < 0.01:
                stars = "**"
            elif row['p_value'] < 0.05:
                stars = "*"
            print(f"  {row['zone']}: {row['correlation']:.3f}{stars} ({row['days']} days)")
    
    return fig, manhattan
