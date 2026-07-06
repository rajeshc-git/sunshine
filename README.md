# ☀️ Sunshine RCA Dashboard

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Container-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![Pandas](https://img.shields.io/badge/Data-Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![Vanilla JS](https://img.shields.io/badge/Frontend-Vanilla%20JS-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](#)

A professional, interactive, and high-performance **Asset Health Monitoring & Root Cause Analysis (RCA) Dashboard** for industrial plants. This system processes a year's worth of plant telemetry data (~527,000 logs) to identify and classify equipment failures, diagnose root causes, and visualizes causal graphs.

---

## 🏗️ Professional Project Structure

The project is organized cleanly to separate data, presentation, and execution concerns:

```
sunshine/
├── backend/                  # Python backend server and algorithms
│   ├── server.py             # FastAPI server, endpoints, and background trainer
│   ├── run_rca_modeling.py   # Causal topology and structural inference engine
│   ├── analyze_dataset_full.py # Telemetry preprocess and anomaly locator
│   └── convert_to_csv.py     # CSV conversion assistant
├── frontend/                 # Operator UI dashboard
│   ├── index.html            # Main interface
│   ├── app.js                # Core frontend controller & NN visualizer
│   ├── style.css             # Vanilla CSS custom design theme
│   └── data.js               # Offline browser fallback datasets
├── data/                     # Operational datasets (Single source of truth)
│   ├── training_data_full.csv # Unified pre-cleaned full year telemetry data
│   ├── metadata.json         # Operating ranges & DCS tags metadata
│   ├── shutdown_events.json  # Detected shutdown events list
│   └── model_weights.json    # Trained neural network weights
├── Dockerfile                # Dashboard container description
├── docker-compose.yml        # Multi-container service configuration
├── requirements.txt          # Python dependencies manifest
├── start_local.bat           # Launch on host machine (Local Python)
└── start_docker.bat          # Launch via Docker Compose (Containerized)
```

---

## 🚀 Quick Start Guide

You can launch the dashboard using either **Docker** or your **Local Python Host**.

### Option A: Local Host (Without Docker) 💻

Ensure you have **Python 3.10+** installed on your Windows machine, then run:

1. Double-click the **`start_local.bat`** script.
2. The script will automatically check your Python environment, install any missing dependencies, and launch the server.
3. Open your browser and navigate to: **[http://localhost:2026](http://localhost:2026)**

---

### Option B: Docker Container (Recommended) 🐳

Ensure you have **Docker Desktop** installed and running, then:

1. Double-click the **`start_docker.bat`** script.
2. Docker will build the image, mount your `./data` folder dynamically, and boot up the container.
3. Open your browser and navigate to: **[http://localhost:2026](http://localhost:2026)**

*Note: Any AI retraining performed inside the container will persistently update your host machine's `data/` folder via volume mounts.*

---

## 🧭 Dashboard Features & Walkthrough

### 1. Telemetry Explorer
* View real-time plotted sensor data and select from **19 historical shutdown events** detected from the full-year telemetry data.
* Highlight sensor variables to trace when currents, levels, or temperatures cross normal operating boundaries.

### 2. Causal Topology
* Examine the cause-and-effect physical networks of your plant nodes.
* Select a node to view its detailed DCS tag, historical statistics, engineering units, and direct parental/child dependencies.

### 3. RCA Diagnostics
* Runs causal inference calculations (powered by **DoWhy** average treatment effects).
* Isolates root cause rankings and details recommendations to guide plant operators.

### 4. NN Sandbox
* Simulates alert scenarios in real time. Toggling anomalous sensor states dynamically feeds forward into the multi-layer neural network model visualizer on your screen.

### 5. Training Center
* Triggers model retraining directly from the UI over all 527,041 logs. Live loss and accuracy indicators update sequentially on the log screen as calculations complete.

---

## 🛠️ Requirements & Troubleshooting

### Local Prerequisites
* **Python 3.10 or higher**
* System dependencies listed in `requirements.txt` (FastAPI, Uvicorn, Pandas, NumPy, OpenPyXL).

### Port Conflicts
* The application runs on port `2026`. If this port is already in use, you can adjust it by setting the `PORT` environment variable before running the scripts:
  ```cmd
  set PORT=3000
  start_local.bat
  ```
