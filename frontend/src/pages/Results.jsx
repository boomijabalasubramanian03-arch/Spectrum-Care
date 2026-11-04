import { useEffect, useState, useCallback, useMemo } from "react";
import { useParams, Link } from "react-router-dom";
import { getAnalysis, downloadReport } from "../api/analysis.js";
import Sidebar from "../components/Sidebar.jsx";
import SplitViewSlider from "../components/SplitViewSlider.jsx";
import WardrobeContrastAdvisor from "../components/WardrobeContrastAdvisor.jsx";

const COLOR_DOT = {
  Red: "#c4553b", Orange: "#e8a33d", Yellow: "#d4b400", Green: "#2c6e71",
  Blue: "#3b82c4", Purple: "#7b4fa0", Pink: "#d4699b", Brown: "#8b4513",
  Black: "#1a1d23", White: "#d9d9d9", Gray: "#808080", Cyan: "#00a0a8",
  Maroon: "#800020", Navy: "#14205a", Olive: "#6e6e1e", Teal: "#008080",
  Gold: "#c8a43a", Beige: "#c9ad82", Silver: "#a6a6a6",
  "Red, Yellow & Green": "linear-gradient(135deg, #c4553b 0%, #d4b400 50%, #2c6e71 100%)",
};

const COLOR_DATALIST_OPTIONS = [
  "Red", "Orange", "Yellow", "Green", "Blue", "Cyan",
  "Purple", "Pink", "Brown", "Black", "White", "Gray", "Teal", "Beige"
];

