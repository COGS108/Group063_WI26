"""Statistical tests for day-to-day Manhattan ride-hailing ridership patterns.

This module compares daily ridership dynamics across four TLC services:
- For Hire Vehicles (FHV)
- High-Volume For Hire Vehicles (HVFHV)
- Green Taxi
- Yellow Taxi

Primary question:
"Do methods increase/decrease by similar factors on the same day?"

Key p-value columns in outputs:
- p_value: raw p-value from the individual test.
- p_value_fdr_bh: Benjamini-Hochberg adjusted p-value for multiple comparisons.
"""

from __future__ import annotations

import argparse
import json
import os
from itertools import combinations
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, pearsonr, ttest_rel


DEFAULT_RIDEHAIL_DIR = Path("data/01-interim/TLC_ridehail")
DEFAULT_TAXI_ZONES_PATH = Path("data/02-processed/map_files/NYC_Taxi_Zones.geojson")

SERVICE_FILES = {
    "fhv": "2023_For_Hire_Vehicles_Trip_Data_cleaned.csv",
    "hvfhv": "2023_High_Volume_FHV_Trip_Data_cleaned.csv",
    "green_taxi": "2023_Green_Taxi_Trip_Data_cleaned.csv",
    "yellow_taxi": "2023_Yellow_Taxi_Trip_Data_cleaned.csv",
}


def _find_column(df: pd.DataFrame, candidates: Iterable[str]) -> str:
    """Return first matching column name (case-insensitive)."""
    lowered = {col.lower(): col for col in df.columns}
    for cand in candidates:
        key = cand.lower()
        if key in lowered:
            return lowered[key]
    raise KeyError(f"Missing required column. Tried: {list(candidates)}")


