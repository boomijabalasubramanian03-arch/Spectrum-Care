import { useEffect, useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import AuthVisual from "../components/AuthVisual.jsx";
import { login } from "../api/auth.js";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (location.state?.justRegistered) {
      setNotice("Account created successfully. Please log in to continue.");
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location, navigate]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setNotice("");

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail) {
      setError("Please enter your email address.");
      return;
    }
    if (!password) {
      setError("Please enter your password.");
      return;
    }

    setSubmitting(true);
    try {
      await login({ email: cleanEmail, password });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err?.message || "Login failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-shell">
      <AuthVisual />

      <div className="auth-form-panel">
        <div className="auth-form-card">
          <p className="auth-form-card__eyebrow">User Control · Authentication</p>
          <h1>Welcome back</h1>
          <p className="auth-form-card__sub">
            Log in to analyse an image, hear its contextual colour description, or revisit
            your history.
          </p>

          {notice && (
            <div className="notice" role="status">
              {notice}
            </div>
          )}

          {error && (
            <div className="alert" role="alert">
              <span className="alert__icon" aria-hidden="true">⚠</span>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate>
            <div className="field">
              <label htmlFor="email">Email address</label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
              />
            </div>

            <div className="field">
              <label htmlFor="password">Password</label>
              <div className="password-field">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            <button className="btn-primary" type="submit" disabled={submitting}>
              {submitting ? "Logging in…" : "Log in"}
            </button>
          </form>

          <p className="auth-form-card__foot">
            New here? <Link to="/register">Create an account</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
