import os
import sys

# Reconfigure stdout to handle UTF-8/Unicode characters in the console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def check_dependencies():
    packages = []
    try:
        import pandas as pd
    except ImportError:
        packages.append("pandas")
    try:
        import openpyxl
    except ImportError:
        packages.append("openpyxl")
    
    if packages:
        print(f"Missing packages: {', '.join(packages)}")
        print("Please install them using: pip install " + " ".join(packages))
        return False
    return True

def inspect():
    if not check_dependencies():
        return
        
    import pandas as pd
    import openpyxl
    
    file_path = "training dataset.xlsx"
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return
        
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"File: {file_path}")
    print(f"File size: {size_mb:.2f} MB")
    
    sheet_names = []
    print("Loading workbook structure (read-only)...")
    try:
        wb = openpyxl.load_workbook(file_path, read_only=True)
        sheet_names = wb.sheetnames
        # Safe print sheet names using ascii/repr to avoid encoding errors on windows cmd
        safe_names = [name.encode('ascii', errors='replace').decode('ascii') for name in sheet_names]
        print(f"Sheet names found: {safe_names}")
        wb.close()
    except Exception as e:
        print(f"Error loading sheet names via openpyxl: {e}")
        
    if not sheet_names:
        # Fallback: let pandas read all sheets structure
        print("Falling back to pandas to list sheets...")
        try:
            xl = pd.ExcelFile(file_path)
            sheet_names = xl.sheet_names
            safe_names = [name.encode('ascii', errors='replace').decode('ascii') for name in sheet_names]
            print(f"Sheet names found via pandas: {safe_names}")
        except Exception as e:
            print(f"Error listing sheet names via pandas: {e}")
            sheet_names = [0]
            
    for sheet in sheet_names:
        sheet_repr = repr(sheet)
        print(f"\n================ Inspecting Sheet: {sheet_repr} ================")
        try:
            # Read header and first 5 rows
            df = pd.read_excel(file_path, sheet_name=sheet, nrows=5)
            if isinstance(df, dict):
                # This shouldn't happen unless sheet is None, but let's handle it
                print(f"Read returned a dict. Keys: {list(df.keys())}")
                if df:
                    first_key = list(df.keys())[0]
                    df = df[first_key]
            
            print(f"Shape: {df.shape[0]}+ rows, {df.shape[1]} columns")
            print("Columns:")
            safe_cols = [str(c).encode('ascii', errors='replace').decode('ascii') for c in df.columns]
            print(safe_cols)
            print("\nFirst 5 rows:")
            # Display first 5 rows with safe encoding
            df_str = df.to_string(index=False)
            safe_df_str = df_str.encode('ascii', errors='replace').decode('ascii')
            print(safe_df_str)
        except Exception as e:
            print(f"Error reading sheet {sheet_repr}: {e}")

if __name__ == "__main__":
    inspect()
