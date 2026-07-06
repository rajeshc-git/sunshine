import os
import sys
import json
import numpy as np
import pandas as pd

# Reconfigure stdout for UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def load_data():
    sample_path = "data/training_data_full.csv"
    metadata_path = "data/metadata.json"
    
    if not os.path.exists(sample_path) or not os.path.exists(metadata_path):
        print("Error: preprocessed data or metadata not found. Waiting for preprocessing task...")
        return None, None
        
    df = pd.read_csv(sample_path, index_col="Timestamp", parse_dates=True)
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
        
    return df, metadata

def build_causal_graph(df, metadata):
    print("Building causal graph...")
    
    # 1. Define physical topology (DAG) nodes based on process engineering flow
    # Each connection represents: Source -> Target (causes target)
    physical_edges = [
        ("Plant Load", "Hot N2 Flow"),
        ("Plant Load", "FBD Blower  B-4601 Current (A)"),
        ("Plant Load", "FBD Blower  B-4602 Current (A)"),
        ("Hot N2 Flow", "Hot N2 Temperature (1st stage)"),
        ("Hot N2 Temperature (1st stage)", "FBD Bed Temperature  at 3rd Panel"),
        ("FBD Bed Temperature  at 3rd Panel", "FBD Bed Temperature  at 5th Panel"),
        ("FBD Bed Temperature  at 5th Panel", "FBD Bed Temperature  at 7th Panel"),
        ("FBD Bed Temperature  at 7th Panel", "FBD Bed Temperature  at 10th Panel"),
        ("FBD Bed Temperature  at 10th Panel", "FBD Bed Temperature  at 12th Panel"),
        ("FBD Bed Temperature  at 12th Panel", "FBD Bed Temperature  at 14th Panel"),
        ("FBD Bed Temperature  at 14th Panel", "FBD Off Gas Temperature (1st stage)"),
        ("FBD Bed Temperature  at 14th Panel", "FBD Off Gas Temperature (2nd stage)"),
        
        ("FBD Blower  B-4601 Current (A)", "1st stage  Bed Level"),
        ("FBD Blower  B-4602 Current (A)", "2nd stage  Bed Level"),
        ("1st stage  Bed Level", "Interstage PDC"),
        ("2nd stage  Bed Level", "Interstage PDC"),
        
        ("L-1 Conveying Pressure", "Decanter A Current (A)"),
        ("L-1 Conveying Pressure", "Decanter B Current (A)"),
        ("L-1 Conveying Pressure", "Decanter C Current (A)"),
        ("L-1 Conveying Pressure", "Decanter D Current (A)"),
        
        ("Decanter A Current (A)", "V-4607 Level"),
        ("Decanter B Current (A)", "V-4607 Level"),
        ("Decanter C Current (A)", "V-4607 Level"),
        ("Decanter D Current (A)", "V-4607 Level"),
        
        ("V-4607 Level", "V-4607 Temperature"),
        ("V-4607 Level", "V-4607 Pressure"),
        
        ("V-4607 Pressure", "P-4612A Current (A)"),
        ("V-4607 Pressure", "P-4612B Current (A)"),
        ("P-4612A Current (A)", "C-4601 Level"),
        ("P-4612B Current (A)", "C-4601 Level"),
        
        ("C-4601 Level", "C-4601 Top Temperature"),
        ("C-4601 Level", "C-4601 Diff. Pressure"),
        
        ("C-4601 Diff. Pressure", "P-4614A/B Recovered Flow")
    ]
    
    # Calculate correlation matrix for numeric columns only
    corr_matrix = df.corr(numeric_only=True)
    
    # Build list of nodes
    nodes = []
    for col in df.columns:
        if col in ["Production Grade"]:
            continue
        meta = metadata.get(col, {"unit": "", "range": "", "tag": ""})
        nodes.append({
            "id": col,
            "label": col,
            "unit": meta["unit"],
            "range": meta["range"],
            "tag": meta["tag"]
        })
        
    # Build list of links with correlation-based weights
    links = []
    for src, tgt in physical_edges:
        if src in corr_matrix.columns and tgt in corr_matrix.columns:
            corr_val = float(corr_matrix.loc[src, tgt])
            # Handle NaN correlation
            if np.isnan(corr_val):
                corr_val = 0.0
            links.append({
                "source": src,
                "target": tgt,
                "weight": round(corr_val, 3)
            })
            
    # Save causal graph
    graph_data = {"nodes": nodes, "links": links}
    with open("data/causal_graph.json", "w") as f:
        json.dump(graph_data, f, indent=4)
    print("Saved data/causal_graph.json")
    return graph_data

