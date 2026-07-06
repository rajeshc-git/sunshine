import React, { useEffect } from "react";

interface HeaderProps {
  activeTab: string;
  theme: "dark" | "light";
  setTheme: (theme: "dark" | "light") => void;
  plantStatus: string;
  isPlantShutdown: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  theme,
  setTheme,
  plantStatus,
  isPlantShutdown,
}) => {
  // Sync theme with body element class
  useEffect(() => {
    if (theme === "light") {
      document.body.classList.add("light-theme");
    } else {
      document.body.classList.remove("light-theme");
    }
  }, [theme]);

  const toggleTheme = () => {
    const nextTheme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    localStorage.setItem("theme", nextTheme);
  };

  const getHeaderInfo = () => {
    switch (activeTab) {
      case "explorer":
        return {
          title: "Telemetry Explorer",
          subtitle: "Analyze real-time process variables and detect anomalies.",
        };
      case "causal":
        return {
          title: "Causal Topology Graph",
          subtitle: "Visualize causal dependencies discovered from telemetry correlations (PyRCA).",
        };
      case "rca":
        return {
          title: "RCA Diagnostics Engine",
          subtitle: "Trace failure roots using Random Walk attribution and DoWhy causal validation.",
        };
      case "network":
        return {
          title: "Neural Network Sandbox",
          subtitle: "Interact with the symptom classifier neural network in real-time.",
        };
      case "train-center":
        return {
          title: "Model Training Center",
          subtitle: "Re-train neural network classifier directly on the cleaned telemetry data.",
        };
      default:
        return {
          title: "Asset Health & Root Cause Analysis Dashboard",
          subtitle: "Sunshine Telemetry RCA platform.",
        };
    }
  };

  const { title, subtitle } = getHeaderInfo();

  return (
    <header className="main-header">
      <div className="header-title">
        <h1 id="page-title">{title}</h1>
        <p id="page-subtitle">{subtitle}</p>
      </div>
      <div className="header-actions">
        <div className="quick-stat">
          <span className="stat-label">Plant Status:</span>
          <span
            className={`stat-val ${isPlantShutdown ? "text-pink" : "text-green"}`}
            id="plant-status-text"
          >
            {plantStatus}
          </span>
        </div>
        <button
          id="theme-toggle"
          className="theme-toggle-btn"
          title="Toggle Light/Dark Mode"
          onClick={toggleTheme}
        >
          <i className={`fa-solid ${theme === "dark" ? "fa-moon" : "fa-sun"}`}></i>
        </button>
      </div>
    </header>
  );
};
