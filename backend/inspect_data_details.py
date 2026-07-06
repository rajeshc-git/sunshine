import os
import sys
import pandas as pd

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def inspect_details():
    file_path = "training dataset.xlsx"
    print("Reading dataset starting from row 4 as header...")
    try:
        # read_excel with header=4 makes row 4 (0-indexed) the column names
        df = pd.read_excel(file_path, sheet_name=0, header=4, nrows=20)
        print("Data loaded successfully (first 20 rows of data):")
        print(f"Number of columns: {len(df.columns)}")
        print("\nColumns:")
        for idx, col in enumerate(df.columns):
            safe_col = str(col).encode('ascii', errors='replace').decode('ascii')
            print(f"  {idx}: {safe_col}")
            
        print("\nFirst 10 rows of data:")
        df_str = df.head(10).to_string(index=False)
        safe_df_str = df_str.encode('ascii', errors='replace').decode('ascii')
        print(safe_df_str)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_details()