def run_causal_inference(df):
    print("Running causal inference (DoWhy treatment effects style)...")
    
    treatments = ["Hot N2 Flow", "FBD Blower  B-4601 Current (A)", "V-4607 Level", "P-4612A Current (A)"]
    outcomes = ["FBD Bed Temperature  at 14th Panel", "Interstage PDC", "V-4607 Pressure", "C-4601 Diff. Pressure"]
    
    effects = {}
    for t, o in zip(treatments, outcomes):
        if t in df.columns and o in df.columns:
            try:
                # Find some potential confounders (variables correlated with both)
                confounders = ["Plant Load"] if "Plant Load" in df.columns and t != "Plant Load" else []
                
                # Fit linear model
                X = df[[t] + confounders].dropna()
                Y = df.loc[X.index, o]
                
                # Convert to numeric just in case
                X_numeric = X.apply(pd.to_numeric, errors='coerce')
                Y_numeric = pd.to_numeric(Y, errors='coerce')
                
                # Standardize variables to get standardized treatment effect
                X_std = (X_numeric - X_numeric.mean()) / X_numeric.std()
                Y_std = (Y_numeric - Y_numeric.mean()) / Y_numeric.std()
                
                # Add constant
                X_std["const"] = 1.0
                
                # Linear regression using numpy
                coeffs = np.linalg.lstsq(X_std, Y_std, rcond=None)[0]
                ate = float(coeffs[0]) # average treatment effect coefficient
                
                effects[f"{t} -> {o}"] = {
                    "treatment": t,
                    "outcome": o,
                    "ate": round(ate, 4),
                    "confounders": confounders,
                    "method": "Linear Regression with Backdoor Adjustment"
                }
            except Exception as e:
                print(f"Error estimating effect for {t} -> {o}: {e}")
                
    with open("data/causal_effects.json", "w") as f:
        json.dump(effects, f, indent=4)
    print("Saved data/causal_effects.json")

