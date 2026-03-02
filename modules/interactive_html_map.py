import folium
import geopandas as gpd
import pandas as pd
from folium import plugins
import numpy as np

# Load your files
taxi_zones = gpd.read_file('data/02-processed/NYC_Taxi_Zones_20260218.geojson')
subway_lines = gpd.read_file('data/02-processed/MTA_Subway_Service_Lines_20260221.geojson')
subway_stops_df = pd.read_csv('data/02-processed/MTA_Subway_Stations.csv')

# Convert datetime columns to strings in taxi_zones
for col in taxi_zones.columns:
    if pd.api.types.is_datetime64_any_dtype(taxi_zones[col]):
        taxi_zones[col] = taxi_zones[col].astype(str)

# Convert datetime columns to strings in subway_lines
for col in subway_lines.columns:
    if pd.api.types.is_datetime64_any_dtype(subway_lines[col]):
        subway_lines[col] = subway_lines[col].astype(str)

# Convert subway stops to GeoDataFrame
subway_stops = gpd.GeoDataFrame(
    subway_stops_df,
    geometry=gpd.points_from_xy(
        subway_stops_df['GTFS Longitude'], 
        subway_stops_df['GTFS Latitude']
    ),
    crs="EPSG:4326"
)

# Ensure all data is in WGS84 (EPSG:4326) for Folium
if taxi_zones.crs != "EPSG:4326":
    taxi_zones = taxi_zones.to_crs("EPSG:4326")
if subway_lines.crs != "EPSG:4326":
    subway_lines = subway_lines.to_crs("EPSG:4326")

# Calculate center point for the map
center_lat = (taxi_zones.geometry.centroid.y.mean() + subway_stops.geometry.y.mean()) / 2
center_lon = (taxi_zones.geometry.centroid.x.mean() + subway_stops.geometry.x.mean()) / 2

# Create base map
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=11,
    tiles='CartoDB positron',
    control_scale=True
)

# Add fullscreen button
plugins.Fullscreen().add_to(m)

# Add taxi zones (with popup info)
# Simplify the GeoJSON to avoid potential issues
taxi_zones_simple = taxi_zones.copy()

# Keep only essential columns for the popup
popup_fields = []
popup_aliases = []

# Check what columns are available
if 'zone' in taxi_zones_simple.columns:
    popup_fields.append('zone')
    popup_aliases.append('Zone:')
if 'borough' in taxi_zones_simple.columns:
    popup_fields.append('borough')
    popup_aliases.append('Borough:')
if 'LocationID' in taxi_zones_simple.columns:
    popup_fields.append('LocationID')
    popup_aliases.append('Zone ID:')

# If no expected columns, use all non-geometry columns
if not popup_fields:
    popup_fields = [col for col in taxi_zones_simple.columns if col != 'geometry'][:3]  # Limit to first 3
    popup_aliases = [f"{col}:" for col in popup_fields]

style_function = lambda x: {
    'fillColor': 'lightgray',
    'color': 'black',
    'weight': 0.5,
    'fillOpacity': 0.4
}

highlight_function = lambda x: {
    'fillColor': 'yellow',
    'color': 'black',
    'weight': 1,
    'fillOpacity': 0.7
}

# Convert to GeoJSON with string conversion for any remaining non-serializable data
taxi_zones_json = taxi_zones_simple.to_json()
folium.GeoJson(
    taxi_zones_json,
    name='Taxi Zones',
    style_function=style_function,
    highlight_function=highlight_function,
    popup=folium.GeoJsonPopup(
        fields=popup_fields,
        aliases=popup_aliases
    ),
    tooltip=folium.GeoJsonTooltip(
        fields=popup_fields,
        aliases=popup_aliases,
        style="background-color: white; color: black; font-weight: bold;"
    )
).add_to(m)

# Add subway lines
subway_lines_simple = subway_lines.copy()

# Convert any datetime columns in subway_lines
for col in subway_lines_simple.columns:
    if pd.api.types.is_datetime64_any_dtype(subway_lines_simple[col]):
        subway_lines_simple[col] = subway_lines_simple[col].astype(str)

# Try to color by route if column exists
if 'route' in subway_lines_simple.columns or 'line' in subway_lines_simple.columns:
    line_col = 'route' if 'route' in subway_lines_simple.columns else 'line'
    
    # Create a color map
    unique_lines = subway_lines_simple[line_col].unique()
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 
              'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 
              'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 
              'gray', 'black', 'lightgray']
    
    line_color_map = {line: colors[i % len(colors)] for i, line in enumerate(unique_lines)}
    
    for line_name, line_data in subway_lines_simple.groupby(line_col):
        line_json = line_data.to_json()
        folium.GeoJson(
            line_json,
            name=f'Subway Line: {line_name}',
            style_function=lambda x, color=line_color_map[line_name]: {
                'color': color,
                'weight': 2,
                'opacity': 0.8
            }
        ).add_to(m)
else:
    # Just add all lines with default color
    subway_lines_json = subway_lines_simple.to_json()
    folium.GeoJson(
        subway_lines_json,
        name='Subway Lines',
        style_function=lambda x: {
            'color': 'red',
            'weight': 2,
            'opacity': 0.8
        }
    ).add_to(m)

# Add subway stations as circle markers
for idx, row in subway_stops.iterrows():
    # Create popup text
    popup_text = f"""
    <b>Station:</b> {row.get('stop_name', row.get('GTFS Stop Name', 'Unknown'))}<br>
    <b>Lines:</b> {row.get('GTFS Stop Name', 'N/A')}<br>
    """
    
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=3,
        popup=popup_text,
        tooltip=row.get('stop_name', row.get('GTFS Stop Name', 'Subway Station')),
        color='blue',
        fill=True,
        fillColor='blue',
        fillOpacity=0.9
    ).add_to(m)

# Add layer control
folium.LayerControl().add_to(m)

# Add measure control
plugins.MeasureControl(position='topright').add_to(m)

# Save map
m.save('nyc_transportation_interactive.html')

print("Map created successfully! Open 'nyc_transportation_interactive.html' in your browser.")