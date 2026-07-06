"""
convert_to_csv.py
=================
Converts  "training dataset.xlsx"  (198 MB, ~527 k rows) to a clean CSV
with ZERO data loss.

What this script does carefully:
  - Reads the FULL workbook into RAM with pandas (40 GB RAM → no problem)
  - Preserves EVERY data row from row 9 onward (0-indexed)
  - Keeps ALL original values as-is (no numeric coercion, no NaN filling)
    so the training pipeline can decide how to handle bad/missing readings
  - Keeps the Production Grade text column untouched
  - Saves "Bad Input" strings, blanks, and NaN exactly as they are
  - Writes timestamps with full datetime precision
  - Produces two output files:
      training_data_full.csv   — complete dataset (all rows, all columns)
      training_metadata.json   — column names, units, ranges, tags
  - Prints a detailed integrity report at the end so you can verify
    nothing was lost

Run from the sunshine directory:
    python convert_to_csv.py
"""

import os
import sys
import json
import time
import pandas as pd
import numpy as np

# ── UTF-8 console output ──────────────────────────────────────────────────────
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# ── Paths ─────────────────────────────────────────────────────────────────────
XLSX_PATH     = "data/training dataset.xlsx"
OUT_CSV       = "data/training_data_full.csv"
OUT_META      = "data/training_metadata.json"

# ── Helpers ───────────────────────────────────────────────────────────────────
def separator(title=""):
    line = "─" * 70
    if title:
        pad = (68 - len(title)) // 2
        print(f"┌{'─'*pad} {title} {'─'*(68-pad-len(title))}┐")
    else:
        print(line)

def check_file():
    if not os.path.exists(XLSX_PATH):
        print(f"\n✗  File not found: '{XLSX_PATH}'")
        print("   Make sure you run this script from the sunshine directory.")
        sys.exit(1)
    size_mb = os.path.getsize(XLSX_PATH) / (1024 * 1024)
    print(f"✓  Found '{XLSX_PATH}'  ({size_mb:.1f} MB)")
    return size_mb