def train_symptom_classifier(df, metadata):
    print("Training Deep Learning Symptom Classifier (ML for RCA style)...")
    
    ranges = {}
    for col, meta in metadata.items():
        range_str = meta.get("range", "")
        if "-" in range_str:
            try:
                parts = range_str.split("-")
                low = float(parts[0].replace(",", "").strip())
                high = float(parts[1].replace(",", "").strip())
                ranges[col] = (low, high)
            except:
                pass
                
    # Define features
    features = [c for c in df.columns if c in ranges]
    num_features = len(features)
    
    fault_categories = [
        "Normal Operation",
        "Nitrogen Loop Disruption",
        "Blower Mechanical Failure",
        "Decanter Overload",
        "Scrubber Diff. Pressure Spike"
    ]
    
    X_train = []
    y_train = []
    
    np.random.seed(42)
    # Generate 1000 samples per class
    samples_per_class = 800
    
    for label in range(5):
        for _ in range(samples_per_class):
            # Start with a base symptom vector (mostly zeros)
            symptom = np.zeros(num_features)
            # Add some random noise flips (5% chance of random anomaly)
            symptom = np.where(np.random.rand(num_features) < 0.05, 1, 0)
            
            if label == 1: # Nitrogen Loop
                idx_flow = features.index("Hot N2 Flow")
                idx_t1 = features.index("FBD Bed Temperature  at 3rd Panel")
                idx_t2 = features.index("FBD Bed Temperature  at 14th Panel")
                symptom[idx_flow] = 1
                symptom[idx_t1] = 1
                symptom[idx_t2] = 1
                if "FBD Off Gas Temperature (1st stage)" in features:
                    idx_off = features.index("FBD Off Gas Temperature (1st stage)")
                    symptom[idx_off] = 1
                    
            elif label == 2: # Blower issue
                idx_b1 = features.index("FBD Blower  B-4601 Current (A)")
                idx_l1 = features.index("1st stage  Bed Level")
                symptom[idx_b1] = 1
                symptom[idx_l1] = 1
                if "Interstage PDC" in features:
                    idx_pdc = features.index("Interstage PDC")
                    symptom[idx_pdc] = 1
                    
            elif label == 3: # Decanter issue
                idx_da = features.index("Decanter A Current (A)")
                idx_db = features.index("Decanter B Current (A)")
                idx_vlvl = features.index("V-4607 Level")
                symptom[idx_da] = 1
                symptom[idx_db] = 1
                symptom[idx_vlvl] = 1
                
            elif label == 4: # Scrubber issue
                idx_dp = features.index("C-4601 Diff. Pressure")
                idx_top = features.index("C-4601 Top Temperature")
                symptom[idx_dp] = 1
                symptom[idx_top] = 1
                if "P-4614A/B Recovered Flow" in features:
                    idx_flow = features.index("P-4614A/B Recovered Flow")
                    symptom[idx_flow] = 1
                    
            elif label == 0: # Normal
                symptom = np.zeros(num_features)
                
            X_train.append(symptom)
            y_train.append(label)
            
    X_train = np.array(X_train, dtype=np.float32)
    y_train = np.array(y_train, dtype=np.int32)
    
    # Train a Multi-Layer Perceptron (MLP) in Python using NumPy!
    input_dim = num_features
    hidden_dim = 16
    output_dim = 5
    
    # Initialize weights
    W1 = np.random.randn(input_dim, hidden_dim) * np.sqrt(2.0 / input_dim)
    b1 = np.zeros((1, hidden_dim))
    W2 = np.random.randn(hidden_dim, output_dim) * np.sqrt(2.0 / hidden_dim)
    b2 = np.zeros((1, output_dim))
    
    # Hyperparameters
    learning_rate = 0.05
    epochs = 40
    batch_size = 32
    
    history_loss = []
    history_acc = []
    
    print(f"Neural Network: Input Dim={input_dim}, Hidden Dim={hidden_dim}, Output Dim={output_dim}")
    print("Training neural network...")
    
    num_samples = X_train.shape[0]
    for epoch in range(epochs):
        indices = np.arange(num_samples)
        np.random.shuffle(indices)
        X_shuffled = X_train[indices]
        y_shuffled = y_train[indices]
        
        epoch_loss = 0
        correct = 0
        
        for i in range(0, num_samples, batch_size):
            X_batch = X_shuffled[i:i+batch_size]
            y_batch = y_shuffled[i:i+batch_size]
            
            z1 = np.dot(X_batch, W1) + b1
            a1 = np.maximum(0, z1) # ReLU
            
            z2 = np.dot(a1, W2) + b2
            exp_z2 = np.exp(z2 - np.max(z2, axis=1, keepdims=True))
            probs = exp_z2 / np.sum(exp_z2, axis=1, keepdims=True)
            
            m = X_batch.shape[0]
            loss = -np.log(probs[np.arange(m), y_batch] + 1e-15).mean()
            epoch_loss += loss * m
            
            preds = np.argmax(probs, axis=1)
            correct += (preds == y_batch).sum()
            
            dz2 = probs.copy()
            dz2[np.arange(m), y_batch] -= 1
            dz2 /= m
            
            dW2 = np.dot(a1.T, dz2)
            db2 = np.sum(dz2, axis=0, keepdims=True)
            
            da1 = np.dot(dz2, W2.T)
            dz1 = da1 * (z1 > 0) # ReLU derivative
            
            dW1 = np.dot(X_batch.T, dz1)
            db1 = np.sum(dz1, axis=0, keepdims=True)
            
            W1 -= learning_rate * dW1
            b1 -= learning_rate * db1
            W2 -= learning_rate * dW2
            b2 -= learning_rate * db2
            
        epoch_loss /= num_samples
        epoch_acc = correct / num_samples
        history_loss.append(float(epoch_loss))
        history_acc.append(float(epoch_acc))
        
        if (epoch + 1) % 5 == 0:
            print(f"  Epoch {epoch+1}/{epochs} - Loss: {epoch_loss:.4f} - Accuracy: {epoch_acc:.4f}")
            
    model_export = {
        "features": features,
        "classes": fault_categories,
        "W1": W1.tolist(),
        "b1": b1.tolist()[0],
        "W2": W2.tolist(),
        "b2": b2.tolist()[0],
        "history": {
            "loss": history_loss,
            "accuracy": history_acc
        }
    }
    
    with open("data/model_weights.json", "w") as f:
        json.dump(model_export, f, indent=4)
    print("Saved data/model_weights.json")

def main():
    df, metadata = load_data()
    if df is None:
        return
        
    build_causal_graph(df, metadata)
    run_causal_inference(df)
    train_symptom_classifier(df, metadata)
    print("\nAll modeling and pre-computations completed successfully!")

if __name__ == "__main__":
    main()
