import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Sidebar from "../components/Sidebar.jsx";
import { resolveUrl } from "../api/http.js";
import {
  getAdminOverview,
  getAdminUsers,
  updateUserStatus,
  updateUserRole,
  getServicesStatus,
  getModelInfo,
  updateModelConfig,
  getAuditLogs,
  validateAnalysisTask,
} from "../api/admin.js";

export default function Admin() {
  const [activeTab, setActiveTab] = useState("tasks"); // 'tasks', 'users', 'models', 'services', 'overview'
  const [overview, setOverview] = useState(null);
  const [users, setUsers] = useState([]);
  const [services, setServices] = useState([]);
  const [modelInfo, setModelInfo] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  // Model parameters state
  const [confThreshold, setConfThreshold] = useState(0.45);
  const [iouThreshold, setIouThreshold] = useState(0.45);
  const [savingModel, setSavingModel] = useState(false);

  // Filters
  const [userSearch, setUserSearch] = useState("");
  const [taskFilter, setTaskFilter] = useState("all");

  function showToast(msg) {
    setToast(msg);
    setTimeout(() => setToast(""), 4000);
  }

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const [ovData, usersData, srvData, mdlData, logsData] = await Promise.all([
        getAdminOverview(),
        getAdminUsers(),
        getServicesStatus(),
        getModelInfo(),
        getAuditLogs(50),
      ]);
      setOverview(ovData);
      setUsers(usersData);
      setServices(srvData.services || []);
      setModelInfo(mdlData);
      setConfThreshold(mdlData.conf_threshold || 0.45);
      setIouThreshold(mdlData.iou_threshold || 0.45);
      setAuditLogs(logsData || []);
    } catch (err) {
      setError(err.message || "Failed to load administrative data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleToggleStatus(u) {
    const nextStatus = u.status === "active" ? "suspended" : "active";
    try {
      await updateUserStatus(u.user_id, nextStatus);
      setUsers((prev) =>
        prev.map((item) =>
          item.user_id === u.user_id ? { ...item, status: nextStatus } : item
        )
      );
      showToast(`User ${u.email} is now ${nextStatus}.`);
    } catch (err) {
      alert(err.message || "Failed to update status.");
    }
  }

  async function handleToggleRole(u) {
    const nextRole = u.role === "admin" ? "user" : "admin";
    if (
      !confirm(
        `Are you sure you want to change ${u.email}'s role to ${nextRole.toUpperCase()}?`
      )
    ) {
      return;
    }
    try {
      await updateUserRole(u.user_id, nextRole);
      setUsers((prev) =>
        prev.map((item) =>
          item.user_id === u.user_id ? { ...item, role: nextRole } : item
        )
      );
      showToast(`User ${u.email} role updated to ${nextRole}.`);
    } catch (err) {
      alert(err.message || "Failed to update role.");
    }
  }

  async function handleValidateTask(anaId, nextStatus) {
    try {
      await validateAnalysisTask(anaId, nextStatus);
      setAuditLogs((prev) =>
        prev.map((item) =>
          item.ana_id === anaId ? { ...item, status: nextStatus } : item
        )
      );
      showToast(`Analysis task marked as ${nextStatus.toUpperCase()}.`);
    } catch (err) {
      alert(err.message || "Failed to update task validation.");
    }
  }

  async function handleSaveModelConfig(e) {
    e.preventDefault();
    setSavingModel(true);
    try {
      const res = await updateModelConfig({
        conf_threshold: parseFloat(confThreshold),
        iou_threshold: parseFloat(iouThreshold),
      });
      setModelInfo(res.config);
      showToast("Detection threshold settings applied successfully.");
    } catch (err) {
      alert(err.message || "Failed to save configuration.");
    } finally {
      setSavingModel(false);
    }
  }

  const filteredUsers = users.filter((u) => {
    if (!userSearch.trim()) return true;
    const q = userSearch.toLowerCase();
    return (
      u.email.toLowerCase().includes(q) ||
      u.first_name.toLowerCase().includes(q) ||
      u.last_name.toLowerCase().includes(q) ||
      (u.cvd_type && u.cvd_type.toLowerCase().includes(q))
    );
  });

  const filteredTasks = auditLogs.filter((t) => {
    if (taskFilter === "all") return true;
    return t.status === taskFilter;
  });

  return (
    <div className="app-shell">
      <Sidebar />

      <main className="dash-main">
        {/* Admin Header */}
        <div className="dash-hero mb-4">
          <div>
            <div className="d-flex align-items-center gap-2 mb-1">
              <p className="app-main__eyebrow mb-0">Task Control · Administration Module</p>
              <span className="badge bg-success-subtle text-success-emphasis border border-success-subtle">
                Administrator
              </span>
            </div>
            <h2 className="dash-hero__title">Task Validation &amp; Management</h2>
            <p className="dash-hero__sub">
              Validate and review image analysis tasks, manage registered user accounts, and configure detection thresholds.
            </p>
          </div>
          <button
            type="button"
            className="btn-ghost"
            style={{ width: "auto" }}
            onClick={loadData}
            disabled={loading}
          >
            🔄 Refresh Tasks
          </button>
        </div>

        {toast && (
          <div className="alert alert-success d-flex align-items-center justify-content-between mb-3" role="alert">
            <span>✅ {toast}</span>
            <button type="button" className="btn-close" onClick={() => setToast("")} />
          </div>
        )}

        {error && (
          <div className="alert alert-danger" role="alert">
            ⚠️ {error}
          </div>
        )}

        {/* Tab Navigation */}
        <div className="view-mode-tabs mb-4">
          <button
            type="button"
            className={`view-mode-tab ${activeTab === "tasks" ? "view-mode-tab--active" : ""}`}
            onClick={() => setActiveTab("tasks")}
          >
            📋 Task Validation &amp; Review ({auditLogs.length})
          </button>
          <button
            type="button"
            className={`view-mode-tab ${activeTab === "users" ? "view-mode-tab--active" : ""}`}
            onClick={() => setActiveTab("users")}
          >
            👥 User Management ({users.length})
          </button>
          <button
            type="button"
            className={`view-mode-tab ${activeTab === "models" ? "view-mode-tab--active" : ""}`}
            onClick={() => setActiveTab("models")}
          >
            🧠 AI Model Validation
          </button>
          <button
            type="button"
            className={`view-mode-tab ${activeTab === "services" ? "view-mode-tab--active" : ""}`}
            onClick={() => setActiveTab("services")}
          >
            ⚡ Subsystem Status
          </button>
          <button
            type="button"
            className={`view-mode-tab ${activeTab === "overview" ? "view-mode-tab--active" : ""}`}
            onClick={() => setActiveTab("overview")}
          >
            📊 System Overview
          </button>
        </div>

        {loading ? (
          <div className="d-flex align-items-center gap-2 p-5 text-secondary">
            <div className="spinner-border text-primary" role="status" />
            <span>Loading administration workspace…</span>
          </div>
        ) : (
          <>
            {/* TAB 1: TASK VALIDATION & REVIEW */}
            {activeTab === "tasks" && (
              <div className="dash-card">
                <div className="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
                  <div>
                    <h4 className="dash-card__title fs-6 mb-1">User Analysis Tasks</h4>
                    <p className="text-secondary small mb-0">
                      Review detections, validate analytical accuracy, and manage task lifecycle.
                    </p>
                  </div>
                  <div className="d-flex gap-2 align-items-center">
                    <span className="small text-secondary">Filter:</span>
                    <div className="btn-group btn-group-sm" role="group">
                      {["all", "verified", "done", "flagged"].map((f) => (
                        <button
                          key={f}
                          type="button"
                          className={`btn ${
                            taskFilter === f ? "btn-primary" : "btn-outline-secondary"
                          } py-0 px-2`}
                          style={{ fontSize: "12px", textTransform: "capitalize" }}
                          onClick={() => setTaskFilter(f)}
                        >
                          {f === "done" ? "Pending Review" : f}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="table-responsive">
                  <table className="table table-hover table-bordered align-middle mb-0">
                    <thead className="table-dark">
                      <tr>
                        <th>Task / Date</th>
                        <th>User</th>
                        <th>Preview</th>
                        <th>Objects</th>
                        <th>Inference</th>
                        <th>Validation Status</th>
                        <th>Task Management</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredTasks.length === 0 ? (
                        <tr>
                          <td colSpan="7" className="text-center text-secondary py-4 small">
                            No analysis tasks match the selected filter.
                          </td>
                        </tr>
                      ) : (
                        filteredTasks.map((t) => (
                          <tr key={t.ana_id}>
                            <td className="small text-nowrap">
                              <span className="fw-semibold">#{t.ana_id.slice(0, 8)}</span>
                              <br />
                              <span className="text-secondary" style={{ fontSize: "11px" }}>
                                {t.ana_date ? new Date(t.ana_date).toLocaleDateString() : "—"}
                              </span>
                            </td>
                            <td className="small">
                              <strong>{t.user_name}</strong>
                              <br />
                              <span className="text-secondary" style={{ fontSize: "11px" }}>
                                {t.user_email}
                              </span>
                            </td>
                            <td>
                              {t.img_url ? (
                                <img
                                  src={resolveUrl(t.img_url)}
                                  alt="Preview"
                                  style={{
                                    width: "42px",
                                    height: "42px",
                                    objectFit: "cover",
                                    borderRadius: "4px",
                                    border: "1px solid #ddd",
                                  }}
                                />
                              ) : "—"}
                            </td>
                            <td>
                              <span className="badge bg-light text-dark border">
                                {t.det_count} objects
                              </span>
                            </td>
                            <td className="small">
                              {t.comp_time != null ? `${t.comp_time}s` : "—"}
                            </td>
                            <td>
                              {t.status === "verified" && (
                                <span className="badge bg-success text-white">
                                  ✅ Verified
                                </span>
                              )}
                              {t.status === "flagged" && (
                                <span className="badge bg-warning text-dark">
                                  ⚠️ Flagged
                                </span>
                              )}
                              {t.status === "done" && (
                                <span className="badge bg-info-subtle text-info-emphasis border border-info-subtle">
                                  Completed
                                </span>
                              )}
                              {t.status === "error" && (
                                <span className="badge bg-danger text-white">
                                  Failed
                                </span>
                              )}
                            </td>
                            <td>
                              <div className="d-flex gap-1 flex-wrap">
                                <Link
                                  to={`/results/${t.ana_id}`}
                                  className="btn btn-sm btn-outline-primary py-0 px-2"
                                  style={{ fontSize: "11px" }}
                                >
                                  Inspect
                                </Link>
                                {t.status !== "verified" && (
                                  <button
                                    type="button"
                                    className="btn btn-sm btn-outline-success py-0 px-2"
                                    style={{ fontSize: "11px" }}
                                    onClick={() => handleValidateTask(t.ana_id, "verified")}
                                    title="Mark as Verified"
                                  >
                                    Approve
                                  </button>
                                )}
                                {t.status !== "flagged" && (
                                  <button
                                    type="button"
                                    className="btn btn-sm btn-outline-warning py-0 px-2"
                                    style={{ fontSize: "11px" }}
                                    onClick={() => handleValidateTask(t.ana_id, "flagged")}
                                    title="Flag for Quality Review"
                                  >
                                    Flag
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 2: USER ACCOUNT MANAGEMENT */}
            {activeTab === "users" && (
              <div className="dash-card">
                <div className="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
                  <div>
                    <h4 className="dash-card__title fs-6 mb-1">Registered User Accounts</h4>
                    <p className="text-secondary small mb-0">
                      Validate accounts, manage permissions, and assign administrative roles.
                    </p>
                  </div>
                  <input
                    type="text"
                    className="form-control form-control-sm"
                    style={{ maxWidth: "240px" }}
                    placeholder="Search users…"
                    value={userSearch}
                    onChange={(e) => setUserSearch(e.target.value)}
                  />
                </div>

                <div className="table-responsive">
                  <table className="table table-hover table-bordered align-middle mb-0">
                    <thead className="table-dark">
                      <tr>
                        <th>User</th>
                        <th>Email</th>
                        <th>Vision Profile</th>
                        <th>Analyses</th>
                        <th>Role</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredUsers.map((u) => (
                        <tr key={u.user_id}>
                          <td>
                            <div className="d-flex align-items-center gap-2">
                              <div
                                style={{
                                  width: "28px",
                                  height: "28px",
                                  borderRadius: "50%",
                                  background: u.role === "admin" ? "#2c6e71" : "#e0e6ed",
                                  color: u.role === "admin" ? "#fff" : "#333",
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  fontWeight: "bold",
                                  fontSize: "12px",
                                }}
                              >
                                {u.first_name ? u.first_name[0].toUpperCase() : "U"}
                              </div>
                              <span className="fw-semibold small">
                                {u.first_name} {u.last_name}
                              </span>
                            </div>
                          </td>
                          <td className="small">{u.email}</td>
                          <td>
                            <span className="badge bg-light text-dark border">
                              {u.cvd_type || "None"}
                            </span>
                          </td>
                          <td>
                            <span className="badge bg-light text-dark border">
                              {u.analyses_count}
                            </span>
                          </td>
                          <td>
                            <span
                              className={`badge ${
                                u.role === "admin"
                                  ? "bg-primary text-white"
                                  : "bg-secondary-subtle text-secondary-emphasis"
                              }`}
                            >
                              {u.role.toUpperCase()}
                            </span>
                          </td>
                          <td>
                            <span
                              className={`badge ${
                                u.status === "active"
                                  ? "bg-success text-white"
                                  : "bg-danger text-white"
                              }`}
                            >
                              {u.status}
                            </span>
                          </td>
                          <td>
                            <div className="d-flex gap-1">
                              <button
                                type="button"
                                className="btn btn-sm btn-outline-secondary py-0 px-2"
                                style={{ fontSize: "11px" }}
                                onClick={() => handleToggleRole(u)}
                              >
                                {u.role === "admin" ? "Demote" : "Make Admin"}
                              </button>
                              <button
                                type="button"
                                className={`btn btn-sm py-0 px-2 ${
                                  u.status === "active" ? "btn-outline-danger" : "btn-outline-success"
                                }`}
                                style={{ fontSize: "11px" }}
                                onClick={() => handleToggleStatus(u)}
                              >
                                {u.status === "active" ? "Suspend" : "Activate"}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 3: AI MODEL VALIDATION & CONFIG */}
            {activeTab === "models" && modelInfo && (
              <div className="row g-3">
                <div className="col-md-6">
                  <div className="dash-card h-100">
                    <h4 className="dash-card__title fs-6 mb-3">AI Vision Detector</h4>
                    <div className="d-flex flex-column gap-2 small">
                      <div className="d-flex justify-content-between p-2 rounded bg-light border">
                        <span>Architecture:</span>
                        <strong>{modelInfo.model_name}</strong>
                      </div>
                      <div className="d-flex justify-content-between p-2 rounded bg-light border">
                        <span>Model Checkpoint:</span>
                        <code>{modelInfo.weights_file}</code>
                      </div>
                      <div className="d-flex justify-content-between p-2 rounded bg-light border">
                        <span>Detectable Categories:</span>
                        <strong>{modelInfo.classes_count} Object Classes</strong>
                      </div>
                      <div className="d-flex justify-content-between p-2 rounded bg-light border">
                        <span>Inference Hardware:</span>
                        <strong>{modelInfo.device}</strong>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="col-md-6">
                  <div className="dash-card h-100">
                    <h4 className="dash-card__title fs-6 mb-3">Detection Sensitivity Controls</h4>
                    <form onSubmit={handleSaveModelConfig}>
                      <div className="mb-3">
                        <label className="form-label small fw-semibold">
                          Confidence Threshold: <span className="text-primary">{confThreshold}</span>
                        </label>
                        <input
                          type="range"
                          className="form-range"
                          min="0.10"
                          max="0.90"
                          step="0.05"
                          value={confThreshold}
                          onChange={(e) => setConfThreshold(e.target.value)}
                        />
                        <div className="d-flex justify-content-between text-secondary" style={{ fontSize: "11px" }}>
                          <span>0.10 (Sensitive)</span>
                          <span>0.90 (Strict)</span>
                        </div>
                      </div>

                      <div className="mb-3">
                        <label className="form-label small fw-semibold">
                          NMS IoU Threshold: <span className="text-primary">{iouThreshold}</span>
                        </label>
                        <input
                          type="range"
                          className="form-range"
                          min="0.10"
                          max="0.90"
                          step="0.05"
                          value={iouThreshold}
                          onChange={(e) => setIouThreshold(e.target.value)}
                        />
                      </div>

                      <button
                        type="submit"
                        className="btn-primary w-100"
                        disabled={savingModel}
                      >
                        {savingModel ? "Saving…" : "Save Model Settings"}
                      </button>
                    </form>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 4: SUBSYSTEM STATUS */}
            {activeTab === "services" && (
              <div className="row g-3">
                {services.map((s) => (
                  <div key={s.id} className="col-md-6">
                    <div className="dash-card h-100">
                      <div className="d-flex justify-content-between align-items-center mb-1">
                        <h4 className="dash-card__title fs-6 mb-0">{s.name}</h4>
                        <span className="badge bg-success-subtle text-success-emphasis border border-success-subtle">
                          🟢 {s.uptime}
                        </span>
                      </div>
                      <p className="small text-secondary mb-0">
                        {s.details}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* TAB 5: SYSTEM OVERVIEW */}
            {activeTab === "overview" && overview && (
              <div>
                <section className="stat-grid mb-4">
                  <div className="stat-card">
                    <span className="stat-card__icon">👥</span>
                    <span className="stat-card__value">{overview.users.total}</span>
                    <span className="stat-card__label">
                      Registered Users ({overview.users.active} active)
                    </span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-card__icon">🖼️</span>
                    <span className="stat-card__value">{overview.analyses.total}</span>
                    <span className="stat-card__label">
                      Total Tasks ({overview.analyses.completed} done)
                    </span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-card__icon">🎯</span>
                    <span className="stat-card__value">{overview.analyses.total_detections}</span>
                    <span className="stat-card__label">Objects Localized</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-card__icon">📈</span>
                    <span className="stat-card__value">{overview.analyses.success_rate}%</span>
                    <span className="stat-card__label">Success Rate</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-card__icon">⚡</span>
                    <span className="stat-card__value">{overview.analyses.avg_latency_s}s</span>
                    <span className="stat-card__label">Avg. Latency</span>
                  </div>
                </section>

                <div className="row g-3">
                  <div className="col-md-6">
                    <div className="dash-card h-100">
                      <h4 className="dash-card__title fs-6 mb-3">👁️ Vision Profile Demographics</h4>
                      {overview.cvd_distribution.length === 0 ? (
                        <p className="text-secondary small">No user CVD profiles recorded yet.</p>
                      ) : (
                        <div className="d-flex flex-column gap-2">
                          {overview.cvd_distribution.map((c) => (
                            <div key={c.type} className="d-flex justify-content-between align-items-center p-2 rounded bg-light border">
                              <span className="fw-semibold small">{c.type}</span>
                              <span className="badge bg-primary rounded-pill">{c.count} users</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="col-md-6">
                    <div className="dash-card h-100">
                      <h4 className="dash-card__title fs-6 mb-3">🏷️ Common Detected Objects</h4>
                      <div className="d-flex flex-column gap-2">
                        {overview.top_objects.map((o, idx) => (
                          <div key={o.name} className="d-flex justify-content-between align-items-center p-2 rounded bg-light border">
                            <span className="small">#{idx + 1} <strong>{o.name}</strong></span>
                            <span className="badge bg-secondary rounded-pill">{o.count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
