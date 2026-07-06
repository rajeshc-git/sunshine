import os
import sys
import pandas as pd
import numpy as np
import json

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def analyze():
    csv_path = "data/training_data_full.csv"
    meta_path = "data/training_metadata.json" if os.path.exists("data/training_metadata.json") else "data/metadata.json"
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return
        
    print(f"Loading complete dataset from {csv_path}...")
    # Load raw CSV as string types to preserve original format
    data_df = pd.read_csv(csv_path, dtype=str, keep_default_na=False, low_memory=False)
    print(f"Loaded dataset shape: {data_df.shape}")
    
    print("Parsing Timestamp...")
    data_df["Timestamp"] = pd.to_datetime(data_df["Timestamp"], errors="coerce")
    data_df = data_df.dropna(subset=["Timestamp"])
    data_df = data_df.set_index("Timestamp")
    
    # Convert all telemetry columns to numeric
    telemetry_cols = [c for c in data_df.columns if c != "Production Grade"]
    print("Converting telemetry variables to numeric...")
    for col in telemetry_cols:
        data_df[col] = pd.to_numeric(
            data_df[col].astype(str).str.replace(',', '').str.strip(),
            errors='coerce'
        )
        
    # Analyze nulls
    null_counts = data_df[telemetry_cols].isnull().sum()
    print("\nNull/Bad Input count per column:")
    for col, null_c in null_counts.items():
        if null_c > 0:
            print(f"  {col}: {null_c} ({null_c/len(data_df)*100:.2f}%)")
            
    # Interpolate missing values
    print("Interpolating missing values...")
    data_df[telemetry_cols] = data_df[telemetry_cols].ffill().bfill()
    
    # Detect plant shutdowns based on Plant Load < 5000 (Normal is 30,000 - 60,000)
    if "Plant Load" in data_df.columns:
        print("\nAnalyzing plant load and shutdowns...")
        shutdowns = data_df[data_df["Plant Load"] < 5000]
        print(f"Total minutes with low Plant Load: {len(shutdowns)} mins")
        
        shutdown_times = shutdowns.index
        if len(shutdown_times) > 0:
            intervals = []
            start_time = shutdown_times[0]
            prev_time = shutdown_times[0]
            
            for t in shutdown_times[1:]:
                # If gap between low load times is > 15 minutes, start a new shutdown event
                if (t - prev_time).total_seconds() > 900:
                    intervals.append((start_time, prev_time))
                    start_time = t
                prev_time = t
            intervals.append((start_time, prev_time))
            
            print(f"Detected {len(intervals)} distinct shutdown/low-load events:")
            shutdown_summary = []
            for idx, (start, end) in enumerate(intervals):
                duration = (end - start).total_seconds() / 3600
                print(f"  Event {idx+1}: {start} to {end} (Duration: {duration:.2f} hours)")
                shutdown_summary.append({
                    "event_id": idx+1,
                    "start": str(start),
                    "end": str(end),
                    "duration_hours": round(duration, 2)
                })
                
            with open("data/shutdown_events.json", "w") as f:
                json.dump(shutdown_summary, f, indent=4)
            print("Saved data/shutdown_events.json")
            
    # Save the full preprocessed/cleaned telemetry dataset (User requested full dataset)
    print("Saving full cleaned telemetry to data/training_data_full.csv...")
    data_df.to_csv("data/training_data_full.csv")
    print("Saved data/training_data_full.csv (full year dataset)")
    
    # Save summary statistical description
    stats = {}
    for col in telemetry_cols:
        col_stats = data_df[col].describe()
        stats[col] = {
            "mean": float(col_stats["mean"]),
            "std": float(col_stats["std"]),
            "min": float(col_stats["min"]),
            "max": float(col_stats["max"]),
            "q25": float(col_stats["25%"]),
            "q50": float(col_stats["50%"]),
            "q75": float(col_stats["75%"])
        }
    with open("data/column_stats.json", "w") as f:
        json.dump(stats, f, indent=4)
    print("Saved data/column_stats.json")

if __name__ == "__main__":
    analyze()
