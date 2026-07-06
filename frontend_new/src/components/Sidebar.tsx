import React from "react";

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isBackendOnline: boolean;
  metadataCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  isBackendOnline,
  metadataCount,
}) => {
  const navItems = [
    { id: "explorer", label: "Telemetry Explorer", icon: "fa-chart-line" },
    { id: "causal", label: "Causal Topology", icon: "fa-diagram-project" },
    { id: "rca", label: "RCA Diagnostics", icon: "fa-kit-medical" },
    { id: "network", label: "Neural Net Sandbox", icon: "fa-brain" },
    { id: "train-center", label: "Model Training", icon: "fa-dumbbell" },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo">
          <i className="fa-solid fa-bolt glow-icon"></i>
          <span>SUNSHINE RCA</span>
        </div>
        <div className="status-badge">
          <span
            className={`pulse-indicator ${isBackendOnline ? "green" : "green"}`}
            style={{
              backgroundColor: isBackendOnline ? "#10b981" : "#eab308",
              boxShadow: isBackendOnline
                ? "0 0 8px #10b981"
                : "0 0 8px #eab308",
            }}
          ></span>
          <span id="system-status-lbl">
            {isBackendOnline ? "Enterprise API Connected" : "Self-Contained Mode"}
          </span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`nav-btn ${activeTab === item.id ? "active" : ""}`}
            onClick={() => setActiveTab(item.id)}
            data-tab={item.id}
          >
            <i className={`fa-solid ${item.icon}`}></i>
            {item.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="dataset-info">
          <div className="info-label">Active Database</div>
          <div className="info-value">training_data_full.csv</div>
          <div className="info-meta">
            {metadataCount > 0 ? `${metadataCount} process variables` : "Loading..."}
          </div>
        </div>
      </div>
    </aside>
  );
};
