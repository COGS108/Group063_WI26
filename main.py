from modules import maps, utils, histogram
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import importlib

importlib.reload(utils)

station_gdf, taxi_zones_gdf, subway_lines_gdf = utils.prepare_gdf_data()
print(utils.find_stations_near_taxi_zone(161, 0, station_gdf, taxi_zones_gdf))

subway_ridership_df, hvfhv_df =utils.prepare_ridership_data()
histogram.create_popularity_histogram(hvfhv_df, subway_ridership_df, 1)