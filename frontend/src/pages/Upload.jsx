import { useRef, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { uploadImage } from "../api/analysis.js";
import Sidebar from "../components/Sidebar.jsx";
import CameraCapture from "../components/CameraCapture.jsx";

const ACCEPTED_TYPES = ["image/jpeg", "image/jpg", "image/png"];
const MAX_BYTES = 10 * 1024 * 1024;

export default function Upload() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [preview, setPreview] = useState(null);
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [cameraOpen, setCameraOpen] = useState(false);

  function validateAndSet(selected) {
    setError("");
    if (!selected) return;
    if (!ACCEPTED_TYPES.includes(selected.type)) {
      setError("Only JPG, JPEG and PNG images are supported.");
      return;
    }
    if (selected.size > MAX_BYTES) {
      setError("Image exceeds the 10MB size limit.");
      return;
    }
    setFile(selected);
    setPreview(URL.createObjectURL(selected));
  }

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    validateAndSet(e.dataTransfer.files?.[0]);
  }, []);

  async function handleAnalyze() {
    if (!file) return;
    setError("");
    setUploading(true);
    try {
      const result = await uploadImage(file);
      navigate(`/results/${result.ana_id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="app-shell">
      <Sidebar />

      <main className="upload-main-wide">
        <div className="page-header">
          <p className="app-main__eyebrow">Ingestion Pipeline · Image Upload</p>
          <h2>Analyse Scene &amp; Contextual Colours</h2>
          <p className="upload-sub">
            Upload any everyday photograph. The AI model detects objects, extracts localized CIELAB colors, evaluates CVD contrast conflicts, and synthesizes audio descriptions.
          </p>
        </div>

        {error && (
          <div className="alert" role="alert">
            <span className="alert__icon" aria-hidden="true">⚠</span>
            <span>{error}</span>
          </div>
        )}

        <div className="upload-grid-layout">
          {/* Main Dropzone & Input Panel */}
          <div className="upload-main-col">
            <div
              className={`dropzone dropzone--large${dragOver ? " dropzone--active" : ""}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
            >
              {preview ? (
                <div className="preview-container">
                  <img src={preview} alt="Selected preview" className="dropzone__preview" />
                  <div className="preview-meta">
                    <span className="file-name">{file?.name}</span>
                    <span className="file-size">({(file?.size / (1024 * 1024)).toFixed(2)} MB)</span>
                  </div>
                </div>
              ) : (
                <div className="dropzone-empty-state">
                  <span className="dropzone-icon">📥</span>
                  <p className="dropzone__title">Drag and drop an image file here</p>
                  <p className="dropzone__sub">Supports JPG, JPEG, and PNG formats up to 10MB</p>
                </div>
              )}
            </div>

            <div className="upload-actions">
              <button
                type="button"
                className="btn-ghost"
                onClick={() => fileInputRef.current?.click()}
              >
                📁 Browse local files
              </button>
              <button
                type="button"
                className="btn-ghost"
                onClick={() => setCameraOpen(true)}
              >
                📸 Capture via camera
              </button>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png"
              hidden
              onChange={(e) => validateAndSet(e.target.files?.[0])}
            />

            <button
              className="btn-primary btn-large-cta"
              type="button"
              disabled={!file || uploading}
              onClick={handleAnalyze}
            >
              {uploading ? (
                <span className="d-flex align-items-center justify-content-center gap-2">
                  <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true" />
                  Analysing scene &amp; colours…
                </span>
              ) : (
                "🚀 Start Full Accessibility Analysis"
              )}
            </button>
          </div>

          {/* Right Reference & Instructions Panel */}
          <div className="upload-side-col">
            <div className="info-card">
              <h4 className="info-card__title">💡 Analysis Tips for CVD Users</h4>
              <ul className="info-card__list">
                <li>
                  <strong>Good Lighting:</strong> Daylight photos yield higher color clustering accuracy in the CIELAB color space.
                </li>
                <li>
                  <strong>Multiple Objects:</strong> The system automatically extracts spatial positions (left, right, center, top, bottom).
                </li>
                <li>
                  <strong>Traffic Lights &amp; Signs:</strong> Dedicated multi-aspect analyzers distinguish active signals and advise position.
                </li>
                <li>
                  <strong>Natural Sound:</strong> Once processed, click "Read Aloud" to hear full audio synthesis.
                </li>
              </ul>
            </div>

            <div className="info-card info-card--accent">
              <h4 className="info-card__title">🛡️ Supported Formats</h4>
              <div className="tag-cloud">
                <span className="tech-badge">JPEG / JPG</span>
                <span className="tech-badge">PNG</span>
                <span className="tech-badge">&lt; 10 MB</span>
                <span className="tech-badge">YOLOv8s Ingestion</span>
              </div>
            </div>
          </div>
        </div>
      </main>

      {cameraOpen && (
        <CameraCapture
          onCapture={(capturedFile) => {
            validateAndSet(capturedFile);
            setCameraOpen(false);
          }}
          onClose={() => setCameraOpen(false)}
        />
      )}
    </div>
  );
}