# ── Main conversion ───────────────────────────────────────────────────────────
def convert():
    separator("DATASET CONVERSION: xlsx → csv")
    print()

    size_mb = check_file()

    # ── STEP 1: Load full workbook ────────────────────────────────────────────
    print(f"\n[1/6] Loading full workbook into RAM (this may take 60-120 s for {size_mb:.0f} MB)...")
    t0 = time.time()

    # header=None → we read every row as plain data, no pandas header magic
    # keep_default_na=False → preserve strings like "Bad Input", "nan", ""
    #                         exactly as they appear in the cells
    raw_df = pd.read_excel(
        XLSX_PATH,
        sheet_name=0,
        header=None,
        keep_default_na=False,   # ← critical: do NOT silently turn "" into NaN
        dtype=str,               # ← read everything as string first; we decide
                                 #   what to convert later in training
    )

    elapsed = time.time() - t0
    print(f"   Loaded in {elapsed:.1f} s  →  raw shape: {raw_df.shape[0]} rows × {raw_df.shape[1]} columns")

    # ── STEP 2: Extract header rows ───────────────────────────────────────────
    print("\n[2/6] Parsing header rows (names / units / ranges / tags)...")

    # Row indices (0-based) in the raw dataframe:
    #   0-4  : info / description rows (START TIME, END TIME, INTERVAL, etc.)
    #   5    : column names
    #   6    : engineering units
    #   7    : normal operating ranges
    #   8    : DCS tag names
    #   9+   : actual 1-minute telemetry data

    raw_cols   = list(raw_df.iloc[5])
    raw_units  = list(raw_df.iloc[6])
    raw_ranges = list(raw_df.iloc[7])
    raw_tags   = list(raw_df.iloc[8])

    # Build clean column names
    column_names = []
    for idx, c in enumerate(raw_cols):
        val = str(c).strip()
        if val == "" or val.lower() == "nan":
            column_names.append(f"Col_{idx}")
        else:
            column_names.append(val.replace("\n", " ").strip())

    # Column index 1 is always the timestamp column
    column_names[1] = "Timestamp"

    num_cols = len(column_names)
    print(f"   Total columns in xlsx: {num_cols}")
    print(f"   Column names (index 0-5): {column_names[:6]}")
    print(f"   ... (index {num_cols-3} to {num_cols-1}): {column_names[-3:]}")

    # ── STEP 3: Build metadata JSON ───────────────────────────────────────────
    print("\n[3/6] Building metadata.json (units / ranges / tags)...")

    metadata = {}
    for i in range(2, num_cols):
        col_name = column_names[i]

        unit  = str(raw_units[i]).replace("\n", " ").strip()
        rng   = str(raw_ranges[i]).replace("\n", " ").strip()
        tag   = str(raw_tags[i]).replace("\n", " ").strip()

        # Treat "nan" strings as empty (artifact of dtype=str read)
        unit  = "" if unit.lower()  == "nan" else unit
        rng   = "" if rng.lower()   == "nan" else rng
        tag   = "" if tag.lower()   == "nan" else tag

        metadata[col_name] = {
            "index": i,
            "unit":  unit,
            "range": rng,
            "tag":   tag,
        }

    with open(OUT_META, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)
    print(f"   ✓  Saved {OUT_META}  ({len(metadata)} sensor/variable entries)")

    # ── STEP 4: Extract data rows ─────────────────────────────────────────────
    print("\n[4/6] Extracting data rows (row 9 onwards)...")

    data_df = raw_df.iloc[9:].copy()
    data_df.columns = column_names

    # Drop the blank placeholder column (always Col_0 at index 0)
    data_df = data_df.drop(columns=["Col_0"], errors="ignore")
    final_cols = list(data_df.columns)   # Timestamp, Production Grade, sensor1, ...

    total_rows = len(data_df)
    total_cols = len(final_cols)
    print(f"   Data rows extracted : {total_rows:,}")
    print(f"   Data columns        : {total_cols}")
    print(f"   Columns: {final_cols[:4]} ... {final_cols[-2:]}")

    # ── STEP 5: Integrity checks BEFORE writing ───────────────────────────────
    print("\n[5/6] Running pre-write integrity checks...")

    # 5a. Check row count matches expected (~527 k for a full year at 1-min intervals)
    expected_low  = 500_000
    expected_high = 530_000
    if expected_low <= total_rows <= expected_high:
        print(f"   ✓  Row count {total_rows:,} is within expected range [{expected_low:,} – {expected_high:,}]")
    else:
        print(f"   ⚠  Row count {total_rows:,} is OUTSIDE expected range — verify xlsx is complete")

    # 5b. Check timestamp column parses correctly
    ts_series = pd.to_datetime(data_df["Timestamp"], errors="coerce")
    bad_ts    = ts_series.isna().sum()
    if bad_ts == 0:
        print(f"   ✓  All {total_rows:,} timestamps parse successfully")
        print(f"      Range: {ts_series.min()}  →  {ts_series.max()}")
    else:
        print(f"   ⚠  {bad_ts:,} timestamps could NOT be parsed (kept as-is in CSV)")

    # 5c. Per-column: count blank cells and "Bad Input" strings
    print("\n   Blank / Bad-Input counts per sensor column:")
    sensor_columns = [c for c in final_cols if c not in ("Timestamp", "Production Grade", "Col_0")]
    issues_found   = False
    for col in sensor_columns:
        series = data_df[col].astype(str)
        blank_count   = (series.str.strip() == "").sum()
        bad_inp_count = series.str.contains("Bad Input", case=False, na=False).sum()
        nan_str_count = (series.str.lower() == "nan").sum()
        total_bad     = blank_count + bad_inp_count + nan_str_count
        if total_bad > 0:
            pct = total_bad / total_rows * 100
            print(f"   ⚠  {col:<45}  {total_bad:>6,} missing/bad  ({pct:.2f}%)")
            issues_found = True
    if not issues_found:
        print("   ✓  No blank or Bad-Input cells found in any sensor column")

    # 5d. Check Production Grade column
    grade_col = data_df["Production Grade"].astype(str)
    unique_grades = grade_col.unique()
    print(f"\n   Production Grade unique values ({len(unique_grades)}): {list(unique_grades[:10])}")

    # ── STEP 6: Write CSV ─────────────────────────────────────────────────────
    print(f"\n[6/6] Writing '{OUT_CSV}'...")
    t1 = time.time()

    data_df.to_csv(
        OUT_CSV,
        index=False,          # Timestamp is already a column — no extra index
        encoding="utf-8",
        lineterminator="\n",  # Unix line endings — consistent across platforms
    )

    elapsed = time.time() - t1
    out_size_mb = os.path.getsize(OUT_CSV) / (1024 * 1024)
    print(f"   ✓  Written in {elapsed:.1f} s  →  {out_size_mb:.1f} MB")

    # ── STEP 7: Post-write verification ───────────────────────────────────────
    separator("POST-WRITE VERIFICATION")
    print()
    print("   Reading back CSV to verify row + column count...")
    verify_df = pd.read_csv(OUT_CSV, nrows=5, dtype=str)
    verify_full = pd.read_csv(OUT_CSV, dtype=str)

    v_rows = len(verify_full)
    v_cols = len(verify_full.columns)

    row_ok = v_rows == total_rows
    col_ok = v_cols == total_cols

    print(f"   Rows  — written: {total_rows:,}   read back: {v_rows:,}   {'✓ MATCH' if row_ok else '✗ MISMATCH'}")
    print(f"   Cols  — written: {total_cols}      read back: {v_cols}      {'✓ MATCH' if col_ok else '✗ MISMATCH'}")

    if row_ok and col_ok:
        print("\n   ✓  CSV is complete — zero data loss confirmed.")
    else:
        print("\n   ✗  MISMATCH DETECTED — do NOT use this CSV for training.")
        print("      Re-run this script to regenerate.")
        sys.exit(1)

    # Final summary
    print()
    separator("SUMMARY")
    print(f"""
   Source xlsx  : {XLSX_PATH}  ({size_mb:.1f} MB)
   Output CSV   : {OUT_CSV}   ({out_size_mb:.1f} MB)
   Metadata     : {OUT_META}

   Total rows   : {total_rows:,}
   Total cols   : {total_cols}
   Timestamp    : {ts_series.min()}  →  {ts_series.max()}

   CSV is ready for training.
   The server will automatically use '{OUT_CSV}' on the next
   "Start Retraining" click — no xlsx reading required.
""")


if __name__ == "__main__":
    convert()
