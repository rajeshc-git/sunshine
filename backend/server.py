import os
import sys
import json
import threading
import time
import pandas as pd
import numpy as np
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Reconfigure stdout for UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

app = FastAPI(title="Sunshine RCA Enterprise API", version="1.0.0")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Variables to store loaded dataset and model states
data_df = None
metadata = {}
shutdown_events = []
column_stats = {}
causal_graph = {}
causal_effects = {}
model_weights = {}

# Retraining Status Tracker
training_state = {
    "status": "idle",  # "idle", "running", "completed", "failed"
    "epoch": 0,
    "total_epochs": 50,
    "loss": 0.0,
    "accuracy": 0.0,
    "logs": []
}

def load_system_data():
    global data_df, metadata, shutdown_events, column_stats, causal_graph, causal_effects, model_weights
    print("Initializing Enterprise RCA Engine...")
    
    # Load metadata
    if os.path.exists("data/metadata.json"):
        with open("data/metadata.json", "r") as f:
            metadata = json.load(f)
            
    # Load shutdown events
    if os.path.exists("data/shutdown_events.json"):
        with open("data/shutdown_events.json", "r") as f:
            shutdown_events = json.load(f)
            
    # Load column stats
    if os.path.exists("data/column_stats.json"):
        with open("data/column_stats.json", "r") as f:
            column_stats = json.load(f)
            
    # Load causal graph
    if os.path.exists("data/causal_graph.json"):
        with open("data/causal_graph.json", "r") as f:
            causal_graph = json.load(f)
            
    # Load causal effects
    if os.path.exists("data/causal_effects.json"):
        with open("data/causal_effects.json", "r") as f:
            causal_effects = json.load(f)
            
    # Load model weights
    if os.path.exists("data/model_weights.json"):
        with open("data/model_weights.json", "r") as f:
            model_weights = json.load(f)
            
    # Load telemetry database
    full_csv = "data/training_data_full.csv"
    if os.path.exists(full_csv):
        print(f"Loading pre-cleaned telemetry dataset from {full_csv}...")
        data_df = pd.read_csv(full_csv, index_col="Timestamp", parse_dates=True)
        print("Telemetry data loaded successfully.")
    else:
        print(f"Warning: {full_csv} not found.")
# Load data on startup
load_system_data()


# ----------------- API Endpoints -----------------

@app.get("/api/status")
def get_status():
    return {
        "status": "online",
        "dataset_loaded": data_df is not None,
        "total_records": len(data_df) if data_df is not None else 0,
        "active_shutdowns": len(shutdown_events)
    }

@app.get("/api/metadata")
def get_metadata():
    return metadata

@app.get("/api/events")
def get_events():
    return shutdown_events

@app.get("/api/column_stats")
def get_stats():
    return column_stats

@app.get("/api/causal_graph")
def get_graph():
    return causal_graph

@app.get("/api/causal_effects")
def get_effects():
    return causal_effects

@app.get("/api/model_weights")
def get_weights():
    return model_weights

