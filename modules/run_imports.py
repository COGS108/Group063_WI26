"""Notebook import helpers for the final project."""

from __future__ import annotations

from datetime import datetime

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
from shapely.geometry import Point, box
from shapely.ops import unary_union
from statsmodels.nonparametric.smoothers_lowess import lowess

from modules import graph, maps, utils


def _build_namespace(load_default_data: bool = True) -> dict[str, object]:
    """Create the namespace the notebook expects."""
    namespace: dict[str, object] = {
        "datetime": datetime,
        "Point": Point,
        "box": box,
        "gpd": gpd,
        "graph": graph,
        "lowess": lowess,
        "maps": maps,
        "np": np,
        "pd": pd,
        "plt": plt,
        "sns": sns,
        "unary_union": unary_union,
        "utils": utils,
    }

    if load_default_data:
        subway_stations_gdf, taxi_zones_gdf, subway_lines_gdf = utils.prepare_gdf_data()
        ridehail_df, mta_df = utils.prepare_ridership_data(
            "data/02-processed/ridehailing_daily_cleaned.csv",
            "data/02-processed/MTA_Ridership_cleaned.csv",
        )
        namespace.update(
            {
                "subway_stations_gdf": subway_stations_gdf,
                "taxi_zones_gdf": taxi_zones_gdf,
                "subway_lines_gdf": subway_lines_gdf,
                "ridehail_df": ridehail_df,
                "mta_df": mta_df,
            }
        )

    return namespace


def setup_final_project_imports(
    target_globals: dict[str, object] | None = None,
    load_default_data: bool = True,
    return_namespace: bool = False,
) -> dict[str, object] | None:
    """
    Load common imports for ``03-FinalProject.ipynb``.

    Pass ``globals()`` from a notebook cell to make the imported names available
    across later cells.
    """
    namespace = _build_namespace(load_default_data=load_default_data)

    if target_globals is not None:
        target_globals.update(namespace)

    if return_namespace:
        return namespace

    return None
