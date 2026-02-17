import matplotlib.pyplot as plt
import geopandas as gpd

# Load the cleaned data
sd_bg = gpd.read_file("data/sd_bg.geojson")


# Plot using log_density
fig, ax = plt.subplots(figsize=(10, 10))
sd_bg.plot(
    column='log_density',  # log-transformed
    cmap='Reds',
    linewidth=0.2,
    edgecolor='black',
    legend=True,
    ax=ax
)

ax.set_title("San Diego Block Groups - Log Job Density")
ax.axis('off')
plt.show()