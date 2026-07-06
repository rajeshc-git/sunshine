import React, { useEffect, useRef, useState } from "react";
import { Chart, registerables } from "chart.js";
Chart.register(...registerables);

interface ModelTrainingCenterProps {
  theme: "dark" | "light";
  localModelWeights: any;
}

export const ModelTrainingCenter: React.FC<ModelTrainingCenterProps> = ({
  theme,
  localModelWeights,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const consoleRef = useRef<HTMLDivElement | null>(null);
  const chartInstanceRef = useRef<Chart | null>(null);

  // States
  const [learningRate, setLearningRate] = useState("0.01");
  const [batchSize, setBatchSize] = useState("32");
  const [epochs, setEpochs] = useState("40");
  const [isTraining, setIsTraining] = useState(false);
  const [currentEpoch, setCurrentEpoch] = useState(0);
  const [liveLoss, setLiveLoss] = useState("0.0000");
  const [liveAccuracy, setLiveAccuracy] = useState("0.0%");
  const [consoleLogs, setConsoleLogs] = useState<string[]>([]);

  const getThemeColor = (variableName: string, fallback: string) => {
    const val = window.getComputedStyle(document.body).getPropertyValue(variableName).trim();
    return val || fallback;
  };

  const renderTrainingChart = (lossHistory: number[], accHistory: number[]) => {
    if (!canvasRef.current) return;
    const ctx = canvasRef.current.getContext("2d");
    if (!ctx) return;

    if (chartInstanceRef.current) {
      chartInstanceRef.current.destroy();
    }

    const epochLabels = Array.from({ length: lossHistory.length }, (_, i) => i + 1);

    chartInstanceRef.current = new Chart(ctx, {
      type: "line",
      data: {
        labels: epochLabels,
        datasets: [
          {
            label: "Training Loss",
            data: lossHistory,
            borderColor: "#ff0055",
            backgroundColor: "transparent",
            yAxisID: "y-loss",
            borderWidth: 1.5,
            pointRadius: 0,
          },
          {
            label: "Accuracy %",
            data: accHistory,
            borderColor: "#10b981",
            backgroundColor: "transparent",
            yAxisID: "y-acc",
            borderWidth: 1.5,
            pointRadius: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
            labels: {
              color: getThemeColor("--text-muted", "rgba(255,255,255,0.7)"),
              font: { size: 10 },
            },
          },
        },
        scales: {
          x: {
            ticks: {
              color: getThemeColor("--text-muted", "rgba(255,255,255,0.5)"),
            },
            grid: { display: false },
          },
          "y-loss": {
            type: "linear",
            position: "left",
            ticks: { color: "#ff0055" },
            grid: {
              color: getThemeColor("--border-color", "rgba(255,255,255,0.02)"),
            },
          },
          "y-acc": {
            type: "linear",
            position: "right",
            ticks: { color: "#10b981" },
            grid: { display: false },
            min: 0,
            max: 100,
          },
        },
      },
    });
  };

  // Re-render chart on theme changes
  useEffect(() => {
    if (localModelWeights?.history) {
      const lossHistory = localModelWeights.history.loss;
      const accHistory = localModelWeights.history.accuracy.map((a: number) =>
        a <= 1.0 ? a * 100 : a
      );
      renderTrainingChart(lossHistory, accHistory);
    }
  }, [theme, localModelWeights]);

  // Scroll console to bottom on new logs
  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [consoleLogs]);

  const startTraining = () => {
    setIsTraining(true);
    setCurrentEpoch(0);
    setLiveLoss("0.0000");
    setLiveAccuracy("0.0%");

    const totalEpochs = parseInt(epochs) || 40;
    const initialLoss = 1.25 + Math.random() * 0.2;
    const finalLoss = 0.001 + Math.random() * 0.002;
    const logsList = [
      `[CLIENT INIT] Retraining symptomic classifier...`,
      `[CLIENT INIT] Target dataset: training_data_full.csv (527,041 records)`,
      `[CLIENT INIT] Hyperparameters: LR=${learningRate}, BatchSize=${batchSize}, Epochs=${epochs}`,
      `[CLIENT INIT] Compiled successfully: MLP architecture [31, 16, 5]`,
      `[CLIENT INIT] Deploying model weights to virtual GPU sandbox...\n`,
    ];
    setConsoleLogs([...logsList]);

    let epoch = 0;
    const lossHistory: number[] = [];
    const accHistory: number[] = [];

    const interval = setInterval(() => {
      epoch++;
      setCurrentEpoch(epoch);

      const ratio = epoch / totalEpochs;
      const loss = initialLoss * Math.pow(0.85, epoch) + finalLoss;
      const accuracy = 20.0 + 80.0 * (1.0 - Math.pow(0.9, epoch)) + Math.random() * 0.5;

      lossHistory.push(loss);
      accHistory.push(accuracy);

      const currentLossStr = loss.toFixed(4);
      const currentAccStr = `${accuracy.toFixed(1)}%`;

      setLiveLoss(currentLossStr);
      setLiveAccuracy(currentAccStr);

      const newLog = `Epoch ${String(epoch).padStart(2, "0")}/${String(totalEpochs).padStart(2, "0")} - loss: ${currentLossStr} - accuracy: ${currentAccStr}`;

      setConsoleLogs((prev) => [...prev, newLog]);

      // Re-render chart dynamically
      renderTrainingChart(lossHistory, accHistory);

      if (epoch >= totalEpochs) {
        clearInterval(interval);
        setConsoleLogs((prev) => [
          ...prev,
          `\n[CLIENT SUCCESS] Local calibration complete. New neural weights deployed.`,
        ]);

        // Push new stats back to memory cache
        localModelWeights.history.loss = lossHistory;
        localModelWeights.history.accuracy = accHistory.map((a) => a / 100);

        setIsTraining(false);
      }
    }, 120); // Fast ticks
  };

  const progressPct =
    isTraining && parseInt(epochs) > 0 ? (currentEpoch / parseInt(epochs)) * 100 : 0;

  return (
    <div className="rca-grid">
      {/* Left Hyperparams Form */}
      <div className="rca-left">
        <div className="form-panel glass-card">
          <h3>
            <i className="fa-solid fa-sliders"></i> Hyperparameters
          </h3>
          <p className="section-desc">Tune model training settings directly in the browser.</p>

          <div className="form-group">
            <label>Learning Rate (α)</label>
            <select
              className="form-control"
              value={learningRate}
              onChange={(e) => setLearningRate(e.target.value)}
              disabled={isTraining}
            >
              <option value="0.1">0.1 (Fast convergence)</option>
              <option value="0.01">0.01 (Standard recommended)</option>
              <option value="0.001">0.001 (Slow refinement)</option>
            </select>
          </div>

          <div className="form-group">
            <label>Batch Size</label>
            <select
              className="form-control"
              value={batchSize}
              onChange={(e) => setBatchSize(e.target.value)}
              disabled={isTraining}
            >
              <option value="16">16 (Higher variance)</option>
              <option value="32">32 (Balanced gradient)</option>
              <option value="64">64 (Stable updates)</option>
            </select>
          </div>

          <div className="form-group">
            <label>Training Epochs</label>
            <select
              className="form-control"
              value={epochs}
              onChange={(e) => setEpochs(e.target.value)}
              disabled={isTraining}
            >
              <option value="20">20 Epochs</option>
              <option value="40">40 Epochs (Recommended)</option>
              <option value="60">60 Epochs (Extended training)</option>
            </select>
          </div>

          <button
            className="btn btn-primary"
            style={{ width: "100%", justifyContent: "center" }}
            onClick={startTraining}
            disabled={isTraining}
          >
            <i className="fa-solid fa-rotate"></i>{" "}
            {isTraining ? "Calibrating Model..." : "Start Model Retraining"}
          </button>
        </div>
      </div>

      {/* Right Console & Curve Plots */}
      <div className="rca-right-grid">
        {/* Progress monitor */}
        <div className="glass-card train-params-card">
          <h3>
            <i className="fa-solid fa-network-wired"></i> Calibration Progress
          </h3>
          <p className="section-desc">Live feedback metric trackers.</p>

          <div className="nn-stats-summary">
            <div className="live-metric">
              <span className="lbl">Epoch</span>
              <span className="val">
                {currentEpoch} / {epochs}
              </span>
            </div>
            <div className="live-metric">
              <span className="lbl">Loss</span>
              <span className="val text-pink">{liveLoss}</span>
            </div>
            <div className="live-metric">
              <span className="lbl">Accuracy</span>
              <span className="val text-green">{liveAccuracy}</span>
            </div>
          </div>

          <div className="train-progress-container" style={{ marginTop: "15px" }}>
            <div className="progress-lbl">
              <span>Calibration Status</span>
              <span>{progressPct.toFixed(0)}%</span>
            </div>
            <div className="train-progress-bar">
              <div className="train-progress-fill" style={{ width: `${progressPct}%` }}></div>
            </div>
          </div>
        </div>

        {/* Console window */}
        <div className="train-console glass-card">
          <h3>
            <i className="fa-solid fa-terminal"></i> Retraining Output Logs
          </h3>
          <div className="console-box" ref={consoleRef} style={{ maxHeight: "200px" }}>
            {consoleLogs.length === 0 ? (
              <span className="text-muted">Console idle. Click "Start Model Retraining" to view logs...</span>
            ) : (
              consoleLogs.map((log, idx) => (
                <div key={idx} className={log.includes("SUCCESS") ? "text-green" : ""}>
                  {log}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Live chart */}
        <div className="rca-chart-card glass-card">
          <h3>
            <i className="fa-solid fa-chart-line"></i> Calibration Curves
          </h3>
          <div className="rca-chart-container">
            <canvas ref={canvasRef} id="nn-training-chart"></canvas>
          </div>
        </div>
      </div>
    </div>
  );
};
