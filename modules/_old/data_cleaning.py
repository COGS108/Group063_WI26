import pandas as pd

def clean_FHV_data(filename):
    hvfhv_df = pd.read_csv(filename)
    hvfhv_df['total_cost'] = hvfhv_df['base_passenger_fare'] + hvfhv_df['congestion_surcharge'] + hvfhv_df['airport_fee'] + hvfhv_df['tips'] + hvfhv_df['tolls'] + hvfhv_df['sales_tax']
    df_new = hvfhv_df.drop(columns=['base_passenger_fare', 'congestion_surcharge', 'airport_fee', 'tips', 'tolls', 'sales_tax'])
    df_new = df_new.drop(columns= ['dropoff_datetime', 'DOLocationID', 'driver_pay', 'hvfhs_license_num'])
    return df_new

def clean_MTS_data(filename):
    mts_df = pd.read_csv(filename)
    mts_df = mts_df.drop(columns=['latitude', 'longitude'])

def clean_subway_stations(filename):
    stations_df = pd.read_csv(filename)
    cleaned_df = stations_df.drop(columns=['Complex ID', 'Division', 'CBD',
                                        'Daytime Routes', 'Structure',
                                        'North Direction Label', 'South Direction Label',
                                        'ADA', 'ADA Northbound', 'ADA Southbound', 'ADA Notes',
                                        'Georeference'])
    return cleaned_df

def load_and_shorten_data(file_path, n_rows):
    """
    Load a CSV file and return only the first n rows.
    
    Parameters:
    - file_path: str, path to the CSV file
    - n_rows: int, number of rows to return
    
    Returns:
    - DataFrame containing the first n rows of the CSV file
    """
    try:
        df = pd.read_csv(file_path)
        return df.head(n_rows)
    except Exception as e:
        print(f"Error loading data from {file_path}: {e}")
        return None
    
stations_path = "data/00-raw/MTA_Subway_Stations.csv"
cleaned_df = clean_subway_stations(stations_path)
print(cleaned_df.head())
print(cleaned_df.columns)
cleaned_df.to_csv("data/02-processed/map_files/MTA_Subway_Stations_cleaned.csv", index=False)

shortened_df =load_and_shorten_data("data/00-raw/2023_High_Volume_FHV_Trip_Data_20260218.csv", 10000)
shortened_df.to_csv("data/01-interim/2023_HVFHV_Trip_Data_shortened_raw.csv", index=False)