def load_manhattan_location_ids(taxi_zones_geojson_path: os.PathLike) -> List[int]:
    """Load Manhattan taxi zone IDs from the TLC taxi zones geojson."""
    with open(taxi_zones_geojson_path, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    ids: List[int] = []
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        borough = str(props.get("borough", "")).strip().lower()
        if borough != "manhattan":
            continue

        raw_id = props.get("locationid", props.get("LocationID"))
        if raw_id is None:
            continue
        try:
            ids.append(int(raw_id))
        except (TypeError, ValueError):
            continue

    if not ids:
        raise ValueError("No Manhattan location IDs found in taxi zones file.")
    return sorted(set(ids))


def load_service_daily_manhattan(
    csv_path: os.PathLike, manhattan_ids: Iterable[int]
) -> pd.DataFrame:
    """Load one service file and return daily Manhattan trip totals."""
    df = pd.read_csv(csv_path)
    date_col = _find_column(df, ["by_day_pickup_datetime", "pickup_datetime", "date"])
    pu_col = _find_column(df, ["PULocationID", "PUlocationID", "locationid"])
    trip_col = _find_column(df, ["trip_count", "ride_count", "count"])

    out = df[[date_col, pu_col, trip_col]].copy()
    out.columns = ["date", "location_id", "trip_count"]

    out["date"] = pd.to_datetime(
        out["date"], format="%Y %b %d %I:%M:%S %p", errors="coerce"
    )
    out["location_id"] = pd.to_numeric(out["location_id"], errors="coerce").astype("Int64")
    out["trip_count"] = (
        out["trip_count"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )

    out = out.dropna(subset=["date", "location_id", "trip_count"])
    out["date"] = out["date"].dt.normalize()
    out = out[out["location_id"].isin(set(manhattan_ids))]

    daily = out.groupby("date", as_index=False)["trip_count"].sum()
    return daily.sort_values("date")


def build_daily_manhattan_matrix(
    ridehail_dir: os.PathLike = DEFAULT_RIDEHAIL_DIR,
    taxi_zones_geojson_path: os.PathLike = DEFAULT_TAXI_ZONES_PATH,
) -> pd.DataFrame:
    """Build a date x service matrix with Manhattan-only daily totals."""
    manhattan_ids = load_manhattan_location_ids(taxi_zones_geojson_path)

    service_series = []
    for service, filename in SERVICE_FILES.items():
        csv_path = Path(ridehail_dir) / filename
        daily = load_service_daily_manhattan(csv_path, manhattan_ids)
        daily = daily.rename(columns={"trip_count": service})
        service_series.append(daily)

    merged = service_series[0]
    for daily in service_series[1:]:
        merged = merged.merge(daily, on="date", how="outer")

    merged = merged.sort_values("date").reset_index(drop=True)
    merged["date"] = pd.to_datetime(merged["date"])
    return merged


def benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values."""
    p_values = np.asarray(p_values, dtype=float)
    n = len(p_values)
    order = np.argsort(p_values)
    ranked = p_values[order]

    adjusted_ranked = np.empty(n, dtype=float)
    prev = 1.0
    for i in range(n - 1, -1, -1):
        rank = i + 1
        val = ranked[i] * n / rank
        prev = min(prev, val)
        adjusted_ranked[i] = prev

    adjusted = np.empty(n, dtype=float)
    adjusted[order] = np.clip(adjusted_ranked, 0, 1)
    return adjusted


def run_day_to_day_tests(daily_matrix: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Run statistical tests for synchronized daily movement across services."""
    value_cols = [c for c in daily_matrix.columns if c != "date"]
    daily_totals = daily_matrix.copy()

    # We keep only days where all services are observed for fair paired tests.
    complete = daily_totals.dropna(subset=value_cols).copy()
    if complete.empty:
        raise ValueError("No fully-overlapping dates across services.")

    # Use log day-over-day ratios as multiplicative daily change.
    # Example:
    # +20% -> log(1.20)=+0.182, -20% -> log(0.80)=-0.223.
    # These are not perfectly equal, but much closer to symmetric around 0
    # than raw percent changes (+0.20 vs -0.20 has asymmetric compounding).
    ratios = np.log(complete[value_cols] / complete[value_cols].shift(1))
    ratios = ratios.replace([np.inf, -np.inf], np.nan).dropna()
    if ratios.empty:
        raise ValueError("Unable to compute day-over-day log ratios.")

    # 1) Friedman repeated-measures test (rank-based, non-parametric).
    # Null hypothesis: across matched days, all services come from the same
    # distribution of day-over-day log changes.
    # "Repeated-measures" here means each day provides one observation per service.
    # "Rank-based" means values are compared by within-day rank, not raw magnitude.
    friedman = friedmanchisquare(*(ratios[c].values for c in value_cols))
    overall = pd.DataFrame(
        {
            "test": ["friedman_repeated_measures"],
            "n_days": [len(ratios)],
            "statistic": [friedman.statistic],
            "p_value": [friedman.pvalue],
        }
    )

    # 2) Pairwise paired t-tests on service differences per day.
    # Null hypothesis for each pair (A,B): mean(log_change_A - log_change_B) = 0.
    # Raw p-values are adjusted with BH-FDR because we run multiple pair tests.
    pair_rows: List[Dict[str, float]] = []
    for a, b in combinations(value_cols, 2):
        t_res = ttest_rel(ratios[a], ratios[b], nan_policy="omit")
        diff = ratios[a] - ratios[b]
        pair_rows.append(
            {
                "service_a": a,
                "service_b": b,
                "n_days": int(diff.notna().sum()),
                "mean_diff_log_ratio": float(diff.mean()),
                "t_statistic": float(t_res.statistic),
                "p_value": float(t_res.pvalue),
            }
        )
    pairwise = pd.DataFrame(pair_rows)
    pairwise["p_value_fdr_bh"] = benjamini_hochberg(pairwise["p_value"].to_numpy())

    # 3) Pairwise Pearson correlation of daily log-ratio movements.
    # Null hypothesis for each pair: correlation r = 0 (no linear co-movement).
    # Again, BH-FDR is applied across the multiple pairwise correlation tests.
    corr_rows: List[Dict[str, float]] = []
    for a, b in combinations(value_cols, 2):
        r, p = pearsonr(ratios[a], ratios[b])
        corr_rows.append(
            {
                "service_a": a,
                "service_b": b,
                "n_days": len(ratios),
                "pearson_r": float(r),
                "p_value": float(p),
            }
        )
    correlations = pd.DataFrame(corr_rows)
    correlations["p_value_fdr_bh"] = benjamini_hochberg(correlations["p_value"].to_numpy())

    summary_stats = ratios.describe().T.reset_index().rename(columns={"index": "service"})
    summary_stats = summary_stats[
        ["service", "count", "mean", "std", "min", "25%", "50%", "75%", "max"]
    ]

    ratios_with_date = ratios.copy()
    ratios_with_date.insert(0, "date", complete["date"].iloc[1:].values)

    return {
        "daily_totals": complete,
        "daily_log_ratios": ratios_with_date,
        "overall_test": overall,
        "pairwise_ttests": pairwise,
        "pairwise_correlations": correlations,
        "ratio_summary": summary_stats,
    }


def save_results(results: Dict[str, pd.DataFrame], output_dir: os.PathLike) -> None:
    """Save result tables to CSV files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    for name, df in results.items():
        df.to_csv(output_path / f"{name}.csv", index=False)


def print_interpretation(results: Dict[str, pd.DataFrame], alpha: float = 0.05) -> None:
    """Print a concise interpretation for EDA use."""
    overall = results["overall_test"].iloc[0]
    print("\nDay-to-day Manhattan ridership synchronization tests")
    print("===================================================")
    print(
        f"Friedman test (all four services): statistic={overall['statistic']:.3f}, "
        f"p={overall['p_value']:.4g}, n_days={int(overall['n_days'])}"
    )
    if overall["p_value"] < alpha:
        print("Interpretation: daily proportional changes differ across at least one service.")
    else:
        print("Interpretation: no strong evidence that daily proportional changes differ.")

    ttests = results["pairwise_ttests"].sort_values("p_value_fdr_bh")
    print("\nMost similar pair(s) by paired-change test (largest adjusted p-value):")
    for _, row in ttests.sort_values("p_value_fdr_bh", ascending=False).head(3).iterrows():
        print(
            f"- {row['service_a']} vs {row['service_b']}: "
            f"mean_diff={row['mean_diff_log_ratio']:.5f}, "
            f"adj_p={row['p_value_fdr_bh']:.4g}"
        )

    cors = results["pairwise_correlations"].sort_values("pearson_r", ascending=False)
    print("\nTop correlated pair(s) in day-over-day movement:")
    for _, row in cors.head(3).iterrows():
        print(
            f"- {row['service_a']} vs {row['service_b']}: "
            f"r={row['pearson_r']:.3f}, adj_p={row['p_value_fdr_bh']:.4g}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Manhattan ride-hailing day-to-day synchronization statistical tests."
    )
    parser.add_argument(
        "--ridehail-dir",
        default=str(DEFAULT_RIDEHAIL_DIR),
        help="Directory containing cleaned TLC ride-hailing CSV files.",
    )
    parser.add_argument(
        "--taxi-zones-geojson",
        default=str(DEFAULT_TAXI_ZONES_PATH),
        help="Path to NYC taxi zones geojson (for Manhattan filtering).",
    )
    parser.add_argument(
        "--output-dir",
        default="results/ridehail_day_to_day_tests",
        help="Directory to write output CSV tables.",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level for interpretation.",
    )
    args = parser.parse_args()

    daily = build_daily_manhattan_matrix(
        ridehail_dir=args.ridehail_dir,
        taxi_zones_geojson_path=args.taxi_zones_geojson,
    )
    results = run_day_to_day_tests(daily)
    save_results(results, args.output_dir)
    print_interpretation(results, alpha=args.alpha)
    print(f"\nSaved output tables to: {args.output_dir}")


if __name__ == "__main__":
    main()
