import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Load the shapefile
block_groups = gpd.read_file("data/tl_2023_bg/tl_2023_06_bg.shp")
block_groups = block_groups[[
    'GEOID',       # unique ID
    'COUNTYFP',    # county FIPS code
    'geometry',    # polygon
    'ALAND',       # land area
    'INTPTLAT',    # centroid latitude
    'INTPTLON',    # centroid longitude
    'NAMELSAD'     # human-readable block group name
]].copy()

#Filter to just San Diego County (FIPS 073)
sd_bg = block_groups[block_groups["COUNTYFP"] == "073"].copy()

wac = pd.read_csv("data/lodes_wac_totalJobs_income.csv")
wac = wac[['w_geocode', 'C000']]
wac['w_geocode'] = wac['w_geocode'].astype(str).str.zfill(15)

#we want the block group, not the blocks
wac['GEOID_bg'] = wac['w_geocode'].str[:12]

#Sum the jobs by block group
jobs_bg = wac.groupby('GEOID_bg')['C000'].sum().reset_index()
jobs_bg = jobs_bg.rename(columns={'GEOID_bg': 'GEOID'})


sd_bg = sd_bg.merge(jobs_bg, on='GEOID', how='left')


#use square kilometers instead of square meters
sd_bg['area_km2'] = sd_bg['ALAND'] / 1_000_000
#job density = jobs per square kilometer
sd_bg['job_density'] = sd_bg['C000'] / sd_bg['area_km2']

print(sd_bg[['area_km2', 'C000', 'job_density']].head(20))
print(sd_bg.columns)
num_block_groups = sd_bg.shape[0]
print(f"Number of block groups in San Diego: {num_block_groups}")

max_density = sd_bg['job_density'].max()
print(f"Maximum job density: {max_density:.0f} jobs per km²")

sd_bg['log_density'] = np.log1p(sd_bg['job_density'])

sd_bg_csv = sd_bg[[
    'GEOID',
    'NAMELSAD',
    'ALAND',
    'area_km2',
    'C000',
    'job_density',
    'log_density',
    'INTPTLAT',
    'INTPTLON'
]].copy()

# Save to CSV
sd_bg_csv.to_csv("data/sd_bg.csv", index=False)
print("CSV saved as data/sd_bg.csv")

# Save to GeoJSON
sd_bg.to_file("data/sd_bg.geojson", driver="GeoJSON")
print("GeoJSON saved as data/sd_bg.geojson")

