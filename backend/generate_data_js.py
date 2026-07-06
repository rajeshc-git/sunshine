import os
import json

def generate():
    js_content = "/* Consolidate RCA Data for Self-Contained Web App */\n\n"
    
    # List of JSON files to embed
    json_files = {
        "METADATA": "data/metadata.json",
        "CAUSAL_GRAPH": "data/causal_graph.json",
        "CAUSAL_EFFECTS": "data/causal_effects.json",
        "MODEL_WEIGHTS": "data/model_weights.json",
        "SHUTDOWN_EVENTS": "data/shutdown_events.json",
        "COLUMN_STATS": "data/column_stats.json"
    }
    
    for var_name, filename in json_files.items():
        if os.path.exists(filename):
            print(f"Embedding {filename} as const {var_name}...")
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            js_content += f"const {var_name} = {json.dumps(data, indent=2)};\n\n"
        else:
            print(f"Warning: {filename} not found, embedding empty object.")
            js_content += f"const {var_name} = {{}};\n\n"
            
    # Embed the CSV telemetry data as a string (limit to first 10,000 rows for browser dashboard performance)
    csv_file = "data/training_data_full.csv"
    if os.path.exists(csv_file):
        print(f"Embedding first 10,000 rows of {csv_file} as const TELEMETRY_CSV...")
        lines = []
        with open(csv_file, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 10001:  # header + 10,000 data lines
                    break
                lines.append(line)
        csv_data = "".join(lines)
        # Escape backslashes and quotes to safely embed as JS template literal
        escaped_csv = csv_data.replace("`", "\\`").replace("${", "\\${")
        js_content += f"const TELEMETRY_CSV = `{escaped_csv}`;\n\n"
    else:
        print(f"Warning: {csv_file} not found.")
        js_content += "const TELEMETRY_CSV = '';\n\n"

        
    # Write data.js
    with open("frontend/data.js", "w", encoding="utf-8") as f:
        f.write(js_content)
    print("Successfully generated data.js!")

if __name__ == "__main__":
    generate()