@app.get("/api/telemetry")
def get_telemetry(event_id: int):
    # Retrieve the shutdown event info
    evt = next((e for e in shutdown_events if e["event_id"] == event_id), None)
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
        
    start_time = pd.to_datetime(evt["start"])
    # We slice out a 120-minute window around the event start
    # Let's say: 40 minutes before, 80 minutes after
    window_start = start_time - pd.Timedelta(minutes=40)
    window_end = window_start + pd.Timedelta(minutes=120)
    
    # Try slicing from the real telemetry dataset loaded in memory
    if data_df is not None:
        try:
            sliced_df = data_df.loc[window_start:window_end]
            if len(sliced_df) > 0:
                df_reset = sliced_df.reset_index()
                df_reset["Timestamp"] = df_reset["Timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
                # Drop non-sensor columns if present
                if "Production Grade" in df_reset.columns:
                    df_reset = df_reset.drop(columns=["Production Grade"])
                # Round numeric columns to 2 decimal places for JSON serialization
                for col in df_reset.columns:
                    if col != "Timestamp":
                        df_reset[col] = df_reset[col].round(2)
                return df_reset.to_dict(orient="records")
        except Exception as e:
            print(f"Error slicing real telemetry data: {e}")
            
    # Fallback to simulated data if real data is not loaded or slice is empty
    try:
        data_slice = generate_simulated_slice(evt, event_id)
        return data_slice
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def generate_simulated_slice(evt, event_id):
    # Mapping events to physical failures
    event_faults = {
        1: {"type": "nitrogen", "root": "Hot N2 Flow"},
        2: {"type": "nitrogen", "root": "Hot N2 Flow"},
        3: {"type": "nitrogen", "root": "Hot N2 Flow"},
        4: {"type": "blower", "root": "FBD Blower  B-4601 Current (A)"},
        5: {"type": "decanter", "root": "Decanter A Current (A)"},
        6: {"type": "decanter", "root": "Decanter B Current (A)"},
        7: {"type": "decanter", "root": "Decanter C Current (A)"},
        8: {"type": "decanter", "root": "Decanter A Current (A)"},
        9: {"type": "decanter", "root": "Decanter D Current (A)"},
        10: {"type": "scrubber", "root": "C-4601 Diff. Pressure"},
        11: {"type": "scrubber", "root": "C-4601 Diff. Pressure"},
        12: {"type": "scrubber", "root": "C-4601 Diff. Pressure"},
        13: {"type": "scrubber", "root": "C-4601 Diff. Pressure"},
        14: {"type": "blower", "root": "FBD Blower  B-4602 Current (A)"},
        15: {"type": "blower", "root": "FBD Blower  B-4601 Current (A)"},
        16: {"type": "nitrogen", "root": "Hot N2 Flow"},
        17: {"type": "scrubber", "root": "C-4601 Diff. Pressure"},
        18: {"type": "decanter", "root": "Decanter B Current (A)"},
        19: {"type": "blower", "root": "FBD Blower  B-4601 Current (A)"}
    }
    
    fault_info = event_faults.get(event_id, {"type": "normal", "root": ""})
    fault_type = fault_info["type"]
    root_cause = fault_info["root"]
    
    duration_mins = 120
    shutdown_start = 40
    shutdown_dur = Math_round(evt["duration_hours"] * 60)
    
    base_time = pd.to_datetime(evt["start"]) - pd.Timedelta(minutes=shutdown_start)
    
    columns = [c for c in metadata.keys() if c != "Production Grade"]
    
    data_list = []
    for m in range(duration_mins):
        t_val = base_time + pd.Timedelta(minutes=m)
        row = {"Timestamp": str(t_val)}
        
        is_failing = m >= shutdown_start and m < (shutdown_start + shutdown_dur)
        is_recovering = m >= (shutdown_start + shutdown_dur)
        
        for col in columns:
            stats = column_stats.get(col, {"mean": 50, "std": 5, "min": 0, "max": 100})
            mean_val = stats["mean"]
            std_val = stats["std"]
            
            # Parse limits
            limit_low = stats["min"]
            limit_high = stats["max"]
            r_str = metadata[col]["range"]
            if "-" in r_str and r_str != "-":
                try:
                    parts = r_str.split("-")
                    limit_low = float(parts[0].replace(",", ""))
                    limit_high = float(parts[1].replace(",", ""))
                except:
                    pass
            
            val = mean_val + (np.sin(m/5) * 0.2 * std_val) + (np.random.rand() - 0.5) * 0.1 * std_val
            
            if fault_type == "nitrogen":
                if col == "Hot N2 Flow":
                    if is_failing:
                        val = limit_low - (std_val * 5) - (np.random.rand() * std_val)
                elif "FBD Bed Temperature" in col or "Hot N2 Temperature" in col:
                    if is_failing:
                        delay = 2 if "3rd Panel" in col else 5 if "7th Panel" in col else 10
                        if m >= shutdown_start + delay:
                            val = limit_low - (std_val * 4) * ((m - shutdown_start - delay)/30 + 0.1)
                elif "Off Gas Temperature" in col:
                    if is_failing and m >= shutdown_start + 12:
                        val = limit_low - (std_val * 3)
                elif col == "Plant Load":
                    if is_failing and m >= shutdown_start + 15:
                        val = 0.0
                        
            elif fault_type == "blower":
                if col == root_cause:
                    if is_failing:
                        val = limit_high + (std_val * 6) + (np.random.rand() * std_val)
                elif col in ["1st stage  Bed Level", "2nd stage  Bed Level"]:
                    if is_failing and m >= shutdown_start + 4:
                        val = limit_low - (std_val * 4)
                elif col == "L-1 Conveying Pressure":
                    if is_failing and m >= shutdown_start + 2:
                        val = limit_high + (std_val * 5)
                elif col == "Plant Load":
                    if is_failing and m >= shutdown_start + 8:
                        val = 0.0
                        
            elif fault_type == "decanter":
                if col == root_cause:
                    if is_failing:
                        val = limit_high + (std_val * 5)
                elif col == "V-4607 Level":
                    if is_failing and m >= shutdown_start + 5:
                        val = limit_high + (std_val * 4)
                elif col == "V-4607 Pressure":
                    if is_failing and m >= shutdown_start + 8:
                        val = limit_high + (std_val * 3)
                elif col == "Plant Load":
                    if is_failing and m >= shutdown_start + 12:
                        val = 0.0
                        
            elif fault_type == "scrubber":
                if col == "C-4601 Diff. Pressure":
                    if is_failing:
                        val = limit_high + (std_val * 5)
                elif col == "C-4601 Top Temperature":
                    if is_failing and m >= shutdown_start + 4:
                        val = limit_high + (std_val * 3)
                elif col == "P-4614A/B Recovered Flow":
                    if is_failing and m >= shutdown_start + 6:
                        val = limit_low - (std_val * 5)
                elif col == "Plant Load":
                    if is_failing and m >= shutdown_start + 10:
                        val = 0.0
            
            if is_recovering:
                if col == "Plant Load":
                    val = mean_val * 0.2
                else:
                    val = (val + mean_val) / 2
                    
            val = max(stats["min"] * 0.5, min(stats["max"] * 1.5, val))
            row[col] = round(val, 2)
            
        data_list.append(row)
    return data_list

def Math_round(val):
    return int(val + 0.5) if val >= 0 else int(val - 0.5)

# -----------------Retraining Thread Logic -----------------

# Path for the cached training CSV (created once from xlsx, reused forever)
TRAINING_CSV_CACHE = "training_data_cache.csv"
XLSX_PATH          = "training dataset.xlsx"

def convert_xlsx_to_csv_cache(log_fn):
    """
    One-time conversion of the 198 MB xlsx to a flat CSV cache.
    Uses openpyxl read-only / write-only streaming so the full workbook
    is NEVER loaded into RAM at once.

    The CSV will have:
      - Row 0 : column names  (parsed from xlsx row 5, 0-indexed)
      - Row 1+: data rows     (from xlsx row 9 onwards)
    Normal-range metadata (rows 6-8) is saved separately to metadata.json
    if that file does not already exist.
    """
    import openpyxl

    log_fn(f"Opening '{XLSX_PATH}' in streaming read-only mode (198 MB — patience)...")
    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True, data_only=True)
    ws = wb.active
    log_fn(f"Workbook opened. Streaming rows...")

    # We need rows 5-8 for headers/metadata and row 9+ for data.
    # openpyxl streaming iterates row by row — we buffer the first ~10 rows.
    header_rows = {}   # 0-indexed row number -> list of cell values
    row_idx     = 0
    rows_written = 0

    import csv, io
    out_buf = open(TRAINING_CSV_CACHE, "w", newline="", encoding="utf-8")
    writer  = None   # csv.writer, created after we know the columns

    column_names = None
    sensor_ranges_from_xlsx = {}  # {col_name: (lo, hi)}

    for row in ws.iter_rows(values_only=True):
        if row_idx < 5:
            header_rows[row_idx] = list(row)
            row_idx += 1
            continue

        if row_idx == 5:
            # Column names row
            raw_cols = list(row)
            column_names = []
            for i, c in enumerate(raw_cols):
                if c is None or str(c).strip() == "":
                    column_names.append(f"Col_{i}")
                else:
                    column_names.append(str(c).replace('\n', ' ').strip())
            column_names[1] = "Timestamp"
            header_rows[5] = raw_cols
            row_idx += 1
            continue

        if row_idx == 6:
            header_rows[6] = list(row)   # units
            row_idx += 1
            continue

        if row_idx == 7:
            # Normal operating ranges row — parse now
            raw_ranges = list(row)
            for i in range(2, len(column_names)):
                col = column_names[i]
                r_val = raw_ranges[i]
                r_str = str(r_val).replace('\n', ' ').strip() if r_val is not None else ""
                if "-" in r_str and r_str != "-":
                    try:
                        parts = r_str.split("-")
                        lo = float(parts[0].replace(",", "").strip())
                        hi = float(parts[1].replace(",", "").strip())
                        sensor_ranges_from_xlsx[col] = (lo, hi)
                    except Exception:
                        pass
            header_rows[7] = raw_ranges
            row_idx += 1
            continue

        if row_idx == 8:
            header_rows[8] = list(row)   # DCS tags
            row_idx += 1
            continue

        # row_idx >= 9 : actual data rows
        if writer is None:
            # Write CSV header — skip Col_0 (blank placeholder), keep rest
            csv_cols = [c for c in column_names if c != "Col_0"]
            writer = csv.writer(out_buf)
            writer.writerow(csv_cols)

        row_vals = list(row)
        # Align row_vals to column_names length (pad if shorter)
        while len(row_vals) < len(column_names):
            row_vals.append(None)

        # Build dict keyed by column name, skip Col_0
        row_dict = {column_names[i]: row_vals[i] for i in range(len(column_names))}
        csv_row  = [row_dict.get(c, "") for c in csv_cols]
        writer.writerow(csv_row)
        rows_written += 1

        if rows_written % 50000 == 0:
            log_fn(f"  Streamed {rows_written:,} data rows so far...")

        row_idx += 1

    out_buf.close()
    wb.close()
    log_fn(f"Conversion complete: {rows_written:,} rows written to '{TRAINING_CSV_CACHE}'.")
    return sensor_ranges_from_xlsx, column_names


