import React, { useEffect, useRef, useState } from "react";
import { Chart, registerables } from "chart.js";
Chart.register(...registerables);

interface TelemetryExplorerProps {
  theme: "dark" | "light";
  localShutdownEvents: any[];
  localColumnStats: any;
  localMetadata: any;
  selectedShutdownEventId: number;
  setSelectedShutdownEventId: (id: number) => void;
  selectedSensors: string[];
  setSelectedSensors: (sensors: string[]) => void;
  activeTelemetryDataset: any[];
  loadTelemetryForEvent: (eventId: number) => void;
}

const seriesColors = [
  "#00f0ff", // Cyan
  "#10b981", // Emerald
  "#f59e0b", // Amber
  "#ff0055", // Cyber Pink
  "#8b5cf6", // Purple
  "#ec4899", // Pink
  "#3b82f6", // Blue
  "#eab308", // Yellow
  "#f97316"  // Orange
];

const eventFaultTypes: Record<number, string> = {
  1: "Nitrogen loop pressure drop",
  2: "Brief nitrogen flow dip",
  3: "Minor heater temperature drop",
  4: "B-4601 Blower primary motor failure",
  5: "Decanter A torque peak trip",
  6: "Decanter B lubrication fault",
  7: "Decanter C temporary current surge",
  8: "Decanter A extended mechanical blockage",
  9: "Decanter D motor winding thermal overload",
  10: "Scrubber tower foam carryover",
  11: "Scrubber secondary tray packing collapse",
  12: "C-4601 liquid seal blow-out",
  13: "Liquid block in scrubber column",
  14: "B-4602 secondary blower trip",
  15: "B-4601 minor speed fluctuation",
  16: "Heater loop relay failure",
  17: "Scrubber packing blockage shutdown",
  18: "Decanter B brief overload",
  19: "B-4601 mechanical bearing failure"
};

