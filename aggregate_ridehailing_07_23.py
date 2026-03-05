from pathlib import Path

import pandas as pd


RAW_DIR = Path("data/00-raw")
OUT_DIR = Path("data/01-interim/TLC_ridehail")

FILES = {
    "fhv": {
        "file": "fhv_tripdata_2023-07.parquet",
        "pickup_col": "pickup_datetime",
        "location_col": "PUlocationID",
    },
    "hvfhv": {
        "file": "fhvhv_tripdata_2023-07.parquet",
        "pickup_col": "pickup_datetime",
        "location_col": "PULocationID",
    },
    "green_taxi": {
        "file": "green_tripdata_2023-07.parquet",
        "pickup_col": "lpep_pickup_datetime",
        "location_col": "PULocationID",
    },
    "yellow_taxi": {
        "file": "yellow_tripdata_2023-07.parquet",
        "pickup_col": "tpep_pickup_datetime",
        "location_col": "PULocationID",
    },
}


def hourly_trip_counts(parquet_path: Path, pickup_col: str, location_col: str) -> pd.DataFrame:
    df = pd.read_parquet(parquet_path, columns=[pickup_col, location_col])
    df = df.rename(columns={pickup_col: "pickup_datetime", location_col: "pickup_location"})

    df["pickup_datetime"] = pd.to_datetime(df["pickup_datetime"], errors="coerce")
    df["pickup_hour"] = df["pickup_datetime"].dt.floor("h")

    df = df.dropna(subset=["pickup_hour", "pickup_location"])
    df = df[df["pickup_hour"] >= pd.Timestamp("2023-07-01 00:00:00")]
    df = df[df["pickup_hour"].dt.year == 2023]
    df["pickup_location"] = pd.to_numeric(df["pickup_location"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["pickup_location"])

    out = (
        df.groupby(["pickup_hour", "pickup_location"], as_index=False)
        .size()
        .rename(columns={"size": "trip_count"})
    )
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_services = []

    for service, cfg in FILES.items():
        parquet_path = RAW_DIR / cfg["file"]
        out_df = hourly_trip_counts(parquet_path, cfg["pickup_col"], cfg["location_col"])
        all_services.append(out_df)

        out_path = OUT_DIR / f"2023_{service}_hourly_trip_counts.csv"
        out_df.to_csv(out_path, index=False)
        print(f"Saved {len(out_df):,} rows -> {out_path}")

    total_df = (
        pd.concat(all_services, ignore_index=True)
        .groupby(["pickup_hour", "pickup_location"], as_index=False)["trip_count"]
        .sum()
    )
    total_path = OUT_DIR / "2023_all_ridehail_hourly_trip_counts.csv"
    total_df.to_csv(total_path, index=False)
    print(f"Saved {len(total_df):,} rows -> {total_path}")


if __name__ == "__main__":
    main()
