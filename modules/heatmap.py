import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


# Step 1: Read your data
# Read the ridership CSV
ridership_df = pd.read_csv('data/01-interim/2023_High_Volume_FHV_Trip_Data_cleaned.csv')  # Update with your filename

# Read the taxi zones GeoJSON
zones_gdf = gpd.read_file('data/02-processed/NYC_Taxi_Zones_20260218.geojson')  # Update with your filename

# Step 2: Merge the data
# Make sure the location ID column names match (adjust if needed)
# Common column names: 'LocationID', 'zone_id', 'PULocationID', etc.
merged_gdf = zones_gdf.merge(
    ridership_df, 
    left_on='locationid',  # Column in GeoJSON that identifies zones
    right_on='PULocationID',  # Column in CSV that identifies zones
    how='left'  # Use 'left' to keep all zones even if no rides
)

# If you have multiple days, you might want to aggregate or pick a specific date
# For a specific date:
# specific_date = '2023-02-18'
# merged_gdf = merged_gdf[merged_gdf['pickup_date'] == specific_date]

# For total ridership across all dates:
# merged_gdf = merged_gdf.groupby('PULocationID')['ride_count'].sum().reset_index()
# Then merge this aggregated data

# Step 3: Create the heatmap
fig, ax = plt.subplots(1, 1, figsize=(15, 12))

# Plot the zones with colors based on ridership
merged_gdf.plot(
    column='ride_count',  # Column with the ridership values
    ax=ax,
    legend=True,
    legend_kwds={
        'label': 'Number of Rides',
        'orientation': 'horizontal',
        'shrink': 0.8,
        'pad': 0.01
    },
    cmap='YlOrRd',  # Yellow-Orange-Red colormap (good for heatmaps)
    edgecolor='white',
    linewidth=0.5,
    missing_kwds={
        'color': 'lightgrey',
        'label': 'No data'
    }
)

# Add basemap (optional - requires internet connection)


# Customize the plot
ax.set_title('Taxi Ridership Heatmap by Zone', fontsize=16, pad=20)
ax.set_axis_off()  # Turn off axis

# Adjust layout
plt.tight_layout()

# Save the figure
plt.savefig('taxi_ridership_heatmap.png', dpi=300, bbox_inches='tight')
plt.show()