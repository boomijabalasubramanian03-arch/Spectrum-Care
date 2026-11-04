import { useEffect, useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { getHistory } from "../api/analysis.js";
import { resolveUrl } from "../api/http.js";
import Sidebar from "../components/Sidebar.jsx";

export default function History() {
  const [items, setItems] = useState(null);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    getHistory().then(setItems).catch((err) => setError(err.message));
  }, []);

  const filteredItems = useMemo(() => {
    if (!items) return [];
    return items.filter((item) => {
      const matchesStatus =
        statusFilter === "all" || item.status === statusFilter;
      const dateStr = new Date(item.ana_date).toLocaleString().toLowerCase();
      const matchesSearch =
        !searchTerm.trim() ||
        dateStr.includes(searchTerm.toLowerCase()) ||
        String(item.det_count).includes(searchTerm) ||
        (item.err_msg && item.err_msg.toLowerCase().includes(searchTerm.toLowerCase()));
      return matchesStatus && matchesSearch;
    });
  }, [items, searchTerm, statusFilter]);

  return (
    <div className="app-shell">
      <Sidebar />

      <main className="history-main-wide">
        <div className="page-header">
          <div className="d-flex justify-content-between align-items-center flex-wrap gap-3">
            <div>
              <p className="app-main__eyebrow">Database Records · User History</p>
              <h2>Past Image Analyses</h2>
              <p className="upload-sub">
                Browse through all processed photographs, detection summaries, and CVD simulation reports.
              </p>
            </div>
            <Link to="/upload" className="btn-primary" style={{ width: "auto" }}>
              + New Analysis
            </Link>
          </div>
        </div>

        {error && <div className="alert" role="alert">{error}</div>}

        {/* Search & Filter Toolbar */}
        <div className="history-toolbar">
          <div className="history-search-input">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              placeholder="Search by date, object count, or keyword…"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <div className="history-filter-group">
            <button
              className={`filter-btn ${statusFilter === "all" ? "filter-btn--active" : ""}`}
              onClick={() => setStatusFilter("all")}
            >
              All ({items?.length || 0})
            </button>
            <button
              className={`filter-btn ${statusFilter === "done" ? "filter-btn--active" : ""}`}
              onClick={() => setStatusFilter("done")}
            >
              Completed ({items?.filter((i) => i.status === "done").length || 0})
            </button>
            <button
              className={`filter-btn ${statusFilter === "error" ? "filter-btn--active" : ""}`}
              onClick={() => setStatusFilter("error")}
            >
              Failed ({items?.filter((i) => i.status === "error").length || 0})
            </button>
          </div>
        </div>

        {items && items.length === 0 && (
          <div className="dash-empty">
            <p>You haven't analysed an image yet.</p>
            <Link className="btn-primary" to="/upload">Analyse your first image</Link>
          </div>
        )}

        {items && items.length > 0 && filteredItems.length === 0 && (
          <div className="dash-empty">
            <p>No past analyses match your search criteria.</p>
            <button className="btn-ghost" onClick={() => { setSearchTerm(""); setStatusFilter("all"); }}>
              Reset Filters
            </button>
          </div>
        )}

        {filteredItems.length > 0 && (
          <div className="history-table-container">
            <table className="table table-hover align-middle mb-0 history-table">
              <thead className="table-dark">
                <tr>
                  <th>Thumbnail</th>
                  <th>Analysis Date &amp; Time</th>
                  <th>Objects Identified</th>
                  <th>Status</th>
                  <th>Processing Details</th>
                  <th className="text-end">Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((item) => (
                  <tr key={item.ana_id}>
                    <td style={{ width: "80px" }}>
                      <img src={resolveUrl(item.img_url)} alt="" className="history-row__thumb-lg" />
                    </td>
                    <td>
                      <span className="fw-bold d-block text-dark">
                        {new Date(item.ana_date).toLocaleDateString(undefined, {
                          weekday: "short",
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        })}
                      </span>
                      <span className="text-secondary small font-monospace">
                        {new Date(item.ana_date).toLocaleTimeString()}
                      </span>
                    </td>
                    <td>
                      <span className="badge bg-primary-subtle text-primary-emphasis px-3 py-2 fs-6">
                        {item.det_count} {item.det_count === 1 ? "object" : "objects"}
                      </span>
                    </td>
                    <td>
                      <span className={`status status--${item.status === "done" ? "done" : "next"}`}>
                        {item.status}
                      </span>
                    </td>
                    <td>
                      {item.status === "error" && item.err_msg ? (
                        <span className="text-danger small">{item.err_msg}</span>
                      ) : (
                        <span className="text-secondary small">CVD simulation &amp; voice ready</span>
                      )}
                    </td>
                    <td className="text-end">
                      <Link className="btn-ghost" to={`/results/${item.ana_id}`}>
                        View Analysis →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