def background_training_task():
    """
    Real MLP training pipeline on the full 198 MB training dataset.

    Data strategy
    -------------
    • First run  : xlsx is converted to a flat CSV cache via openpyxl
                   streaming (never loads the whole workbook into RAM).
    • Later runs : CSV cache is loaded directly with pandas — ~10x faster.

    Training pipeline
    -----------------
    1. Load / convert dataset
    2. Parse normal operating ranges (from xlsx header or metadata.json)
    3. Build binary symptom vector per row (1 = out-of-range, 0 = normal)
    4. Auto-label rows from real sensor deviations + Plant Load < 5000
    5. 80/20 chronological train/val split
    6. 3-layer MLP (He init) : input → 64 ReLU → 32 ReLU → 5 Softmax
    7. Mini-batch SGD, cross-entropy, 50 epochs
    8. Save weights from the best validation-accuracy epoch
    """
    global training_state, model_weights

    training_state["status"] = "running"
    training_state["epoch"] = 0
    training_state["loss"] = 0.0
    training_state["accuracy"] = 0.0
    training_state["logs"] = []

    def log(msg):
        print(msg)
        training_state["logs"].append(f"[{time.strftime('%H:%M:%S')}] {msg}")

    try:
        # ------------------------------------------------------------------
        # STEP 1 — Load dataset
        #   Priority: training_data_full.csv (fast, ~seconds)
        #             falling back to training dataset.xlsx (slow, ~60-120 s)
        #   The CSV is produced once by running: python convert_to_csv.py
        # ------------------------------------------------------------------
        CSV_PATH  = "data/training_data_full.csv"
        XLSX_PATH = "data/training dataset.xlsx"

        if os.path.exists(CSV_PATH):
            log(f"CSV cache found — loading '{CSV_PATH}' (much faster than xlsx)...")
            # Values kept as mixed types; we convert sensor cols to numeric below
            data_df_raw = pd.read_csv(
                CSV_PATH,
                dtype=str,           # read all as str first, same as convert_to_csv.py
                keep_default_na=False,
                low_memory=False,
            )
            log(f"CSV loaded: {len(data_df_raw):,} rows × {len(data_df_raw.columns)} columns.")
        elif os.path.exists(XLSX_PATH):
            log(f"No CSV cache found — loading '{XLSX_PATH}' directly (may take 60-120 s)...")
            log("TIP: run  python convert_to_csv.py  once to create a fast CSV cache.")
            raw_df = pd.read_excel(
                XLSX_PATH,
                sheet_name=0,
                header=None,
                keep_default_na=False,
                dtype=str,
            )
            log(f"xlsx loaded: {raw_df.shape[0]} rows × {raw_df.shape[1]} columns.")

            # Parse header rows
            raw_cols   = list(raw_df.iloc[5])
            raw_ranges = list(raw_df.iloc[7])

            column_names = []
            for idx, c in enumerate(raw_cols):
                val = str(c).strip()
                if val == "" or val.lower() == "nan":
                    column_names.append(f"Col_{idx}")
                else:
                    column_names.append(val.replace("\n", " ").strip())
            column_names[1] = "Timestamp"

            data_df_raw = raw_df.iloc[9:].copy()
            data_df_raw.columns = column_names
            data_df_raw = data_df_raw.drop(columns=["Col_0"], errors="ignore")
            data_df_raw = data_df_raw.reset_index(drop=True)
            log(f"Data rows extracted: {len(data_df_raw):,}")
        else:
            raise FileNotFoundError(
                "Neither 'training_data_full.csv' nor 'training dataset.xlsx' found. "
                "Run convert_to_csv.py first."
            )

        # ------------------------------------------------------------------
        # STEP 2 — Load normal operating ranges from training_metadata.json
        #          (written by convert_to_csv.py) or fall back to metadata.json
        # ------------------------------------------------------------------
        meta_path = "data/training_metadata.json" if os.path.exists("data/training_metadata.json") else "data/metadata.json"
        with open(meta_path, "r", encoding="utf-8") as f:
            meta_dict = json.load(f)

        sensor_ranges = {}  # {col_name: (lo, hi)}
        for col_name, info in meta_dict.items():
            r_str = str(info.get("range", "")).strip()
            if "-" in r_str and r_str != "-":
                try:
                    parts = r_str.split("-")
                    lo = float(parts[0].replace(",", "").strip())
                    hi = float(parts[1].replace(",", "").strip())
                    sensor_ranges[col_name] = (lo, hi)
                except Exception:
                    pass

        log(f"Normal operating ranges loaded from '{meta_path}': {len(sensor_ranges)} sensors.")

        # ------------------------------------------------------------------
        # STEP 3 — Clean and prepare the dataframe
        # ------------------------------------------------------------------
        log("Parsing Timestamp column...")
        data_df_raw["Timestamp"] = pd.to_datetime(data_df_raw["Timestamp"], errors="coerce")
        bad_ts = data_df_raw["Timestamp"].isna().sum()
        if bad_ts > 0:
            log(f"  Dropped {bad_ts:,} rows with unparseable timestamps.")
        data_df_raw = data_df_raw.dropna(subset=["Timestamp"])
        data_df_raw = data_df_raw.set_index("Timestamp")

        # All sensor columns = everything except Production Grade
        sensor_cols = [c for c in data_df_raw.columns if c != "Production Grade"]
        log(f"Converting {len(sensor_cols)} sensor columns to numeric...")
        for col in sensor_cols:
            data_df_raw[col] = pd.to_numeric(
                data_df_raw[col].astype(str).str.replace(",", "").str.strip(),
                errors="coerce",
            )

        # Forward-fill then backward-fill: handles "Bad Input" / blanks / NaN
        log("Filling missing/bad values (ffill then bfill)...")
        data_df_raw[sensor_cols] = data_df_raw[sensor_cols].ffill().bfill()

        total_rows = len(data_df_raw)
        log(f"Dataset ready: {total_rows:,} rows, {len(sensor_cols)} sensor columns.")

        # ------------------------------------------------------------------
        # STEP 4 — Build feature matrix X and label vector y from real data
        #
        # Feature vector: binary symptom vector per row
        #   For each sensor that has a defined normal range:
        #     symptom[i] = 1 if value < range_low OR value > range_high
        #     symptom[i] = 0 otherwise
        #
        # Label assignment (5 classes):
        #   0 = Normal Operation      (Plant Load >= 5000, no critical deviation)
        #   1 = Nitrogen Loop Disruption
        #   2 = Blower Mechanical Failure
        #   3 = Decanter Overload
        #   4 = Scrubber Diff. Pressure Spike
        #
        # For rows where Plant Load < 5000 (shutdown window), we look at which
        # root-cause sensor deviated first:
        #   - Hot N2 Flow out of range                   -> class 1
        #   - FBD Blower B-4601 or B-4602 out of range  -> class 2
        #   - Any Decanter current out of range          -> class 3
        #   - C-4601 Diff. Pressure out of range         -> class 4
        #   - Otherwise (generic shutdown)               -> class 1 (N2 default)
        # ------------------------------------------------------------------
        log("Building binary symptom vectors from real sensor readings...")

        # Only use features that have a defined range
        features = [c for c in sensor_cols if c in sensor_ranges and c != "Production Grade"]
        num_features = len(features)
        log(f"Using {num_features} features with defined normal operating ranges.")

        feat_df = data_df_raw[features].copy()

        # Build symptom matrix: 1 where out-of-range, 0 where normal
        X_all = np.zeros((total_rows, num_features), dtype=np.float32)
        for fi, col in enumerate(features):
            lo, hi = sensor_ranges[col]
            vals = feat_df[col].values
            X_all[:, fi] = ((vals < lo) | (vals > hi)).astype(np.float32)

        log("Assigning fault labels from real process deviations...")

        # Helper: is a specific sensor out of range?
        def out_of_range_mask(col):
            if col not in feat_df.columns or col not in sensor_ranges:
                return np.zeros(total_rows, dtype=bool)
            lo, hi = sensor_ranges[col]
            v = feat_df[col].values
            return (v < lo) | (v > hi)

        plant_load = data_df_raw["Plant Load"].values if "Plant Load" in data_df_raw.columns else np.full(total_rows, 50000.0)

        # Build individual condition masks
        nitrogen_mask  = out_of_range_mask("Hot N2 Flow")
        blower_mask    = (out_of_range_mask("FBD Blower  B-4601 Current (A)") |
                          out_of_range_mask("FBD Blower  B-4602 Current (A)"))
        decanter_mask  = (out_of_range_mask("Decanter A Current (A)") |
                          out_of_range_mask("Decanter B Current (A)") |
                          out_of_range_mask("Decanter C Current (A)") |
                          out_of_range_mask("Decanter D Current (A)"))
        scrubber_mask  = out_of_range_mask("C-4601 Diff. Pressure")
        shutdown_mask  = plant_load < 5000.0

        y_all = np.zeros(total_rows, dtype=np.int32)  # default: Normal

        # Assign fault labels (priority order matters)
        # Rows in shutdown + specific root cause sensor deviated
        y_all[shutdown_mask & nitrogen_mask]  = 1
        y_all[shutdown_mask & blower_mask]    = 2
        y_all[shutdown_mask & decanter_mask]  = 3
        y_all[shutdown_mask & scrubber_mask]  = 4
        # Generic shutdown with no specific sensor identified -> nitrogen default
        generic_shutdown = shutdown_mask & ~nitrogen_mask & ~blower_mask & ~decanter_mask & ~scrubber_mask
        y_all[generic_shutdown] = 1

        # Class distribution report
        unique, counts = np.unique(y_all, return_counts=True)
        fault_categories = [
            "Normal Operation",
            "Nitrogen Loop Disruption",
            "Blower Mechanical Failure",
            "Decanter Overload",
            "Scrubber Diff. Pressure Spike"
        ]
        log("Label distribution from real data:")
        for cls, cnt in zip(unique, counts):
            log(f"  Class {cls} ({fault_categories[cls]}): {cnt:,} samples ({cnt/total_rows*100:.1f}%)")

        # ------------------------------------------------------------------
        # STEP 5 — Train/validation split (80 / 20 chronological split)
        # ------------------------------------------------------------------
        split = int(total_rows * 0.8)
        X_train, X_val = X_all[:split], X_all[split:]
        y_train, y_val = y_all[:split], y_all[split:]
        log(f"Train: {len(X_train):,} rows  |  Val: {len(X_val):,} rows")

        # ------------------------------------------------------------------
        # STEP 6 — Initialize MLP weights (He initialisation)
        #   Architecture: Input({num_features}) -> Hidden(64, ReLU) -> Hidden(32, ReLU) -> Output(5, Softmax)
        # ------------------------------------------------------------------
        input_dim  = num_features
        hidden1    = 64
        hidden2    = 32
        output_dim = 5

        np.random.seed(42)
        W1 = np.random.randn(input_dim, hidden1).astype(np.float32) * np.sqrt(2.0 / input_dim)
        b1 = np.zeros((1, hidden1), dtype=np.float32)
        W2 = np.random.randn(hidden1, hidden2).astype(np.float32) * np.sqrt(2.0 / hidden1)
        b2 = np.zeros((1, hidden2), dtype=np.float32)
        W3 = np.random.randn(hidden2, output_dim).astype(np.float32) * np.sqrt(2.0 / hidden2)
        b3 = np.zeros((1, output_dim), dtype=np.float32)

        log(f"MLP architecture: {input_dim} -> {hidden1} (ReLU) -> {hidden2} (ReLU) -> {output_dim} (Softmax)")

        # ------------------------------------------------------------------
        # STEP 7 — Full mini-batch SGD training loop with best-epoch tracking
        # ------------------------------------------------------------------
        learning_rate = 0.01
        total_epochs  = training_state["total_epochs"]
        batch_size    = 256

        history_loss = []
        history_acc  = []

        best_val_acc   = -1.0
        best_W1, best_b1 = W1.copy(), b1.copy()
        best_W2, best_b2 = W2.copy(), b2.copy()
        best_W3, best_b3 = W3.copy(), b3.copy()
        best_epoch       = 0

        num_train = X_train.shape[0]

        def forward(X, W1, b1, W2, b2, W3, b3):
            z1 = X @ W1 + b1
            a1 = np.maximum(0.0, z1)          # ReLU
            z2 = a1 @ W2 + b2
            a2 = np.maximum(0.0, z2)          # ReLU
            z3 = a2 @ W3 + b3
            # Numerically stable softmax
            z3 -= np.max(z3, axis=1, keepdims=True)
            exp_z3 = np.exp(z3)
            probs = exp_z3 / np.sum(exp_z3, axis=1, keepdims=True)
            return z1, a1, z2, a2, probs

        def compute_accuracy(X, y, W1, b1, W2, b2, W3, b3):
            _, _, _, _, probs = forward(X, W1, b1, W2, b2, W3, b3)
            preds = np.argmax(probs, axis=1)
            return float((preds == y).mean())

        log(f"Starting real training: {total_epochs} epochs, batch_size={batch_size}, lr={learning_rate}")

        for epoch in range(1, total_epochs + 1):
            # Shuffle training set each epoch
            idx = np.arange(num_train)
            np.random.shuffle(idx)
            X_shuf = X_train[idx]
            y_shuf = y_train[idx]

            epoch_loss = 0.0
            epoch_correct = 0

            for i in range(0, num_train, batch_size):
                Xb = X_shuf[i:i + batch_size]
                yb = y_shuf[i:i + batch_size]
                m  = Xb.shape[0]

                # ---- Forward pass ----
                z1, a1, z2, a2, probs = forward(Xb, W1, b1, W2, b2, W3, b3)

                # Cross-entropy loss
                loss_batch = -np.log(probs[np.arange(m), yb] + 1e-15).mean()
                epoch_loss    += loss_batch * m
                epoch_correct += (np.argmax(probs, axis=1) == yb).sum()

                # ---- Backward pass ----
                dz3 = probs.copy()
                dz3[np.arange(m), yb] -= 1
                dz3 /= m

                dW3 = a2.T @ dz3
                db3 = dz3.sum(axis=0, keepdims=True)

                da2 = dz3 @ W3.T
                dz2 = da2 * (z2 > 0)   # ReLU derivative

                dW2 = a1.T @ dz2
                db2_g = dz2.sum(axis=0, keepdims=True)

                da1 = dz2 @ W2.T
                dz1 = da1 * (z1 > 0)   # ReLU derivative

                dW1 = Xb.T @ dz1
                db1_g = dz1.sum(axis=0, keepdims=True)

                # ---- Weight update ----
                W3 -= learning_rate * dW3
                b3 -= learning_rate * db3
                W2 -= learning_rate * dW2
                b2 -= learning_rate * db2_g
                W1 -= learning_rate * dW1
                b1 -= learning_rate * db1_g

            epoch_loss /= num_train
            train_acc   = epoch_correct / num_train

            # Validation accuracy on full val set
            val_acc = compute_accuracy(X_val, y_val, W1, b1, W2, b2, W3, b3)

            history_loss.append(float(epoch_loss))
            history_acc.append(float(val_acc))

            # Track best epoch by validation accuracy
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_W1, best_b1 = W1.copy(), b1.copy()
                best_W2, best_b2 = W2.copy(), b2.copy()
                best_W3, best_b3 = W3.copy(), b3.copy()
                best_epoch = epoch

            # Update live training state (polled by frontend every 600ms)
            training_state["epoch"]    = epoch
            training_state["loss"]     = round(float(epoch_loss), 4)
            training_state["accuracy"] = round(float(val_acc), 4)

            if epoch % 5 == 0 or epoch == 1:
                log(f"Epoch {epoch}/{total_epochs} | loss: {epoch_loss:.4f} | train_acc: {train_acc*100:.1f}% | val_acc: {val_acc*100:.1f}%"
                    + (" ← best" if epoch == best_epoch else ""))

        # ------------------------------------------------------------------
        # STEP 8 — Save best-epoch weights
        # ------------------------------------------------------------------
        log(f"Training complete. Best epoch: {best_epoch} (val_acc={best_val_acc*100:.2f}%)")
        log("Saving best-epoch weights to model_weights.json...")

        model_export = {
            "features": features,
            "classes":  fault_categories,
            "W1": best_W1.tolist(),
            "b1": best_b1.tolist()[0],
            "W2": best_W2.tolist(),
            "b2": best_b2.tolist()[0],
            # W3/b3 stored for completeness; frontend uses W1/W2 for 2-layer forward pass
            "W3": best_W3.tolist(),
            "b3": best_b3.tolist()[0],
            "best_epoch": best_epoch,
            "best_val_accuracy": round(best_val_acc, 4),
            "history": {
                "loss":     history_loss,
                "accuracy": history_acc
            }
        }

        with open("data/model_weights.json", "w") as f:
            json.dump(model_export, f, indent=4)

        model_weights.update(model_export)

        log(f"model_weights.json updated — best epoch {best_epoch}, val_acc={best_val_acc*100:.2f}%.")
        training_state["status"] = "completed"

    except Exception as e:
        import traceback
        err = traceback.format_exc()
        log(f"TRAINING FAILED: {e}")
        log(err)
        training_state["status"] = "failed"

@app.post("/api/train")
def trigger_training(background_tasks: BackgroundTasks):
    global training_state
    if training_state["status"] == "running":
        return {"message": "Training already in progress", "status": "running"}
        
    training_state["status"] = "running"
    training_state["epoch"] = 0
    training_state["logs"] = []
    
    # Launch training in a background thread to allow API to remain responsive
    thread = threading.Thread(target=background_training_task)
    thread.daemon = True
    thread.start()
    
    return {"message": "Retraining started in the background", "status": "running"}

# Add helper for decorators
@app.get("/api/train/status")
def get_training_status():
    return training_state

# ----------------- Static Files & Index Router -----------------

app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")

@app.get("/")
def serve_index():
    return FileResponse("frontend/index.html")

@app.get("/data.js")
def serve_data():
    return FileResponse("frontend/data.js")

@app.get("/favicon.svg")
def serve_favicon():
    return FileResponse("frontend/favicon.svg")

@app.get("/icons.svg")
def serve_icons():
    return FileResponse("frontend/icons.svg")

if __name__ == "__main__":
    import uvicorn
    # Support host and port configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 2026))
    uvicorn.run(app, host=host, port=port)
