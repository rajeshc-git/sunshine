import React, { useState, useEffect } from "react";
import { Sidebar } from "./components/Sidebar";
import { Header } from "./components/Header";
import { TelemetryExplorer } from "./components/TelemetryExplorer";
import { CausalTopology } from "./components/CausalTopology";
import { RCADiagnostics } from "./components/RCADiagnostics";
import { NNSandbox } from "./components/NNSandbox";
import { ModelTrainingCenter } from "./components/ModelTrainingCenter";

// Global cache safely loaded from index.html scripts
const getWindowConstant = (key: string, fallback: any) => {
  return (window as any)[key] !== undefined ? (window as any)[key] : fallback;
};

const defaultMetadata = getWindowConstant("METADATA", {});
const defaultShutdownEvents = getWindowConstant("SHUTDOWN_EVENTS", []);
const defaultColumnStats = getWindowConstant("COLUMN_STATS", {});
const defaultCausalGraph = getWindowConstant("CAUSAL_GRAPH", { nodes: [], links: [] });
const defaultModelWeights = getWindowConstant("MODEL_WEIGHTS", { features: [], classes: [], weights: {}, bias: {}, history: { loss: [], accuracy: [] } });

export default function App() {
  const [activeTab, setActiveTab] = useState("explorer");
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [isBackendOnline, setIsBackendOnline] = useState(false);
  const apiBaseUrl = "http://127.0.0.1:2026";

  // Data cache
  const [metadata, setMetadata] = useState<any>(defaultMetadata);
  const [shutdownEvents, setShutdownEvents] = useState<any[]>(defaultShutdownEvents);
  const [columnStats, setColumnStats] = useState<any>(defaultColumnStats);
  const [causalGraph, setCausalGraph] = useState<any>(defaultCausalGraph);
  const [modelWeights, setModelWeights] = useState<any>(defaultModelWeights);
  const [activeTelemetryDataset, setActiveTelemetryDataset] = useState<any[]>([]);

  // Selection states
  const [selectedShutdownEventId, setSelectedShutdownEventId] = useState<number>(1);
  const [selectedSensors, setSelectedSensors] = useState<string[]>([
    "Plant Load",
    "Hot N2 Flow",
    "FBD Bed Temperature  at 14th Panel",
  ]);

  // Plant status states
  const [plantStatus, setPlantStatus] = useState("Normal");
  const [isPlantShutdown, setIsPlantShutdown] = useState(false);

  // Initialize theme preference from localStorage on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "light") {
      setTheme("light");
    } else {
      setTheme("dark");
    }
    checkBackendStatus();
  }, []);

  const checkBackendStatus = async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/status`);
      if (res.ok) {
        setIsBackendOnline(true);
        console.log("Connected to FastAPI backend.");
        fetchEnterpriseData();
      } else {
        throw new Error("Backend offline");
      }
    } catch (e) {
      console.log("FastAPI offline. Fallback client-side cache active.");
      setIsBackendOnline(false);
      initializeFallbackData();
    }
  };

  const fetchEnterpriseData = async () => {
    try {
      const [metaRes, eventsRes, statsRes, graphRes, weightsRes] = await Promise.all([
        fetch(`${apiBaseUrl}/api/metadata`),
        fetch(`${apiBaseUrl}/api/events`),
        fetch(`${apiBaseUrl}/api/column_stats`),
        fetch(`${apiBaseUrl}/api/causal_graph`),
        fetch(`${apiBaseUrl}/api/model_weights`),
      ]);

      const meta = await metaRes.json();
      const events = await eventsRes.json();
      const stats = await statsRes.json();
      const graph = await graphRes.json();
      const weights = await weightsRes.json();

      setMetadata(meta);
      setShutdownEvents(events);
      setColumnStats(stats);
      setCausalGraph(graph);
      setModelWeights(weights);

      // Trigger initial telemetry load
      loadTelemetry(1, events, meta, stats, true);
    } catch (e) {
      console.error("Error fetching data from API endpoints:", e);
      initializeFallbackData();
    }
  };

  const initializeFallbackData = () => {
    setMetadata(defaultMetadata);
    setShutdownEvents(defaultShutdownEvents);
    setColumnStats(defaultColumnStats);
    setCausalGraph(defaultCausalGraph);
    setModelWeights(defaultModelWeights);
    loadTelemetry(1, defaultShutdownEvents, defaultMetadata, defaultColumnStats, false);
  };

  const loadTelemetry = async (
    eventId: number,
    eventsList: any[],
    metaList: any,
    statsList: any,
    apiMode: boolean
  ) => {
    const evt = eventsList.find((e) => e.event_id === eventId);
    if (!evt) return;

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

    const faultName = eventFaultTypes[eventId] || "Process anomaly shutdown";
    setPlantStatus(`Shutdown (${faultName})`);
    setIsPlantShutdown(true);

    if (apiMode) {
      try {
        const res = await fetch(`${apiBaseUrl}/api/telemetry?event_id=${eventId}`);
        if (res.ok) {
          const dataset = await res.json();
          setActiveTelemetryDataset(dataset);
          return;
        }
      } catch (e) {
        console.error("API error loading telemetry, running local simulator...", e);
      }
    }

    // Local simulation fallback
    const simulated = getSimulatedData(eventId, evt, metaList, statsList);
    setActiveTelemetryDataset(simulated);
  };

  const loadTelemetryForEvent = (eventId: number) => {
    loadTelemetry(eventId, shutdownEvents, metadata, columnStats, isBackendOnline);
  };

  // High-fidelity telemetry simulator
  const getSimulatedData = (eventId: number, evt: any, metaList: any, statsList: any) => {
    const eventFaultInfo: Record<number, { type: string; root: string }> = {
      1: { type: "nitrogen", root: "Hot N2 Flow" },
      2: { type: "nitrogen", root: "Hot N2 Flow" },
      3: { type: "nitrogen", root: "Hot N2 Flow" },
      4: { type: "blower", root: "FBD Blower  B-4601 Current (A)" },
      5: { type: "decanter", root: "Decanter A Current (A)" },
      6: { type: "decanter", root: "Decanter B Current (A)" },
      7: { type: "decanter", root: "Decanter C Current (A)" },
      8: { type: "decanter", root: "Decanter A Current (A)" },
      9: { type: "decanter", root: "Decanter D Current (A)" },
      10: { type: "scrubber", root: "C-4601 Diff. Pressure" },
      11: { type: "scrubber", root: "C-4601 Diff. Pressure" },
      12: { type: "scrubber", root: "C-4601 Diff. Pressure" },
      13: { type: "scrubber", root: "C-4601 Diff. Pressure" },
      14: { type: "blower", root: "FBD Blower  B-4602 Current (A)" },
      15: { type: "blower", root: "FBD Blower  B-4601 Current (A)" },
      16: { type: "nitrogen", root: "Hot N2 Flow" },
      17: { type: "scrubber", root: "C-4601 Diff. Pressure" },
      18: { type: "decanter", root: "Decanter B Current (A)" },
      19: { type: "blower", root: "FBD Blower  B-4601 Current (A)" }
    };

    const faultInfo = eventFaultInfo[eventId] || { type: "normal", root: "" };
    const faultType = faultInfo.type;
    const rootCauseNode = faultInfo.root;

    const durationMins = 120;
    const shutdownStartMin = 40;
    const shutdownDurMins = Math.round(evt.duration_hours * 60);

    const dataset = [];
    let baseTime = new Date(evt.start);
    baseTime.setMinutes(baseTime.getMinutes() - shutdownStartMin);

    const columns = Object.keys(metaList).filter((c) => c !== "Production Grade");

    for (let m = 0; m < durationMins; m++) {
      const currentTime = new Date(baseTime.getTime() + m * 60 * 1000);
      const timeStr = currentTime.toISOString().replace("T", " ").substring(0, 19);
      const row: any = { Timestamp: timeStr };

      const isFailing = m >= shutdownStartMin && m < shutdownStartMin + shutdownDurMins;
      const isRecovering = m >= shutdownStartMin + shutdownDurMins;

      columns.forEach((col) => {
        const stats = statsList[col] || { mean: 50, std: 5, min: 0, max: 100 };
        let limitLow = stats.min;
        let limitHigh = stats.max;

        const meta = metaList[col];
        if (meta?.range && meta.range !== "-") {
          const parts = meta.range.split("-");
          limitLow = parseFloat(parts[0].replace(",", ""));
          limitHigh = parseFloat(parts[1].replace(",", ""));
        }

        let val =
          stats.mean +
          Math.sin(m / 5) * 0.2 * stats.std +
          (Math.random() - 0.5) * 0.1 * stats.std;

        if (faultType === "nitrogen") {
          if (col === "Hot N2 Flow") {
            if (isFailing) val = limitLow - stats.std * 5 - Math.random() * stats.std;
          } else if (col.includes("FBD Bed Temperature") || col.includes("Hot N2 Temperature")) {
            if (isFailing) {
              const delay = col.includes("3rd Panel") ? 2 : col.includes("7th Panel") ? 5 : 10;
              if (m >= shutdownStartMin + delay) {
                val = limitLow - stats.std * 4 * ((m - shutdownStartMin - delay) / 30 + 0.1);
              }
            }
          } else if (col.includes("Off Gas Temperature")) {
            if (isFailing && m >= shutdownStartMin + 12) {
              val = limitLow - stats.std * 3;
            }
          } else if (col === "Plant Load") {
            if (isFailing && m >= shutdownStartMin + 15) {
              val = 0.0;
            }
          }
        } else if (faultType === "blower") {
          if (col === rootCauseNode) {
            if (isFailing) val = limitHigh + stats.std * 6 + Math.random() * stats.std;
          } else if (col === "1st stage  Bed Level" || col === "2nd stage  Bed Level") {
            if (isFailing && m >= shutdownStartMin + 4) {
              val = limitLow - stats.std * 4;
            }
          } else if (col === "L-1 Conveying Pressure") {
            if (isFailing && m >= shutdownStartMin + 2) {
              val = limitHigh + stats.std * 5;
            }
          } else if (col === "Plant Load") {
            if (isFailing && m >= shutdownStartMin + 8) {
              val = 0.0;
            }
          }
        } else if (faultType === "decanter") {
          if (col === rootCauseNode) {
            if (isFailing) val = limitHigh + stats.std * 5;
          } else if (col === "V-4607 Level") {
            if (isFailing && m >= shutdownStartMin + 5) {
              val = limitHigh + stats.std * 4;
            }
          } else if (col === "V-4607 Pressure") {
            if (isFailing && m >= shutdownStartMin + 8) {
              val = limitHigh + stats.std * 3;
            }
          } else if (col === "Plant Load") {
            if (isFailing && m >= shutdownStartMin + 12) {
              val = 0.0;
            }
          }
        } else if (faultType === "scrubber") {
          if (col === "C-4601 Diff. Pressure") {
            if (isFailing) val = limitHigh + stats.std * 5;
          } else if (col === "C-4601 Top Temperature") {
            if (isFailing && m >= shutdownStartMin + 4) {
              val = limitHigh + stats.std * 3;
            }
          } else if (col === "P-4614A/B Recovered Flow") {
            if (isFailing && m >= shutdownStartMin + 6) {
              val = limitLow - stats.std * 5;
            }
          } else if (col === "Plant Load") {
            if (isFailing && m >= shutdownStartMin + 10) {
              val = 0.0;
            }
          }
        }

        if (isRecovering) {
          if (col === "Plant Load") {
            val = stats.mean * 0.2;
          } else {
            val = (val + stats.mean) / 2;
          }
        }

        val = Math.max(stats.min * 0.5, Math.min(stats.max * 1.5, val));
        row[col] = val.toFixed(2);
      });
      dataset.push(row);
    }
    return dataset;
  };

  const renderActiveTabContent = () => {
    switch (activeTab) {
      case "explorer":
        return (
          <TelemetryExplorer
            theme={theme}
            localShutdownEvents={shutdownEvents}
            localColumnStats={columnStats}
            localMetadata={metadata}
            selectedShutdownEventId={selectedShutdownEventId}
            setSelectedShutdownEventId={setSelectedShutdownEventId}
            selectedSensors={selectedSensors}
            setSelectedSensors={setSelectedSensors}
            activeTelemetryDataset={activeTelemetryDataset}
            loadTelemetryForEvent={loadTelemetryForEvent}
          />
        );
      case "causal":
        return (
          <CausalTopology
            theme={theme}
            localCausalGraph={causalGraph}
            localColumnStats={columnStats}
            selectedSensors={selectedSensors}
            setSelectedSensors={setSelectedSensors}
          />
        );
      case "rca":
        return (
          <RCADiagnostics
            theme={theme}
            localShutdownEvents={shutdownEvents}
            localMetadata={metadata}
          />
        );
      case "network":
        return (
          <NNSandbox
            theme={theme}
            localModelWeights={modelWeights}
          />
        );
      case "train-center":
        return (
          <ModelTrainingCenter
            theme={theme}
            localModelWeights={modelWeights}
          />
        );
      default:
        return <div>Tab content not found.</div>;
    }
  };

  return (
    <div className="app-container">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isBackendOnline={isBackendOnline}
        metadataCount={Object.keys(metadata).length}
      />
      <main className="main-content">
        <Header
          activeTab={activeTab}
          theme={theme}
          setTheme={setTheme}
          plantStatus={plantStatus}
          isPlantShutdown={isPlantShutdown}
        />
        <div className="tab-container">{renderActiveTabContent()}</div>
      </main>
    </div>
  );
}