export const TelemetryExplorer: React.FC<TelemetryExplorerProps> = ({
  theme,
  localShutdownEvents,
  localColumnStats,
  localMetadata,
  selectedShutdownEventId,
  setSelectedShutdownEventId,
  selectedSensors,
  setSelectedSensors,
  activeTelemetryDataset,
  loadTelemetryForEvent,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const chartInstanceRef = useRef<Chart | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const getThemeColor = (variableName: string, fallback: string) => {
    const val = window.getComputedStyle(document.body).getPropertyValue(variableName).trim();
    return val || fallback;
  };

  // Rebuild chart when dataset, selected sensors, or theme changes
  useEffect(() => {
    if (!canvasRef.current || activeTelemetryDataset.length === 0) return;

    const ctx = canvasRef.current.getContext("2d");
    if (!ctx) return;

    if (chartInstanceRef.current) {
      chartInstanceRef.current.destroy();
    }

    const labels = activeTelemetryDataset.map((row) => row.Timestamp.split(" ")[1]);

    const datasets = selectedSensors.map((sensor, idx) => {
      return {
        label: sensor,
        data: activeTelemetryDataset.map((row) => parseFloat(row[sensor])),
        borderColor: seriesColors[idx % seriesColors.length],
        backgroundColor: "transparent",
        borderWidth: 2,
        pointRadius: 0,
        yAxisID: `y-${idx}`,
      };
    });

    const yAxes: any = {};
    selectedSensors.forEach((sensor, idx) => {
      yAxes[`y-${idx}`] = {
        type: "linear",
        display: idx === 0,
        position: idx % 2 === 0 ? "left" : "right",
        title: {
          display: true,
          text: `${sensor} (${localMetadata[sensor]?.unit || ""})`,
          color: seriesColors[idx % seriesColors.length],
          font: { family: "Outfit", size: 10, weight: 600 },
        },
        grid: {
          drawOnChartArea: idx === 0,
          color: getThemeColor("--border-color", "rgba(255,255,255,0.03)"),
        },
        ticks: {
          color: getThemeColor("--text-muted", "rgba(255,255,255,0.6)"),
          font: { size: 10 },
        },
      };
    });

    chartInstanceRef.current = new Chart(ctx, {
      type: "line",
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: {
            position: "top",
            labels: {
              color: getThemeColor("--text-main", "rgba(255,255,255,0.8)"),
              font: { family: "Outfit", size: 11 },
            },
          },
          tooltip: {
            backgroundColor: getThemeColor("--bg-darker", "rgba(11,17,32,0.95)"),
            borderColor: getThemeColor("--border-color", "rgba(255,255,255,0.1)"),
            borderWidth: 1,
            bodyFont: { family: "Inter" },
          },
        },
        scales: {
          x: {
            grid: {
              color: getThemeColor("--border-color", "rgba(255,255,255,0.02)"),
            },
            ticks: {
              color: getThemeColor("--text-muted", "rgba(255,255,255,0.6)"),
              font: { size: 10 },
            },
          },
          ...yAxes,
        },
      },
    });

    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
      }
    };
  }, [activeTelemetryDataset, selectedSensors, theme]);

  const handleSensorToggle = (sensor: string) => {
    if (selectedSensors.includes(sensor)) {
      setSelectedSensors(selectedSensors.filter((s) => s !== sensor));
    } else {
      setSelectedSensors([...selectedSensors, sensor]);
    }
  };

  const columns = Object.keys(localMetadata).filter((c) => c !== "Production Grade");
  const filteredColumns = columns.filter((col) =>
    col.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const activeEvent = localShutdownEvents.find(
    (e) => e.event_id === selectedShutdownEventId
  );

  return (
    <div className="explorer-grid">
      {/* Left Control Panel */}
      <div className="control-panel">
        {/* Shutdown events */}
        <div className="panel-section">
          <h3>
            <i className="fa-solid fa-triangle-exclamation"></i> Select Shutdown Event
          </h3>
          <p className="section-desc">Select a historical production trip to load corresponding telemetry.</p>
          <div className="shutdown-list-container">
            {localShutdownEvents.map((evt) => {
              const faultName = eventFaultTypes[evt.event_id] || "Process anomaly shutdown";
              const isActive = evt.event_id === selectedShutdownEventId;
              return (
                <div
                  key={evt.event_id}
                  className={`shutdown-item ${isActive ? "active" : ""}`}
                  onClick={() => {
                    setSelectedShutdownEventId(evt.event_id);
                    loadTelemetryForEvent(evt.event_id);
                  }}
                >
                  <div className="shutdown-time">
                    Event #{evt.event_id}: {evt.start.split(" ")[0]}
                  </div>
                  <div className="shutdown-dur">
                    <span>{faultName}</span>
                    <span>{evt.duration_hours} hrs</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Sensor selector */}
        <div className="panel-section separator">
          <h3>
            <i className="fa-solid fa-list-check"></i> Select Variables
          </h3>
          <p className="section-desc">Overlay up to 4 sensors to evaluate correlations.</p>
          <div className="sensor-search-box">
            <i className="fa-solid fa-magnifying-glass"></i>
            <input
              type="text"
              id="sensor-search"
              placeholder="Search variable tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="sensor-list-container">
            <div className="sensor-checkboxes-list">
              {filteredColumns.map((col, idx) => {
                const isChecked = selectedSensors.includes(col);
                const colorIndex = selectedSensors.indexOf(col);
                const borderStyle = isChecked
                  ? { backgroundColor: seriesColors[colorIndex % seriesColors.length] }
                  : { backgroundColor: "#374151" };
                return (
                  <label
                    key={idx}
                    className="sensor-check-item"
                    style={{ display: "flex" }}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => handleSensorToggle(col)}
                    />
                    <span className="sensor-color-dot" style={borderStyle}></span>
                    <span className="sensor-lbl-text">{col}</span>
                  </label>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Right Trend Chart View */}
      <div className="chart-panel">
        <div className="chart-header">
          <div>
            <span className="chart-main-title">Telemetry Multivariable Trend</span>
            <span className="chart-time-range" id="chart-range-label">
              {activeEvent
                ? `Event #${selectedShutdownEventId} Window: ${activeEvent.start} to ${activeEvent.end}`
                : ""}
            </span>
          </div>
          <button
            className="btn btn-secondary btn-sm"
            id="reset-chart-btn"
            onClick={() => loadTelemetryForEvent(1)}
          >
            <i className="fa-solid fa-arrows-rotate"></i> Reset Event
          </button>
        </div>

        <div className="chart-wrapper">
          <canvas ref={canvasRef} id="telemetry-chart"></canvas>
        </div>

        {/* Process Metrics Overview */}
        <div className="panel-section">
          <h3>
            <i className="fa-solid fa-square-poll-vertical"></i> Process Metrics
          </h3>
          <div className="stats-overview-grid" id="stats-overview">
            {selectedSensors.map((sensor) => {
              const meta = localMetadata[sensor];
              if (!meta) return null;
              const stats = localColumnStats[sensor] || { mean: 0 };
              const lastRow = activeTelemetryDataset[activeTelemetryDataset.length - 1];
              const currentVal = lastRow ? parseFloat(lastRow[sensor]).toFixed(2) : "0.00";

              return (
                <div key={sensor} className="stat-card">
                  <div className="stat-card-title">{sensor}</div>
                  <div className="stat-card-val">
                    {currentVal}{" "}
                    <span style={{ fontSize: "10px", fontWeight: "normal", color: "var(--text-muted)" }}>
                      {meta.unit}
                    </span>
                  </div>
                  <div className="stat-card-limits">
                    <span>Limit: {meta.range}</span>
                    <span>Mean: {stats.mean.toFixed(1)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
