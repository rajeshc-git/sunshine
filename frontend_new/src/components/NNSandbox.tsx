import React, { useEffect, useState } from "react";

interface NNSandboxProps {
  theme: "dark" | "light";
  localModelWeights: any;
}

const presetSymptoms: Record<string, string[]> = {
  normal: [],
  nitrogen: ["Hot N2 Flow", "FBD Bed Temperature  at 3rd Panel", "FBD Bed Temperature  at 7th Panel", "FBD Bed Temperature  at 14th Panel"],
  blower: ["FBD Blower  B-4601 Current (A)", "L-1 Conveying Pressure", "1st stage  Bed Level"],
  decanter: ["Decanter A Current (A)", "V-4607 Level", "V-4607 Pressure"],
  scrubber: ["C-4601 Diff. Pressure", "C-4601 Top Temperature", "P-4614A/B Recovered Flow"]
};

export const NNSandbox: React.FC<NNSandboxProps> = ({
  theme,
  localModelWeights,
}) => {
  const features = localModelWeights?.features || [];
  const classes = localModelWeights?.classes || [];

  const [symptoms, setSymptoms] = useState<number[]>([]);
  const [probabilities, setProbabilities] = useState<number[]>([]);
  const [hiddenActivations, setHiddenActivations] = useState<number[]>([]);
  const [maxProbIdx, setMaxProbIdx] = useState<number>(0);

  // Initialize symptoms array
  useEffect(() => {
    if (features.length > 0 && symptoms.length === 0) {
      setSymptoms(new Array(features.length).fill(0));
    }
  }, [features]);

  // Run forward-propagation when symptoms change
  useEffect(() => {
    if (features.length === 0 || symptoms.length === 0) return;
    forwardPropagate(symptoms);
  }, [symptoms, localModelWeights]);

  const forwardPropagate = (inputVector: number[]) => {
    const weights_h = localModelWeights.weights.hidden;
    const bias_h = localModelWeights.bias.hidden;
    const weights_o = localModelWeights.weights.output;
    const bias_o = localModelWeights.bias.output;

    const numHidden = bias_h.length;
    const numOutput = bias_o.length;

    // 1. Input to Hidden Layer (with ReLU)
    const hidden: number[] = [];
    for (let j = 0; j < numHidden; j++) {
      let sum = bias_h[j];
      for (let i = 0; i < inputVector.length; i++) {
        sum += inputVector[i] * weights_h[i][j];
      }
      hidden.push(Math.max(0, sum)); // ReLU
    }
    setHiddenActivations(hidden);

    // 2. Hidden to Output Layer
    const outputs: number[] = [];
    for (let k = 0; k < numOutput; k++) {
      let sum = bias_o[k];
      for (let j = 0; j < numHidden; j++) {
        sum += hidden[j] * weights_o[j][k];
      }
      outputs.push(sum);
    }

    // 3. Softmax Activation
    let maxLogit = -Infinity;
    for (let k = 0; k < numOutput; k++) {
      if (outputs[k] > maxLogit) maxLogit = outputs[k];
    }

    const exps = outputs.map((val) => Math.exp(val - maxLogit));
    const sumExps = exps.reduce((sum, val) => sum + val, 0);
    const probs = exps.map((val) => val / sumExps);
    setProbabilities(probs);

    let maxIdx = 0;
    let maxVal = -1;
    probs.forEach((p, idx) => {
      if (p > maxVal) {
        maxVal = p;
        maxIdx = idx;
      }
    });
    setMaxProbIdx(maxIdx);
  };

  const toggleSymptom = (idx: number) => {
    const nextSymptoms = [...symptoms];
    nextSymptoms[idx] = nextSymptoms[idx] === 1 ? 0 : 1;
    setSymptoms(nextSymptoms);
  };

  const applyPreset = (presetName: string) => {
    const activePresetTags = presetSymptoms[presetName] || [];
    const nextSymptoms = features.map((feat: string) =>
      activePresetTags.includes(feat) ? 1 : 0
    );
    setSymptoms(nextSymptoms);
  };

  return (
    <div className="nn-grid">
      {/* Left panel: Symptom Inputs */}
      <div className="nn-left glass-card">
        <div className="panel-section">
          <h3>
            <i className="fa-solid fa-hospital-user"></i> Trigger Anomaly Symptoms
          </h3>
          <p className="section-desc">
            Simulate sensor alarms. Toggle checkboxes to mark variables as anomalous. The neural network will instantly classify the root cause.
          </p>

          <div className="nn-preset-buttons">
            <button className="btn btn-secondary btn-xs" id="preset-normal" onClick={() => applyPreset("normal")}>
              Normal
            </button>
            <button className="btn btn-secondary btn-xs" id="preset-nitrogen" onClick={() => applyPreset("nitrogen")}>
              N2 Leak
            </button>
            <button className="btn btn-secondary btn-xs" id="preset-blower" onClick={() => applyPreset("blower")}>
              Blower Trip
            </button>
            <button className="btn btn-secondary btn-xs" id="preset-decanter" onClick={() => applyPreset("decanter")}>
              Decanter Overload
            </button>
            <button className="btn btn-secondary btn-xs" id="preset-scrubber" onClick={() => applyPreset("scrubber")}>
              Scrubber Block
            </button>
          </div>

          <div className="symptom-toggle-list" id="symptom-toggles">
            {features.map((feat: string, idx: number) => {
              const isActive = symptoms[idx] === 1;
              return (
                <div key={feat} className={`symptom-toggle-item ${isActive ? "active" : ""}`}>
                  <span>{feat}</span>
                  <label className="switch">
                    <input type="checkbox" checked={isActive} onChange={() => toggleSymptom(idx)} />
                    <span className="slider"></span>
                  </label>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Center panel: Visualizer */}
      <div className="nn-center glass-card">
        <h3>
          <i className="fa-solid fa-bezier-curve"></i> Deep Learning Model Inference
        </h3>
        <p className="section-desc">MLP forward-propagation mapping active symptoms to failure classes.</p>

        <div className="network-vis-container" id="nn-vis-canvas">
          <div className="nn-vis-graph">
            {/* Input layer */}
            <div className="nn-layer" id="layer-input">
              <div className="layer-title">
                Input Layer
                <br />
                (31 Symptoms)
              </div>
              <div className="node-dots-container" id="input-nodes-dots">
                {symptoms.map((val, idx) => (
                  <div key={idx} className={`nn-node-dot ${val === 1 ? "active-pink" : ""}`}></div>
                ))}
              </div>
            </div>

            <div className="nn-connector">
              <i className="fa-solid fa-arrows-left-right-to-line"></i>
            </div>

            {/* Hidden layer */}
            <div className="nn-layer" id="layer-hidden">
              <div className="layer-title">
                Hidden Layer
                <br />
                (16 ReLU Nodes)
              </div>
              <div className="node-dots-container" id="hidden-nodes-dots">
                {hiddenActivations.map((val, idx) => (
                  <div key={idx} className={`nn-node-dot ${val > 0 ? "active-cyan" : ""}`}></div>
                ))}
              </div>
            </div>

            <div className="nn-connector">
              <i className="fa-solid fa-arrows-left-right-to-line"></i>
            </div>

            {/* Output layer */}
            <div className="nn-layer" id="layer-output">
              <div className="layer-title">
                Output Layer
                <br />
                (5 Softmax Classes)
              </div>
              <div className="node-dots-container" id="output-nodes-dots">
                {classes.map((_: string, idx: number) => (
                  <div key={idx} className={`nn-node-dot ${idx === maxProbIdx ? "active-green" : ""}`}></div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Real-time Classifier Predictions */}
        <div className="classifier-predictions">
          <h3>Classification Outputs</h3>
          <div className="predictions-list" id="nn-predictions-container">
            {classes.map((className: string, idx: number) => {
              const probPct = probabilities[idx] ? (probabilities[idx] * 100).toFixed(1) : "0.0";
              const isTop = idx === maxProbIdx;

              return (
                <div key={className} className={`pred-row ${isTop ? "top-prediction" : ""}`}>
                  <div className="pred-meta">
                    <span className="pred-label">{className}</span>
                    <span className="pred-pct">{probPct}%</span>
                  </div>
                  <div className="pred-bar-bg">
                    <div className="pred-bar-fg" style={{ width: `${probPct}%` }}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Right panel: Stats */}
      <div className="nn-right glass-card">
        <h3>
          <i className="fa-solid fa-gauge-high"></i> Model Training Metrics</h3>
        <p className="section-desc">Training curves generated during deep learning model calibration (40 Epochs, MLP).</p>

        <div className="nn-stats-summary">
          <div className="nn-stat-box">
            <span className="lbl">Epochs</span>
            <span className="val">40</span>
          </div>
          <div className="nn-stat-box">
            <span className="lbl">Final Loss</span>
            <span className="val text-green">0.0017</span>
          </div>
          <div className="nn-stat-box">
            <span className="lbl">Final Accuracy</span>
            <span className="val text-green">100.0%</span>
          </div>
        </div>

        <div className="nn-chart-wrapper">
          {/* Note: In this React implementation, the training curves are statically loaded from local weights context or animated dynamically in the training tab */}
          <div style={{ color: "var(--text-muted)", fontSize: "11px", textAlign: "center", paddingTop: "50px" }}>
            Model weights loaded: <span className="text-green">Active</span>
            <br />
            Attribution network layout: <span className="text-cyan">Fully Connected</span>
          </div>
        </div>
      </div>
    </div>
  );
};
