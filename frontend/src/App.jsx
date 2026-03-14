import { useState, useEffect, useRef } from "react";
import Editor from "@monaco-editor/react";
import axios from "axios";
import toast, { Toaster } from "react-hot-toast";
import CytoscapeComponent from "react-cytoscapejs";
import {
  AlertTriangle, CheckCircle, Code2, GitBranch,
  Zap, FileCode, Brain, ChevronDown, ChevronUp
} from "lucide-react";

const API = "http://127.0.0.1:8000";

const SAMPLE_CODE = `# Sample Python code with dead code
import os
import sys

def calculate_sum(a, b):
    return a + b

def unused_helper(x):
    result = x * 2
    return result

def another_dead_function():
    temp = "never called"
    unused_var = 42
    return temp

def process_data(data):
    total = calculate_sum(len(data), 10)
    return total

result = process_data([1, 2, 3, 4, 5])
print(result)
`;

export default function App() {
  const [code, setCode] = useState(SAMPLE_CODE);
  const [language, setLanguage] = useState("python");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("issues");
  const [expandedItems, setExpandedItems] = useState({});
  const [wsStatus, setWsStatus] = useState("disconnected");
  const [liveIssues, setLiveIssues] = useState([]);
  const wsRef = useRef(null);
  const cyRef = useRef(null);
  const editorRef = useRef(null);
  const decorationsRef = useRef([]);

  useEffect(() => {
    connectWebSocket();
    return () => wsRef.current?.close();
  }, []);

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket("ws://127.0.0.1:8000/ws/analyze");
      wsRef.current = ws;
      ws.onopen = () => setWsStatus("connected");
      ws.onclose = () => {
        setWsStatus("disconnected");
        setTimeout(connectWebSocket, 3000);
      };
      ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.dead_code_items) setLiveIssues(data.dead_code_items);
      };
    } catch (e) {
      setWsStatus("disconnected");
    }
  };

  const sendToWebSocket = (code) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ code, language }));
    }
  };

  const handleCodeChange = (value) => {
    setCode(value || "");
    sendToWebSocket(value || "");
  };

  const handleEditorMount = (editor) => {
    editorRef.current = editor;
  };

  const highlightDeadLines = (items) => {
    if (!editorRef.current) return;
    const monaco = window.monaco;
    if (!monaco) return;

    const decorations = items.map((item) => ({
      range: new monaco.Range(item.line_start, 1, item.line_end, 1),
      options: {
        isWholeLine: true,
        className: "dead-code-line",
        glyphMarginClassName: "dead-code-glyph",
        overviewRuler: {
          color: item.severity === "high" ? "#ef4444" : "#f59e0b",
          position: 1,
        },
      },
    }));

    decorationsRef.current = editorRef.current.deltaDecorations(
      decorationsRef.current,
      decorations
    );
  };

  const analyzeCode = async () => {
    if (!code.trim()) return toast.error("Please enter some code first!");
    setLoading(true);
    setResult(null);
    try {
      const res = await axios.post(`${API}/api/analyze`, { code, language });
      setResult(res.data);
      setActiveTab("issues");
      highlightDeadLines(res.data.dead_code_items);
      if (res.data.dead_count === 0) {
        toast.success("No dead code found! Clean codebase!");
      } else {
        toast.error(`Found ${res.data.dead_count} dead code issues!`);
      }
    } catch (e) {
      toast.error("Analysis failed. Is the backend running?");
    }
    setLoading(false);
  };

  const exportPDF = async () => {
    const { jsPDF } = await import("jspdf");
    const doc = new jsPDF();

    doc.setFillColor(15, 17, 23);
    doc.rect(0, 0, 210, 297, "F");

    doc.setTextColor(129, 140, 248);
    doc.setFontSize(20);
    doc.setFont("helvetica", "bold");
    doc.text("Dead Code Detection Report", 20, 25);

    doc.setTextColor(107, 114, 128);
    doc.setFontSize(10);
    doc.text(`Generated: ${new Date().toLocaleString()}`, 20, 33);
    doc.text(`Language: ${language}`, 20, 39);

    doc.setDrawColor(45, 49, 72);
    doc.line(20, 43, 190, 43);

    doc.setTextColor(255, 255, 255);
    doc.setFontSize(13);
    doc.setFont("helvetica", "bold");
    doc.text("Summary", 20, 52);

    const stats = [
      ["Total Lines", result.total_lines],
      ["Dead Issues Found", result.dead_count],
      ["Dead Functions", result.summary.dead_functions],
      ["Dead Variables", result.summary.dead_variables],
      ["Unreachable Blocks", result.summary.unreachable_blocks],
      ["Functions Defined", result.defined_functions.length],
    ];

    stats.forEach(([label, value], i) => {
      const y = 62 + i * 10;
      doc.setFontSize(10);
      doc.setFont("helvetica", "normal");
      doc.setTextColor(156, 163, 175);
      doc.text(label, 25, y);
      doc.setTextColor(129, 140, 248);
      doc.setFont("helvetica", "bold");
      doc.text(String(value), 120, y);
    });

    doc.setDrawColor(45, 49, 72);
    doc.line(20, 128, 190, 128);

    doc.setTextColor(255, 255, 255);
    doc.setFontSize(13);
    doc.setFont("helvetica", "bold");
    doc.text("Dead Code Issues", 20, 138);

    let y = 148;
    result.dead_code_items.forEach((item, i) => {
      if (y > 260) {
        doc.addPage();
        doc.setFillColor(15, 17, 23);
        doc.rect(0, 0, 210, 297, "F");
        y = 20;
      }

      const color = item.severity === "high" ? [239, 68, 68] : [245, 158, 11];
      doc.setFillColor(...color);
      doc.roundedRect(20, y - 5, 170, 8, 2, 2, "F");

      doc.setTextColor(255, 255, 255);
      doc.setFontSize(9);
      doc.setFont("helvetica", "bold");
      doc.text(`${i + 1}. ${item.name} — Line ${item.line_start}`, 24, y);
      doc.setFont("helvetica", "normal");
      doc.text(`[${item.severity.toUpperCase()}]`, 170, y);
      y += 12;

      if (item.message) {
        doc.setTextColor(156, 163, 175);
        doc.setFontSize(8);
        const lines = doc.splitTextToSize(item.message, 165);
        doc.text(lines, 25, y);
        y += lines.length * 5 + 3;
      }

      if (item.ai_explanation) {
        doc.setTextColor(129, 140, 248);
        doc.setFontSize(8);
        doc.setFont("helvetica", "bold");
        doc.text("AI Explanation:", 25, y);
        y += 5;
        doc.setFont("helvetica", "normal");
        doc.setTextColor(156, 163, 175);
        const aiLines = doc.splitTextToSize(item.ai_explanation, 160);
        doc.text(aiLines, 25, y);
        y += aiLines.length * 5 + 4;
      }

      if (item.fix_suggestion) {
        doc.setTextColor(34, 197, 94);
        doc.setFontSize(8);
        doc.setFont("helvetica", "bold");
        doc.text("Fix Suggestion:", 25, y);
        y += 5;
        doc.setFont("helvetica", "normal");
        doc.setTextColor(156, 163, 175);
        const fixLines = doc.splitTextToSize(item.fix_suggestion, 160);
        doc.text(fixLines, 25, y);
        y += fixLines.length * 5 + 8;
      }
    });

    doc.save(`dead-code-report-${Date.now()}.pdf`);
    toast.success("PDF exported successfully!");
  };

  const toggleExpand = (i) => {
    setExpandedItems((prev) => ({ ...prev, [i]: !prev[i] }));
  };

  const getSeverityColor = (severity) => {
    if (severity === "high") return "#ef4444";
    if (severity === "medium") return "#f59e0b";
    return "#3b82f6";
  };

  const getTypeIcon = (type) => {
    if (type === "dead_function") return <Code2 size={14} />;
    if (type === "unreachable_code") return <AlertTriangle size={14} />;
    return <FileCode size={14} />;
  };

  const graphElements = result?.call_graph
    ? [
        ...result.call_graph.nodes.map((n) => ({
          data: { id: n.id, label: n.label, color: n.color, is_dead: n.is_dead },
        })),
        ...result.call_graph.edges.map((e) => ({
          data: { source: e.source, target: e.target },
        })),
      ]
    : [];

  const cytoscapeStylesheet = [
    {
      selector: "node",
      style: {
        label: "data(label)",
        backgroundColor: "data(color)",
        color: "#fff",
        fontSize: 11,
        fontWeight: "bold",
        textValign: "center",
        textHalign: "center",
        width: "label",
        height: 40,
        shape: "roundrectangle",
        textWrap: "none",
        paddingLeft: "14px",
        paddingRight: "14px",
        paddingTop: "10px",
        paddingBottom: "10px",
        borderWidth: 2,
        borderColor: "#ffffff44",
      },
    },
    {
      selector: "node:selected",
      style: { borderWidth: 3, borderColor: "#ffffff" },
    },
    {
      selector: "edge",
      style: {
        width: 2,
        lineColor: "#4f46e5",
        targetArrowColor: "#4f46e5",
        targetArrowShape: "triangle",
        curveStyle: "bezier",
        opacity: 0.9,
      },
    },
  ];

  useEffect(() => {
    if (activeTab === "graph" && cyRef.current) {
      setTimeout(() => {
        cyRef.current.layout({
          name: "breadthfirst",
          animate: true,
          padding: 40,
          directed: true,
          spacingFactor: 1.8,
          fit: true,
          circle: false,
        }).run();
        cyRef.current.fit(40);
      }, 100);
    }
  }, [activeTab, result]);

  const healthScore = result
    ? Math.max(0, Math.round(100 - (result.dead_count / Math.max(1, result.defined_functions.length)) * 100))
    : 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "#0f1117" }}>
      <Toaster position="top-right" />

      <style>{`
        .dead-code-line {
          background: rgba(239, 68, 68, 0.15) !important;
          border-left: 3px solid #ef4444 !important;
        }
        .dead-code-glyph {
          background: #ef4444;
          border-radius: 50%;
          width: 8px !important;
          height: 8px !important;
          margin-top: 6px;
        }
      `}</style>

      {/* Header */}
      <div style={{
        background: "#1a1d27",
        borderBottom: "1px solid #2d3148",
        padding: "12px 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexShrink: 0,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
            borderRadius: 10,
            padding: "6px 10px",
            display: "flex",
          }}>
            <Brain size={20} color="white" />
          </div>
          <div>
            <h1 style={{ fontSize: 18, fontWeight: 700, color: "#fff" }}>
              Dead Code Detector
            </h1>
            <p style={{ fontSize: 11, color: "#6b7280" }}>
              AI-Powered • Tree-sitter • LLM Analysis
            </p>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {/* Live status */}
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{
              width: 8, height: 8, borderRadius: "50%",
              background: wsStatus === "connected" ? "#22c55e" : "#ef4444",
            }} />
            <span style={{ fontSize: 12, color: "#9ca3af" }}>
              {wsStatus === "connected" ? "Live Analysis ON" : "Connecting..."}
            </span>
          </div>

          {/* Language */}
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            style={{
              background: "#252836", border: "1px solid #2d3148",
              color: "#e0e0e0", padding: "6px 12px", borderRadius: 8,
              fontSize: 13, cursor: "pointer",
            }}
          >
            <option value="python">Python</option>
            <option value="javascript">JavaScript</option>
          </select>

          {/* File Upload */}
          <label style={{
            background: "#252836", border: "1px solid #2d3148",
            color: "#e0e0e0", padding: "7px 14px", borderRadius: 8,
            fontSize: 13, cursor: "pointer", display: "flex",
            alignItems: "center", gap: 6,
          }}>
            <FileCode size={14} /> Upload .py
            <input
              type="file"
              accept=".py,.js,.ts"
              style={{ display: "none" }}
              onChange={(e) => {
                const file = e.target.files[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = (ev) => setCode(ev.target.result);
                reader.readAsText(file);
                toast.success(`Loaded: ${file.name}`);
              }}
            />
          </label>

          {/* Export PDF */}
          {result && (
            <button
              onClick={exportPDF}
              style={{
                background: "#252836", border: "1px solid #2d3148",
                color: "#e0e0e0", padding: "7px 14px", borderRadius: 8,
                fontSize: 13, cursor: "pointer", display: "flex",
                alignItems: "center", gap: 6,
              }}
            >
              📄 Export PDF
            </button>
          )}

          {/* Analyze */}
          <button
            onClick={analyzeCode}
            disabled={loading}
            style={{
              background: loading
                ? "#3730a3"
                : "linear-gradient(135deg, #6366f1, #8b5cf6)",
              color: "white", border: "none", padding: "8px 20px",
              borderRadius: 8, fontWeight: 600, fontSize: 14,
              cursor: loading ? "not-allowed" : "pointer",
              display: "flex", alignItems: "center", gap: 8,
            }}
          >
            <Zap size={16} />
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </div>
      </div>

      {/* Main */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>

        {/* Left — Editor */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", borderRight: "1px solid #2d3148" }}>
          <div style={{
            padding: "8px 16px", background: "#1a1d27",
            borderBottom: "1px solid #2d3148", display: "flex",
            alignItems: "center", justifyContent: "space-between", flexShrink: 0,
          }}>
            <span style={{ fontSize: 13, color: "#9ca3af", display: "flex", alignItems: "center", gap: 6 }}>
              <FileCode size={14} /> Code Editor
            </span>
            {liveIssues.length > 0 && (
              <span style={{
                background: "#ef444422", color: "#ef4444",
                padding: "2px 10px", borderRadius: 20, fontSize: 12,
              }}>
                ⚡ {liveIssues.length} live issues
              </span>
            )}
          </div>
          <div style={{ flex: 1, overflow: "hidden" }}>
            <Editor
              height="100%"
              language={language}
              value={code}
              onChange={handleCodeChange}
              onMount={handleEditorMount}
              theme="vs-dark"
              options={{
                fontSize: 14,
                minimap: { enabled: true },
                lineNumbers: "on",
                scrollBeyondLastLine: false,
                automaticLayout: true,
                padding: { top: 12 },
                glyphMargin: true,
              }}
            />
          </div>
        </div>

        {/* Right — Results */}
        <div style={{ width: 440, display: "flex", flexDirection: "column", background: "#13151f" }}>

          {/* Tabs */}
          <div style={{
            display: "flex", background: "#1a1d27",
            borderBottom: "1px solid #2d3148", flexShrink: 0,
          }}>
            {["issues", "graph", "summary"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  flex: 1, padding: "10px", border: "none",
                  background: activeTab === tab ? "#252836" : "transparent",
                  color: activeTab === tab ? "#818cf8" : "#6b7280",
                  borderBottom: activeTab === tab ? "2px solid #818cf8" : "2px solid transparent",
                  fontSize: 13, fontWeight: 600, cursor: "pointer",
                  textTransform: "capitalize", display: "flex",
                  alignItems: "center", justifyContent: "center", gap: 5,
                }}
              >
                {tab === "issues" && <AlertTriangle size={13} />}
                {tab === "graph" && <GitBranch size={13} />}
                {tab === "summary" && <CheckCircle size={13} />}
                {tab}
                {tab === "issues" && result && result.dead_count > 0 && (
                  <span style={{
                    background: "#ef4444", color: "#fff",
                    borderRadius: 20, fontSize: 10,
                    padding: "1px 6px", marginLeft: 2,
                  }}>
                    {result.dead_count}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Content */}
          <div style={{ flex: 1, overflow: "auto", padding: activeTab === "graph" ? 0 : 16 }}>

            {/* Empty state */}
            {!result && !loading && (
              <div style={{ textAlign: "center", marginTop: 60, color: "#4b5563", padding: 16 }}>
                <Brain size={48} style={{ margin: "0 auto 16px", opacity: 0.3 }} />
                <p style={{ fontSize: 15 }}>
                  Click <strong style={{ color: "#818cf8" }}>Analyze</strong> to detect dead code
                </p>
                <p style={{ fontSize: 12, marginTop: 8 }}>AI will explain each issue found</p>
              </div>
            )}

            {/* Loading */}
            {loading && (
              <div style={{ textAlign: "center", marginTop: 60, padding: 16 }}>
                <div style={{
                  width: 48, height: 48, border: "3px solid #2d3148",
                  borderTop: "3px solid #818cf8", borderRadius: "50%",
                  margin: "0 auto 16px", animation: "spin 1s linear infinite",
                }} />
                <p style={{ color: "#9ca3af" }}>AI is analyzing your code...</p>
                <p style={{ fontSize: 12, color: "#4b5563", marginTop: 6 }}>
                  This may take a few seconds
                </p>
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
              </div>
            )}

            {/* Issues Tab */}
            {result && activeTab === "issues" && (
              <div>
                {result.dead_code_items.length === 0 ? (
                  <div style={{ textAlign: "center", marginTop: 40 }}>
                    <CheckCircle size={48} color="#22c55e" style={{ margin: "0 auto 12px" }} />
                    <p style={{ color: "#22c55e", fontWeight: 600 }}>No dead code found!</p>
                    <p style={{ color: "#6b7280", fontSize: 12, marginTop: 6 }}>
                      Your codebase is clean
                    </p>
                  </div>
                ) : (
                  result.dead_code_items.map((item, i) => (
                    <div
                      key={i}
                      style={{
                        background: "#1a1d27", borderRadius: 10, marginBottom: 10,
                        border: `1px solid ${getSeverityColor(item.severity)}33`,
                        overflow: "hidden",
                      }}
                    >
                      <div
                        onClick={() => toggleExpand(i)}
                        style={{
                          padding: "10px 14px", cursor: "pointer",
                          display: "flex", alignItems: "center",
                          justifyContent: "space-between",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <span style={{ color: getSeverityColor(item.severity) }}>
                            {getTypeIcon(item.type)}
                          </span>
                          <div>
                            <p style={{ fontSize: 13, fontWeight: 600, color: "#e0e0e0" }}>
                              {item.name}
                            </p>
                            <p style={{ fontSize: 11, color: "#6b7280" }}>
                              Line {item.line_start}
                              {item.line_end !== item.line_start && `–${item.line_end}`}
                              {" • "}
                              <span style={{ color: getSeverityColor(item.severity) }}>
                                {item.severity}
                              </span>
                              {" • "}
                              {item.type.replace(/_/g, " ")}
                            </p>
                          </div>
                        </div>
                        {expandedItems[i]
                          ? <ChevronUp size={14} color="#6b7280" />
                          : <ChevronDown size={14} color="#6b7280" />}
                      </div>

                      {expandedItems[i] && (
                        <div style={{ padding: "0 14px 14px", borderTop: "1px solid #2d3148" }}>
                          <p style={{ fontSize: 12, color: "#9ca3af", marginTop: 10, lineHeight: 1.5 }}>
                            {item.message}
                          </p>
                          {item.ai_explanation && (
                            <div style={{
                              background: "#0f1117", borderRadius: 8, padding: 10,
                              marginTop: 10, borderLeft: "3px solid #818cf8",
                            }}>
                              <p style={{ fontSize: 11, color: "#818cf8", fontWeight: 600, marginBottom: 4 }}>
                                🤖 AI Explanation
                              </p>
                              <p style={{ fontSize: 12, color: "#9ca3af", lineHeight: 1.6 }}>
                                {item.ai_explanation}
                              </p>
                            </div>
                          )}
                          {item.fix_suggestion && (
                            <div style={{
                              background: "#0f1117", borderRadius: 8, padding: 10,
                              marginTop: 8, borderLeft: "3px solid #22c55e",
                            }}>
                              <p style={{ fontSize: 11, color: "#22c55e", fontWeight: 600, marginBottom: 4 }}>
                                ✅ Fix Suggestion
                              </p>
                              <p style={{ fontSize: 12, color: "#9ca3af", lineHeight: 1.6 }}>
                                {item.fix_suggestion}
                              </p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}

            {/* Graph Tab */}
            {result && activeTab === "graph" && (
              <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
                <div style={{
                  padding: "8px 16px", display: "flex", gap: 16,
                  alignItems: "center", background: "#1a1d27",
                  borderBottom: "1px solid #2d3148", flexShrink: 0,
                }}>
                  {[
                    { color: "#E53935", label: "Dead function" },
                    { color: "#1E88E5", label: "Active function" },
                    { color: "#4CAF50", label: "Entry point" },
                  ].map((item) => (
                    <span key={item.label} style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12, color: "#9ca3af" }}>
                      <span style={{
                        width: 10, height: 10, borderRadius: 3,
                        background: item.color, display: "inline-block",
                      }} />
                      {item.label}
                    </span>
                  ))}
                </div>
                <div style={{ flex: 1, position: "relative" }}>
                  {graphElements.length > 0 ? (
                    <CytoscapeComponent
                      elements={graphElements}
                      stylesheet={cytoscapeStylesheet}
                      layout={{
                        name: "breadthfirst",
                        animate: true,
                        padding: 40,
                        directed: true,
                        spacingFactor: 1.8,
                        fit: true,
                        circle: false,
                      }}
                      style={{ width: "100%", height: "100%" }}
                      cy={(cy) => { cyRef.current = cy; }}
                      zoomingEnabled={true}
                      userZoomingEnabled={true}
                      panningEnabled={true}
                      userPanningEnabled={true}
                      boxSelectionEnabled={false}
                    />
                  ) : (
                    <div style={{ textAlign: "center", marginTop: 80, color: "#4b5563" }}>
                      <GitBranch size={40} style={{ margin: "0 auto 12px", opacity: 0.3 }} />
                      <p>No functions found to graph</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Summary Tab */}
            {result && activeTab === "summary" && (
              <div>
                {[
                  { label: "Total Lines", value: result.total_lines, color: "#818cf8" },
                  { label: "Dead Issues Found", value: result.dead_count, color: "#ef4444" },
                  { label: "Dead Functions", value: result.summary.dead_functions, color: "#f59e0b" },
                  { label: "Dead Variables", value: result.summary.dead_variables, color: "#f59e0b" },
                  { label: "Unreachable Blocks", value: result.summary.unreachable_blocks, color: "#ef4444" },
                  { label: "Functions Defined", value: result.defined_functions.length, color: "#22c55e" },
                ].map((stat, i) => (
                  <div
                    key={i}
                    style={{
                      background: "#1a1d27", borderRadius: 10, padding: "12px 16px",
                      marginBottom: 8, display: "flex", justifyContent: "space-between",
                      alignItems: "center", border: "1px solid #2d3148",
                    }}
                  >
                    <span style={{ fontSize: 13, color: "#9ca3af" }}>{stat.label}</span>
                    <span style={{ fontSize: 22, fontWeight: 700, color: stat.color }}>
                      {stat.value}
                    </span>
                  </div>
                ))}

                <div style={{
                  background: "#1a1d27", borderRadius: 10, padding: 14,
                  marginTop: 8, border: "1px solid #2d3148",
                }}>
                  <p style={{ fontSize: 12, color: "#6b7280", marginBottom: 8 }}>
                    Functions Defined
                  </p>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {result.defined_functions.map((fn, i) => (
                      <span
                        key={i}
                        style={{
                          background: "#252836", color: "#818cf8",
                          padding: "3px 10px", borderRadius: 20, fontSize: 12,
                        }}
                      >
                        {fn}()
                      </span>
                    ))}
                  </div>
                </div>

                <div style={{
                  background: "#1a1d27", borderRadius: 10, padding: 14,
                  marginTop: 8, border: "1px solid #2d3148",
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                    <p style={{ fontSize: 12, color: "#6b7280" }}>Code Health Score</p>
                    <span style={{
                      fontSize: 12, fontWeight: 700,
                      color: healthScore > 70 ? "#22c55e" : healthScore > 40 ? "#f59e0b" : "#ef4444",
                    }}>
                      {healthScore}%
                    </span>
                  </div>
                  <div style={{
                    height: 8, background: "#2d3148",
                    borderRadius: 4, overflow: "hidden",
                  }}>
                    <div style={{
                      height: "100%",
                      width: `${healthScore}%`,
                      background: healthScore > 70
                        ? "linear-gradient(90deg, #16a34a, #22c55e)"
                        : healthScore > 40
                        ? "linear-gradient(90deg, #d97706, #f59e0b)"
                        : "linear-gradient(90deg, #dc2626, #ef4444)",
                      borderRadius: 4,
                      transition: "width 1s ease",
                    }} />
                  </div>
                  <p style={{ fontSize: 11, color: "#4b5563", marginTop: 6 }}>
                    {healthScore > 70
                      ? "Great job! Minimal dead code."
                      : healthScore > 40
                      ? "Some cleanup needed."
                      : "Significant dead code detected."}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}