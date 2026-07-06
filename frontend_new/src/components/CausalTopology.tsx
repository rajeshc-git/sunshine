import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";

interface CausalTopologyProps {
  theme: "dark" | "light";
  localCausalGraph: { nodes: any[]; links: any[] };
  localColumnStats: any;
  selectedSensors: string[];
  setSelectedSensors: (sensors: string[]) => void;
}

export const CausalTopology: React.FC<CausalTopologyProps> = ({
  theme,
  localCausalGraph,
  localColumnStats,
  selectedSensors,
  setSelectedSensors,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const simulationRef = useRef<d3.Simulation<any, undefined> | null>(null);

  const restartSimulation = () => {
    if (simulationRef.current) {
      simulationRef.current.alpha(1).restart();
    }
  };

  const getThemeColor = (variableName: string, fallback: string) => {
    const val = window.getComputedStyle(document.body).getPropertyValue(variableName).trim();
    return val || fallback;
  };

  useEffect(() => {
    if (!containerRef.current || !localCausalGraph.nodes.length) return;

    // Clear previous svg
    containerRef.current.innerHTML = "";

    const width = containerRef.current.clientWidth || 600;
    const height = containerRef.current.clientHeight || 450;

    const svg = d3
      .select(containerRef.current)
      .append("svg")
      .attr("width", width)
      .attr("height", height);

    // Arrowhead marker definition
    svg
      .append("defs")
      .append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 18)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "rgba(255, 255, 255, 0.4)");

    const graphNodes = JSON.parse(JSON.stringify(localCausalGraph.nodes));
    const graphLinks = JSON.parse(JSON.stringify(localCausalGraph.links));

    const simulation = d3
      .forceSimulation(graphNodes)
      .force("link", d3.forceLink(graphLinks).id((d: any) => d.id).distance(80))
      .force("charge", d3.forceManyBody().strength(-120))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(25));

    simulationRef.current = simulation;

    const link = svg
      .append("g")
      .selectAll("line")
      .data(graphLinks)
      .enter()
      .append("line")
      .attr("class", "link-line")
      .attr("stroke", "rgba(0, 240, 255, 0.25)")
      .attr("stroke-width", (d: any) =>
        Math.max(1, Math.min(5, Math.abs(d.weight) * 5))
      )
      .attr("marker-end", "url(#arrowhead)");

    const dragstarted = (event: any, d: any) => {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    };

    const dragged = (event: any, d: any) => {
      d.fx = event.x;
      d.fy = event.y;
    };

    const dragended = (event: any, d: any) => {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    };

    const node = svg
      .append("g")
      .selectAll("g")
      .data(graphNodes)
      .enter()
      .append("g")
      .attr("class", "node-group")
      .call(
        d3
          .drag<any, any>()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended)
      );

    const varColor = (nodeId: string) => {
      if (nodeId.includes("Blower")) return "#f59e0b";
      if (nodeId.includes("Temperature") || nodeId.includes("Flow")) return "#00f0ff";
      if (nodeId.includes("Scrubber") || nodeId.includes("Pressure")) return "#ff0055";
      return "#00f0ff";
    };

    const isSelected = (nodeId: string) => {
      return selectedNode && selectedNode.id === nodeId;
    };

    node
      .append("circle")
      .attr("r", 9)
      .attr("class", "node-circle")
      .attr("fill", (d: any) =>
        selectedSensors.includes(d.id) ? varColor(d.id) : "#1f2937"
      )
      .attr("stroke", (d: any) => (isSelected(d.id) ? varColor(d.id) : "rgba(255, 255, 255, 0.2)"))
      .attr("stroke-width", (d: any) => (isSelected(d.id) ? "3px" : "1.5px"));

    node
      .append("text")
      .attr("dx", 12)
      .attr("dy", 4)
      .attr("class", "node-label")
      .attr("fill", theme === "dark" ? "rgba(255, 255, 255, 0.8)" : "#1f2937")
      .text((d: any) =>
        d.label.length > 20 ? d.label.substring(0, 18) + "..." : d.label
      );

    node.on("click", (event: any, d: any) => {
      event.stopPropagation();
      setSelectedNode(d);
      node
        .selectAll("circle")
        .attr("stroke", (nd: any) =>
          nd.id === d.id ? varColor(nd.id) : "rgba(255, 255, 255, 0.2)"
        )
        .attr("stroke-width", (nd: any) => (nd.id === d.id ? "3px" : "1.5px"));
    });

    svg.on("click", () => {
      setSelectedNode(null);
      node.selectAll("circle").attr("stroke", "rgba(255, 255, 255, 0.2)").attr("stroke-width", "1.5px");
    });

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node.attr("transform", (d: any) => `translate(${d.x}, ${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [localCausalGraph, theme, selectedSensors, selectedNode]);

  const stats = selectedNode ? localColumnStats[selectedNode.id] || { min: 0, max: 0, mean: 0, std: 0 } : null;

  const parents = selectedNode
    ? localCausalGraph.links.filter((l) => l.target === selectedNode.id).map((l) => l.source)
    : [];
  const children = selectedNode
    ? localCausalGraph.links.filter((l) => l.source === selectedNode.id).map((l) => l.target)
    : [];

  return (
    <div className="causal-grid">
      {/* Graph Area */}
      <div className="graph-panel">
        <div className="graph-header">
          <div>
            <span className="graph-main-title">Interactive Causal Diagram</span>
            <span className="graph-desc">
              Force-directed graph of causal linkages. Nodes color-coded by process loop. Drag to rearrange nodes.
            </span>
          </div>
          <button
            className="btn btn-secondary btn-sm"
            id="btn-force-layout"
            onClick={restartSimulation}
          >
            <i className="fa-solid fa-arrows-spin"></i> Trigger Force Layout
          </button>
        </div>

        <div className="graph-container-wrapper" ref={containerRef} id="causal-graph-container">
          {/* Rendered by D3 */}
        </div>
      </div>

      {/* Causal Node Inspector Sidebar */}
      <div className="inspector-panel glass-card" id="node-inspector">
        {!selectedNode ? (
          <div className="empty-inspector-state">
            <i className="fa-solid fa-circle-info"></i>
            <h3>No Variable Selected</h3>
            <p>Click any node in the causal topology graph to inspect its parameters, parent causes, and child dependencies.</p>
          </div>
        ) : (
          <div className="inspector-content" id="inspector-details">
            <h3 id="inspect-node-name">{selectedNode.label}</h3>
            <span className="tag-badge" id="inspect-node-tag">
              {selectedNode.tag}
            </span>

            <div className="inspect-group">
              <label>Standard Bounds</label>
              <div className="inspect-val">
                <span id="inspect-node-range">{selectedNode.range}</span>{" "}
                <span id="inspect-node-unit" style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                  {selectedNode.unit}
                </span>
              </div>
            </div>

            <div className="inspect-group">
              <label>Dataset Statistics</label>
              <div className="inspect-stats-grid">
                <div className="stat-mini">
                  <span className="stat-mini-lbl">Min</span>
                  <span className="stat-mini-val" id="inspect-stat-min">
                    {stats.min.toFixed(2)}
                  </span>
                </div>
                <div className="stat-mini">
                  <span className="stat-mini-lbl">Max</span>
                  <span className="stat-mini-val" id="inspect-stat-max">
                    {stats.max.toFixed(2)}
                  </span>
                </div>
                <div className="stat-mini">
                  <span className="stat-mini-lbl">Mean</span>
                  <span className="stat-mini-val" id="inspect-stat-mean">
                    {stats.mean.toFixed(2)}
                  </span>
                </div>
                <div className="stat-mini">
                  <span className="stat-mini-lbl">Std Dev</span>
                  <span className="stat-mini-val" id="inspect-stat-std">
                    {stats.std.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            <div className="inspect-group">
              <label>Causal Parents (Drivers)</label>
              <div className="causal-connections-list">
                <ul id="inspect-node-parents">
                  {parents.length === 0 ? (
                    <li>None (Root Variable)</li>
                  ) : (
                    parents.map((p) => {
                      const parentNode = localCausalGraph.nodes.find((n) => n.id === p);
                      return (
                        <li key={p} onClick={() => setSelectedNode(parentNode)}>
                          {parentNode?.label || p}
                        </li>
                      );
                    })
                  )}
                </ul>
              </div>
            </div>

            <div className="inspect-group">
              <label>Causal Children (Effects)</label>
              <div className="causal-connections-list">
                <ul id="inspect-node-children">
                  {children.length === 0 ? (
                    <li>None (Leaf Output)</li>
                  ) : (
                    children.map((c) => {
                      const childNode = localCausalGraph.nodes.find((n) => n.id === c);
                      return (
                        <li key={c} onClick={() => setSelectedNode(childNode)}>
                          {childNode?.label || c}
                        </li>
                      );
                    })
                  )}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
