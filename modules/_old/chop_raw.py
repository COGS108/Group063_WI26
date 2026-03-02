import pandas as pd

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
    
shortened_df =load_and_shorten_data("data/00-raw/2023_High_Volume_FHV_Trip_Data_20260218.csv", 10000)

shortened_df.to_csv("data/01-interim/2023_HVFHV_Trip_Data_shortened_raw.csv", index=False)