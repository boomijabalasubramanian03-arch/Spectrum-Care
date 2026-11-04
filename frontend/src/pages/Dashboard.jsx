import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Sidebar from "../components/Sidebar.jsx";
import { getStoredUser } from "../api/auth.js";
import { getStats } from "../api/stats.js";

export default function Dashboard() {
  const user = getStoredUser();
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getStats().then(setStats).catch((e) => setError(e.message));
  }, []);

  const hasHistory = stats && stats.total_analyses > 0;

  return (
    <div className="app-shell">
      <Sidebar />

      <main className="dash-main">
        {/* Welcome Hero */}
        <section className="dash-hero">
          <div>
            <div className="d-flex align-items-center gap-2 mb-1">
              <p className="app-main__eyebrow mb-0">Overview · Accessibility Dashboard</p>
              {(user?.role === "admin" || user?.role === "administrator") && (
                <span className="badge bg-primary-subtle text-primary-emphasis border border-primary-subtle">
                  Administrator Active
                </span>
              )}
            </div>
            <h2 className="dash-hero__title">
              {user ? `Welcome back, ${user.first_name}.` : "Welcome back."}
            </h2>
            <p className="dash-hero__sub">
              Upload photographs to identify objects and their colours, with natural audio descriptions and tailored visual accessibility.
            </p>
          </div>
          <div className="d-flex gap-2 flex-wrap">
            {(user?.role === "admin" || user?.role === "administrator") && (
              <Link className="btn-ghost dash-hero__cta" to="/admin">
                🛡️ Admin Console
              </Link>
            )}
            <Link className="btn-primary dash-hero__cta" to="/upload">
              📷 Analyse an image
            </Link>
          </div>
        </section>

        {error && <div className="alert" role="alert">{error}</div>}

        {/* 5-Card Analytics Grid */}
        <section className="stat-grid">
          <div className="stat-card">
            <span className="stat-card__icon">🖼️</span>
            <span className="stat-card__value">{stats ? stats.total_analyses : "—"}</span>
            <span className="stat-card__label">Images analysed</span>
          </div>
          <div className="stat-card">
            <span className="stat-card__icon">🎯</span>
            <span className="stat-card__value">{stats ? stats.total_objects : "—"}</span>
            <span className="stat-card__label">Objects detected</span>
          </div>
          <div className="stat-card">
            <span className="stat-card__icon">🏷️</span>
            <span className="stat-card__value">{stats?.top_object || "—"}</span>
            <span className="stat-card__label">Most detected object</span>
          </div>
          <div className="stat-card">
            <span className="stat-card__icon">🎨</span>
            <span className="stat-card__value">{stats?.top_color || "—"}</span>
            <span className="stat-card__label">Most common colour</span>
          </div>
          <div className="stat-card">
            <span className="stat-card__icon">⚡</span>
            <span className="stat-card__value">
              {stats?.avg_processing_time != null ? `${stats.avg_processing_time}s` : "—"}
            </span>
            <span className="stat-card__label">Avg. inference speed</span>
          </div>
        </section>

        {/* Recent Activity Card */}
        <section className="dash-recent-card">
          <div className="dash-recent__head">
            <div>
              <h3>Recent Image Analyses</h3>
              <p className="dash-card__subtitle">Your processed photographs, detections, and descriptions</p>
            </div>
            {hasHistory && <Link className="btn-ghost" to="/history">View all history →</Link>}
          </div>

          {!hasHistory && (
            <div className="dash-empty">
              <p>You haven't analysed an image yet.</p>
              <Link className="btn-primary" to="/upload">Analyse your first image</Link>
            </div>
          )}

          {hasHistory && (
            <div className="history-table-wrapper">
              <table className="table table-hover align-middle mb-0">
                <thead className="table-light">
                  <tr>
                    <th>Image</th>
                    <th>Processed Timestamp</th>
                    <th>Detected Entities</th>
                    <th>Status</th>
                    <th className="text-end">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.recent.map((item) => (
                    <tr key={item.ana_id}>
                      <td style={{ width: "70px" }}>
                        <img src={item.img_url} alt="" className="history-row__thumb" />
                      </td>
                      <td>
                        <span className="fw-semibold">
                          {new Date(item.ana_date).toLocaleDateString()}
                        </span>
                        <span className="text-secondary d-block small">
                          {new Date(item.ana_date).toLocaleTimeString()}
                        </span>
                      </td>
                      <td>
                        <span className="badge bg-secondary-subtle text-secondary-emphasis">
                          {item.det_count} object{item.det_count === 1 ? "" : "s"} detected
                        </span>
                      </td>
                      <td>
                        <span className={`status status--${item.status === "done" ? "done" : "next"}`}>
                          {item.status}
                        </span>
                      </td>
                      <td className="text-end">
                        <Link className="btn-ghost" to={`/results/${item.ana_id}`}>
                          View Details →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
