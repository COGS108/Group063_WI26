from functions import maps, utils
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

subway_lines_path = 'data/02-processed/map_files/MTA_Subway_Service_Lines.geojson'
taxi_zones_path = 'data/02-processed/map_files/NYC_Taxi_Zones.geojson'
stations_path = 'data/02-processed/map_files/MTA_Subway_Stations_cleaned.csv'
station_gdf, taxi_zones_gdf, subway_lines_gdf = utils.prepare_gdf_data(
    stations_path,
    taxi_zones_path,
    subway_lines_path
)

#print(utils.find_stations_near_taxi_zone(161, 0, station_gdf, taxi_zones_gdf))

histogram.create_popularity_histogram(None, None, '2023-01')
