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
        df = pd.read_csv(f)
        # Convert date
        df['date'] = pd.to_datetime(df['by_day_pickup_datetime'], format='%Y %b %d %I:%M:%S %p').dt.date
        
        # Convert trip_count to numeric (handles strings with commas)
        df['trip_count'] = pd.to_numeric(df['trip_count'].astype(str).str.replace(',', ''), errors='coerce')
        
        dfs.append(df)
        print(df.head())

if not dfs:
    print("No files found")
    exit()

# Combine all data first
combined = pd.concat(dfs, ignore_index=True)

# Now drop the old column and aggregate
combined = combined.drop('by_day_pickup_datetime', axis=1)
result = combined.groupby(['date', 'PULocationID'])['trip_count'].sum().reset_index()

# Convert PULocationID to string without decimals
result['PULocationID'] = result['PULocationID'].astype(int).astype(str)

# Save
result.to_csv('data/02-processed/total_ridership.csv', index=False)
print(f"Saved {len(result)} rows")
print(f"Total trips: {result['trip_count'].sum():,}")

# Quick check
print(f"\nData types after conversion:")
print(result.dtypes)
print(f"\nFirst few rows:")
print(result.head())