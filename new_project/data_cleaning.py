import pandas as pd

hvfhv_df = pd.read_csv("data/2023_High_Volume_FHV_Trip_Data_20260218.csv")
print("data loaded successfully")
#print(hvfhv_df.columns)

hvfhv_df['total_cost'] = hvfhv_df['base_passenger_fare'] + hvfhv_df['congestion_surcharge'] + hvfhv_df['airport_fee'] + hvfhv_df['tips'] + hvfhv_df['tolls'] + hvfhv_df['sales_tax']
#drop charges columns
df_new = hvfhv_df.drop(columns=['base_passenger_fare', 'congestion_surcharge', 'airport_fee', 'tips', 'tolls', 'sales_tax'])
#drop the unnecessary columns
df_new = df_new.drop(columns= ['dropoff_datetime', 'DOLocationID', 'driver_pay', 'hvfhs_license_num'])

#print(df_new.isna().sum())
##create new csv
#df_new.to_csv("data/2023_High_Volume_FHV_Trip_Data_20260218_cleaned.csv", index=False)
print(df_new.columns)
print(df_new.head())
print("data cleaned and saved successfully")