import pandas as pd
import openpyxl

file_path = "training dataset.xlsx"
df = pd.read_excel(file_path, header=None, nrows=10)
for idx, row in df.iterrows():
    print(f"Row {idx}: {list(row[:6])} ... {list(row[-4:])}")
