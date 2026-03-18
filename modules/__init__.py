"""
NYC Transit Analysis Tools
==========================
This package contains tools for analyzing NYC subway and taxi data.
"""

# Import key functions to make them available at package level
from .maps import (
    
    plot_stations_near_taxi_zone,
    plot_transit_map,
    plot_transit_map2,
    plot_ridehail_heatmap_by_day,
    plot_subway_heatmap_by_day,
    plot_ratio_heatmap_by_day,
    plot_mode_share_heatmap_by_day,
    plot_zonal_correlation_heatmap
)

from .graph import (
    create_popularity_histogram,
    compare_daily_patterns,
    compare_multiple_daily,
    plot_ridership_histogram,
    plot_mta_vs_ridehail_daily,
    plot_rolling_correlation,
    plot_mta_vs_ridehail_both,
    scatterplot_mta_vs_ridehail_daily
)
from .utils import (
    find_stations_near_taxi_zone,
    prepare_gdf_data,
    prepare_ridership_data,
    eliminate_ridership_outliers,
    create_mta_zone_daily_df
)
from .data_cleaning import (
    clean_FHV_data,
    clean_MTS_data,
    clean_subway_stations,
    load_and_shorten_data
)

# Define what gets imported with "from functions import *"
__all__ = [
    'plot_station_map',
    'plot_taxi_zone_with_buffer',
    'plot_borough_map',
    'plot_station_histogram',
    'plot_borough_distribution',
    'plot_accessibility_chart',
    'find_stations_near_taxi_zone',
    'count_stations_by_borough',
    'analyze_accessibility',
    'load_subway_data',
    'load_taxi_zones',
    'setup_plotting_style'
]

# Package metadata
__version__ = '0.1.0'
__author__ = 'Your Name'