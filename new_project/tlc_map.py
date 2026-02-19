import geopandas as gpd
import matplotlib.pyplot as plt

# Read the GeoJSON file
gdf = gpd.read_file('data/NYC_Taxi_Zones_20260218.geojson')

# Create a figure with a specific size
fig, ax = plt.subplots(1, 1, figsize=(15, 12))

# Plot with boroughs colored differently
# First, let's see what boroughs we have
print("Boroughs in the data:", gdf['borough'].unique())

# Plot with different colors for each borough
gdf.plot(
    column='borough',  # Color by borough
    categorical=True,
    legend=True,
    ax=ax,
    edgecolor='black',
    linewidth=0.3,
    alpha=0.7,
    legend_kwds={'title': 'Borough'}
)

# Add title
plt.title('NYC Taxi Zones by Borough', fontsize=16)

# Remove axes
ax.set_axis_off()

# Add some context
plt.text(0.02, 0.98, f'Total Zones: {len(gdf)}', 
         transform=ax.transAxes, fontsize=12, 
         verticalalignment='top')

plt.tight_layout()
plt.savefig('nyc_taxi_zones_map.png', dpi=300, bbox_inches='tight')
plt.show()