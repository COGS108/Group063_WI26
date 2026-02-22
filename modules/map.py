import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point

# Load your files
taxi_zones = gpd.read_file('data/02-processed/NYC_Taxi_Zones_20260218.geojson')
subway_lines = gpd.read_file('data/02-processed/MTA_Subway_Service_Lines_20260221.geojson')
subway_stops_df = pd.read_csv('data/02-processed/MTA_Subway_Stations.csv')

# Convert subway stops CSV to GeoDataFrame
# Make sure these column names match your CSV
subway_stops = gpd.GeoDataFrame(
    subway_stops_df,
    geometry=gpd.points_from_xy(
        subway_stops_df['GTFS Longitude'], 
        subway_stops_df['GTFS Latitude']
    ),
    crs="EPSG:4326"  # assuming lat/lon
)

# Reproject everything to same CRS (use taxi_zones CRS as reference)
subway_lines = subway_lines.to_crs(taxi_zones.crs)
subway_stops = subway_stops.to_crs(taxi_zones.crs)

# Create plot
fig, ax = plt.subplots(figsize=(15, 12))

# 1️⃣ Taxi zones (bottom layer)
taxi_zones.plot(
    ax=ax,
    color='lightgray',
    edgecolor='black',
    linewidth=0.5,
    alpha=0.6
)

# 2️⃣ Subway lines (middle layer)
subway_lines.plot(
    ax=ax,
    color='red',
    linewidth=1,
    alpha=0.8
)

# 3️⃣ Subway stations (top layer)
subway_stops.plot(
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