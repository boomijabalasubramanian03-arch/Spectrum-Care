import { useState, useEffect } from "react";
import { useNavigate, Link, useLocation } from "react-router-dom";
import { getStoredUser, logout } from "../api/auth.js";
import { getCvdProfile } from "../api/profile.js";
import { request, authHeaders } from "../api/http.js";

const BASE_NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: "📊" },
  { to: "/upload", label: "Analyse Image", icon: "📷" },
  { to: "/history", label: "History", icon: "🕒" },
  { to: "/settings", label: "My Vision", icon: "👁️" },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [currentUser, setCurrentUser] = useState(getStoredUser());
  const [cvdType, setCvdType] = useState(null);

  useEffect(() => {
    // Sync latest user details including role
    request("/api/auth/me", { headers: authHeaders() })
      .then(({ data }) => {
        if (data) {
          localStorage.setItem("user", JSON.stringify(data));
          setCurrentUser(data);
        }
      })
      .catch(() => {});

    getCvdProfile()
      .then((p) => {
        if (p?.type) setCvdType(p.type);
      })
      .catch(() => {});
  }, []);

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  const isAdmin = currentUser?.role === "admin" || currentUser?.role === "administrator";
  const navItems = isAdmin
    ? [...BASE_NAV_ITEMS, { to: "/admin", label: "Admin Console", icon: "🛡️" }]
    : BASE_NAV_ITEMS;

  return (
    <aside className="app-sidebar">
      <div className="sidebar-brand">
        <span className="sidebar-brand__mark" />
        <div className="sidebar-brand__text">
          <span className="sidebar-brand__title">Chroma Context</span>
          <span className="sidebar-brand__subtitle">Accessibility AI</span>
        </div>
      </div>

      {cvdType && (
        <div className="sidebar-cvd-pill">
          <span className="sidebar-cvd-pill__dot" />
          <div className="sidebar-cvd-pill__info">
            <span className="sidebar-cvd-pill__label">Active Vision Filter</span>
            <span className="sidebar-cvd-pill__value">{cvdType}</span>
          </div>
        </div>
      )}

      <nav className="sidebar-nav">
        <span className="sidebar-nav__heading">Navigation</span>
        {navItems.map((item) => {
          const isActive = location.pathname.startsWith(item.to);
          return (
            <Link
              key={item.to}
              to={item.to}
              className={`sidebar-nav__link ${isActive ? "sidebar-nav__link--active" : ""}`}
            >
              <span className="sidebar-nav__icon">{item.icon}</span>
              <span className="sidebar-nav__label">{item.label}</span>
              {isActive && <span className="sidebar-nav__indicator" />}
            </Link>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="sidebar-user__avatar">
            {currentUser?.first_name ? currentUser.first_name[0].toUpperCase() : "U"}
          </div>
          <div className="sidebar-user__details">
            <span className="sidebar-user__name">
              {currentUser?.first_name} {currentUser?.last_name}
              {isAdmin && (
                <span className="badge bg-primary ms-1" style={{ fontSize: "10px" }}>
                  ADMIN
                </span>
              )}
            </span>
            <span className="sidebar-user__email">{currentUser?.email}</span>
          </div>
        </div>
        <button className="sidebar-logout-btn" onClick={handleLogout} title="Log out">
          Log out
        </button>
      </div>
    </aside>
  );
}
