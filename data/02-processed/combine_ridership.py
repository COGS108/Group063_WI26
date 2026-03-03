import pandas as pd
import os

# File paths
files = [
    'data/01-interim/TLC_ridehail/2023_For_Hire_Vehicles_Trip_Data_cleaned.csv',
    'data/01-interim/TLC_ridehail/2023_Green_Taxi_Trip_Data_cleaned.csv',
    'data/01-interim/TLC_ridehail/2023_High_Volume_FHV_Trip_Data_cleaned.csv',
    'data/01-interim/TLC_ridehail/2023_Yellow_Taxi_Trip_Data_cleaned.csv'
]

# Load and combine
dfs = []
for f in files:
    if os.path.exists(f):
        dfs.append(pd.read_csv(f))

if not dfs:
    print("No files found")
    exit()

# Combine and aggregate
combined = pd.concat(dfs, ignore_index=True)
result = combined.groupby(['by_day_pickup_datetime', 'PUlocationID'])['trip_count'].sum().reset_index()

# Convert PUlocationID to string without decimals
result['PUlocationID'] = result['PUlocationID'].astype(int).astype(str)

# Save
result.to_csv('data/02-processed/total_ridership.csv', index=False)
print(f"Saved {len(result)} rows")