export default function Results() {
  const { anaId } = useParams();
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState("");
  const [speaking, setSpeaking] = useState(false);
  const [reportBusy, setReportBusy] = useState("");
  const [viewMode, setViewMode] = useState("slider"); // 'slider', 'annotated'
  const [filterQuery, setFilterQuery] = useState("");

  useEffect(() => {
    let cancelled = false;
    getAnalysis(anaId)
      .then((data) => { if (!cancelled) setAnalysis(data); })
      .catch((err) => { if (!cancelled) setError(err.message); });
    return () => { cancelled = true; };
  }, [anaId]);

  const sceneText = analysis?.scenes?.[0]?.text || "";

  // Accessibility > Voice Assistance (Web Speech API)
  const speak = useCallback(() => {
    if (!sceneText || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(sceneText);
    utterance.rate = 0.95;
    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(utterance);
  }, [sceneText]);

  async function handleReport(fmt) {
    setReportBusy(fmt);
    try {
      await downloadReport(anaId, fmt);
    } catch (err) {
      setError(err.message);
    } finally {
      setReportBusy("");
    }
  }

  // Filtered detections based on datalist search
  const filteredDetections = useMemo(() => {
    if (!analysis?.detections) return [];
    if (!filterQuery.trim()) return analysis.detections;
    const q = filterQuery.toLowerCase();
    return analysis.detections.filter(
      (d) => d.label.toLowerCase().includes(q) || d.color.toLowerCase().includes(q)
    );
  }, [analysis, filterQuery]);

  if (error) {
    return (
      <div className="app-shell">
        <Sidebar />
        <main className="results-main-wide">
          <div className="alert alert-danger" role="alert">{error}</div>
        </main>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="app-shell">
        <Sidebar />
        <main className="results-main-wide">
          <div className="d-flex align-items-center gap-2 p-4">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Loading…</span>
            </div>
            <span>Loading analysis…</span>
          </div>
        </main>
      </div>
    );
  }

  if (analysis.status === "error") {
    return (
      <div className="app-shell">
        <Sidebar />
        <main className="results-main-wide">
          <div className="app-main__inner">
            <div className="alert alert-warning" role="alert">
              This analysis failed: {analysis.err_msg || "unknown error"}
            </div>
            <Link to="/upload" className="results-back-link">← Try another image</Link>
          </div>
        </main>
      </div>
    );
  }

  const primaryImage = analysis.annotated_url || analysis.img_url;
  const cvdImage = analysis.cvd_url || analysis.img_url;
  const currentCvdType = analysis.cvd_type || "Deuteranopia";

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="results-main-wide">
        <div className="page-header d-flex justify-content-between align-items-center flex-wrap gap-2">
          <div>
            <p className="app-main__eyebrow">Interactive Vision Suite · Results</p>
            <h2 className="results-title">Analysis &amp; Assistive Controls</h2>
          </div>
          <Link to="/upload" className="btn-ghost" style={{ width: "auto" }}>
            ← Analyse another image
          </Link>
        </div>

        <div className="results-grid">
          {/* Left Column: Visual Viewport */}
          <div className="results-left-col">
            <div className="results-image-panel">
              {/* Mode Switcher Tabs */}
              <div className="view-mode-tabs mb-2">
                <button
                  type="button"
                  className={`view-mode-tab ${viewMode === "slider" ? "view-mode-tab--active" : ""}`}
                  onClick={() => setViewMode("slider")}
                >
                  ↔ Split View Comparison
                </button>
                <button
                  type="button"
                  className={`view-mode-tab ${viewMode === "annotated" ? "view-mode-tab--active" : ""}`}
                  onClick={() => setViewMode("annotated")}
                >
                  🎯 AI Detections View
                </button>
              </div>

              {/* Viewport 1: Split Screen Slider */}
              {viewMode === "slider" && (
                <SplitViewSlider
                  originalUrl={primaryImage}
                  cvdUrl={cvdImage}
                  cvdType={currentCvdType}
                />
              )}

              {/* Viewport 2: Direct AI Annotated Box View */}
              {viewMode === "annotated" && (
                <div className="annotated-view-box">
                  <img
                    src={primaryImage}
                    alt="AI-annotated image with detected objects"
                    className="results-image"
                  />
                  <p className="small text-secondary mt-2 mb-0 text-center">
                    Objects are outlined and labelled by colour and position.
                  </p>
                </div>
              )}
            </div>

            {/* Extracted Swatches Visualizer */}
            {analysis.detections.length > 0 && (
              <div className="dash-card">
                <h4 className="dash-card__title fs-6 mb-2">🎨 Colour Swatches</h4>
                <div className="swatch-strip">
                  {analysis.detections.map((d, i) => (
                    <div key={i} className="swatch-card" title={`${d.color} ${d.label}`}>
                      <div
                        className="swatch-card__color"
                        style={{ background: COLOR_DOT[d.color] || d.hex || "#999" }}
                      />
                      <span className="swatch-card__name">{d.color}</span>
                      <span className="swatch-card__obj">{d.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Audio Scene, Chip List, Structured Table, CVD Guidance */}
          <div className="results-side">
            {/* Audio Scene Description Card */}
            <section className="results-section audio-scene-card">
              <div className="d-flex justify-content-between align-items-center mb-2">
                <h3 className="mb-0">🔊 Voice Assistant &amp; Scene Audio</h3>
                <span className="badge bg-primary-subtle text-primary-emphasis">Audio Assist</span>
              </div>
              <p className="results-scene-text">{sceneText}</p>
              <button className="btn-primary read-aloud-btn" type="button" onClick={speak} disabled={speaking}>
                {speaking ? "Speaking scene aloud…" : "🔊 Read Scene Description Aloud"}
              </button>
            </section>

            {/* Chip filter & list */}
            <section className="results-section">
              <div className="d-flex justify-content-between align-items-center mb-2">
                <h3 className="mb-0">Detected Objects ({analysis.det_count})</h3>
              </div>

              {analysis.detections.length > 2 && (
                <div className="mb-3">
                  <input
                    id="color-search-input"
                    list="color-datalist"
                    type="text"
                    className="form-control form-control-sm"
                    placeholder="Filter detections by color or object..."
                    value={filterQuery}
                    onChange={(e) => setFilterQuery(e.target.value)}
                    autoComplete="off"
                  />
                  <datalist id="color-datalist">
                    {COLOR_DATALIST_OPTIONS.map((c) => (
                      <option key={c} value={c} />
                    ))}
                  </datalist>
                </div>
              )}

              {filteredDetections.length === 0 && (
                <p className="results-empty">No objects match the current filter.</p>
              )}

              <ul className="detection-list">
                {filteredDetections.map((d) => (
                  <li key={d.det_no} className="detection-chip">
                    <span
                      className="detection-chip__dot"
                      style={{ background: COLOR_DOT[d.color] || d.hex || "#999" }}
                    />
                    <span className="detection-chip__label">
                      {d.color} {d.label} <small className="text-muted">({d.pos})</small>
                    </span>
                    <span className="detection-chip__meta">
                      {(d.conf * 100).toFixed(0)}%
                    </span>
                  </li>
                ))}
              </ul>
            </section>

            {/* Structured Table */}
            {analysis.detections.length > 0 && (
              <section className="results-section">
                <h3>Detection details</h3>
                <div className="table-responsive">
                  <table className="table table-sm table-hover table-striped table-bordered align-middle mb-0">
                    <thead className="table-dark">
                      <tr>
                        <th>#</th>
                        <th>Object</th>
                        <th>Color</th>
                        <th>Confidence</th>
                        <th>Position</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analysis.detections.map((d, idx) => (
                        <tr key={d.det_no || idx}>
                          <td>{idx + 1}</td>
                          <td className="fw-semibold">{d.label}</td>
                          <td>
                            <span
                              className="badge rounded-pill"
                              style={{
                                background: COLOR_DOT[d.color] || d.hex || "#2c6e71",
                                color: "#fff",
                                textShadow: "0 1px 2px rgba(0,0,0,0.4)"
                              }}
                            >
                              {d.color}
                            </span>
                          </td>
                          <td>
                            <div className="progress" style={{ height: "14px", minWidth: "60px" }}>
                              <div
                                className="progress-bar bg-success progress-bar-striped"
                                role="progressbar"
                                style={{ width: `${(d.conf * 100).toFixed(0)}%` }}
                                aria-valuenow={(d.conf * 100).toFixed(0)}
                                aria-valuemin="0"
                                aria-valuemax="100"
                              >
                                {(d.conf * 100).toFixed(0)}%
                              </div>
                            </div>
                          </td>
                          <td>
                            <code className="text-secondary small">{d.pos}</code>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            {/* CVD Accessibility Advice */}
            {analysis.color_results.length > 0 && (
              <section className="results-section cvd-guidance-card">
                <h3>Colour Accessibility Guidance ({analysis.cvd_type || "CVD"})</h3>
                <ul className="tip-list">
                  {analysis.color_results.map((c) => (
                    <li key={c.cr_id} className="tip">
                      <p>{c.reason}</p>
                      {c.contrast_ratio && (
                        <span className="detection-chip__meta">
                          WCAG contrast ratio: {c.contrast_ratio}:1
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {/* Wardrobe & Colour Confusion Advisor */}
            <WardrobeContrastAdvisor
              detections={analysis.detections}
              cvdType={currentCvdType}
            />

            {!analysis.cvd_url && (
              <p className="results-empty">
                Want results tailored to your colour vision?{" "}
                <Link to="/settings">Set your CVD profile</Link>.
              </p>
            )}

            {analysis.ocr_results.length > 0 && (
              <section className="results-section">
                <h3>Text found in image</h3>
                <p className="results-ocr-text">
                  {analysis.ocr_results.map((o) => o.text).join(" ")}
                </p>
              </section>
            )}

            {/* Export Toolbar */}
            <section className="results-section">
              <h3>Export Diagnostic Report</h3>
              <div className="report-buttons">
                {["json", "csv", "pdf"].map((fmt) => (
                  <button
                    key={fmt}
                    className="btn-ghost"
                    type="button"
                    disabled={reportBusy === fmt}
                    onClick={() => handleReport(fmt)}
                  >
                    {reportBusy === fmt ? "Generating…" : `Export ${fmt.toUpperCase()}`}
                  </button>
                ))}
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}
