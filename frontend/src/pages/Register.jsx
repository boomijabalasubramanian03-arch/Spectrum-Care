import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import AuthVisual from "../components/AuthVisual.jsx";
import { register } from "../api/auth.js";

const initialForm = {
  firstName: "",
  middleName: "",
  lastName: "",
  email: "",
  password: "",
  confirmPassword: "",
};

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function update(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  function validate() {
    if (!form.firstName.trim() || !form.lastName.trim()) {
      return "First and last name are required.";
    }
    if (!/^\S+@\S+\.\S+$/.test(form.email.trim())) {
      return "Enter a valid email address.";
    }
    if (form.password.length < 8) {
      return "Password must be at least 8 characters.";
    }
    if (form.password.length > 72) {
      return "Password must be 72 characters or fewer.";
    }
    if (form.password !== form.confirmPassword) {
      return "Passwords don't match.";
    }
    return "";
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setSubmitting(true);
    try {
      await register(form);
      navigate("/login", {
        replace: true,
        state: { justRegistered: true },
      });
    } catch (err) {
      setError(err?.message || "Registration failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-shell">
      <AuthVisual />

      <div className="auth-form-panel">
        <div className="auth-form-card">
          <p className="auth-form-card__eyebrow">User Control · Registration</p>
          <h1>Create your account</h1>
          <p className="auth-form-card__sub">
            Create your account first. After login, complete your patient and colour vision
            profile so results can be tailored to you.
          </p>

          {error && (
            <div className="alert" role="alert">
              <span className="alert__icon" aria-hidden="true">⚠</span>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate>
            <div className="field-row">
              <div className="field">
                <label htmlFor="firstName">First name</label>
                <input
                  id="firstName"
                  required
                  value={form.firstName}
                  onChange={update("firstName")}
                  placeholder="Your first name"
                  autoComplete="given-name"
                />
              </div>
              <div className="field">
                <label htmlFor="lastName">Last name</label>
                <input
                  id="lastName"
                  required
                  value={form.lastName}
                  onChange={update("lastName")}
                  placeholder="Your last name"
                  autoComplete="family-name"
                />
              </div>
            </div>

            <div className="field">
              <label htmlFor="middleName">Middle name (optional)</label>
              <input
                id="middleName"
                value={form.middleName}
                onChange={update("middleName")}
                autoComplete="additional-name"
                placeholder="Optional"
              />
            </div>

            <div className="field">
              <label htmlFor="email">Email address</label>
              <input
                id="email"
                type="email"
                required
                value={form.email}
                onChange={update("email")}
                placeholder="you@example.com"
                autoComplete="email"
              />
            </div>

            <div className="field">
              <label htmlFor="password">Password</label>
              <div className="password-field">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={form.password}
                  onChange={update("password")}
                  placeholder="At least 8 characters"
                  autoComplete="new-password"
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
              <p className="field-hint">8–72 characters.</p>
            </div>

            <div className="field">
              <label htmlFor="confirmPassword">Confirm password</label>
              <div className="password-field">
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  required
                  value={form.confirmPassword}
                  onChange={update("confirmPassword")}
                  placeholder="Re-enter your password"
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowConfirmPassword((v) => !v)}
                  aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                >
                  {showConfirmPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            <button className="btn-primary" type="submit" disabled={submitting}>
              {submitting ? "Creating account…" : "Create account"}
            </button>
          </form>

          <p className="auth-form-card__foot">
            Already have an account? <Link to="/login">Log in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
