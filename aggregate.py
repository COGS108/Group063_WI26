import pandas as pd

# Load the data
df = pd.read_csv('data/02-processed/total_ridership.csv')

# Group by date and sum all trip_counts
daily_total = df.groupby('date')['trip_count'].sum().reset_index()

# Rename column for clarity
daily_total = daily_total.rename(columns={'trip_count': 'total_daily_trips'})

# Sort by date
daily_total = daily_total.sort_values('date')

# Save to new CSV
daily_total.to_csv('data/02-processed/daily_total_ridership.csv', index=False)

# Show results
print("📊 Daily Total Ridership Across All Zones:")
print(daily_total.head(10))
print(f"\n✅ Saved {len(daily_total)} days of data")
print(f"📈 Total trips across all days: {daily_total['total_daily_trips'].sum():,}")