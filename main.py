import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
from shapely.geometry import Point, box
from shapely.ops import unary_union
from datetime import datetime
from modules import graph, utils, maps

#Helper functions to prepare the dataframes that we need
subway_stations_gdf, taxi_zones_gdf, subway_lines_gdf = utils.prepare_gdf_data()
hvfhv_df, mta_df = utils.prepare_ridership_data()

utils.eliminate_ridership_outliers(hvfhv_df, mta_df)
