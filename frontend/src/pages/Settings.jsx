import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar.jsx";
import { getCvdProfile, saveCvdProfile, getProfile, saveProfile } from "../api/profile.js";

const TYPES = [
  { value: "Protanopia", hint: "Reds look darker and can blend with greens." },
  { value: "Deuteranopia", hint: "Greens and reds look alike." },
  { value: "Tritanopia", hint: "Blues and yellows are hard to tell apart." },
];
const SEVERITIES = ["mild", "moderate", "severe"];

export default function Settings() {
  const [profile, setProfile] = useState({
    dob: "", gender: "", phone: "", street: "", city: "", state: "", pincode: "",
  });
  const [type, setType] = useState("Deuteranopia");
  const [severity, setSeverity] = useState("moderate");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([getProfile(), getCvdProfile()])
      .then(([p, cvd]) => {
        setProfile({
          dob: p?.dob ? p.dob.slice(0, 10) : "",
          gender: p?.gender || "", phone: p?.phone || "", street: p?.street || "",
          city: p?.city || "", state: p?.state || "", pincode: p?.pincode || "",
        });
        if (cvd) { setType(cvd.type); setSeverity(cvd.severity || "moderate"); }
      })
      .catch((e) => setError(e.message));
  }, []);

  function update(field, value) {
    setProfile((p) => ({ ...p, [field]: value }));
  }

  async function handleSave(e) {
    e.preventDefault();
    setMessage(""); setError(""); setSaving(true);
    try {
      await saveProfile({ ...profile, dob: profile.dob || null });
      await saveCvdProfile({ type, severity });
      setMessage("Saved. Your patient details and colour-vision settings will be used for future analyses.");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="settings-main-wide">
        <div className="page-header">
          <p className="app-main__eyebrow">Profile Configuration · Accessibility</p>
          <h2>Vision Settings &amp; Demographics</h2>
          <p className="upload-sub">
            Customize your Color Vision Deficiency classification to ensure simulation transforms, contrast advisories, and color suggestions are personalized for you.
          </p>
        </div>

        {error && <div className="alert" role="alert">{error}</div>}
        {message && <div className="notice" role="status">{message}</div>}

        <form onSubmit={handleSave} className="settings-form-grid">
          {/* CVD Profile Card */}
          <section className="dash-card">
            <div className="dash-card__header mb-3">
              <div>
                <h3 className="dash-card__title">👁️ Colour Vision Profile</h3>
                <span className="dash-card__subtitle">Defines simulation filters and confusion matrices</span>
              </div>
            </div>

            <div className="field mb-4">
              <label className="fw-semibold">Select Primary Deficiency</label>
              <div className="choice-list">
                {TYPES.map((t) => (
                  <label key={t.value} className={"choice" + (type === t.value ? " choice--on" : "")}>
                    <input
                      type="radio"
                      name="type"
                      value={t.value}
                      checked={type === t.value}
                      onChange={() => setType(t.value)}
                    />
                    <span className="choice__name">{t.value}</span>
                    <span className="choice__hint">{t.hint}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="field">
              <label htmlFor="severity" className="fw-semibold">Deficiency Severity</label>
              <select
                id="severity"
                className="form-select"
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
              >
                {SEVERITIES.map((s) => (
                  <option key={s} value={s}>
                    {s.charAt(0).toUpperCase() + s.slice(1)}
                  </option>
                ))}
              </select>
              <span className="field-hint">
                Controls the intensity factor used in Brettel/Vienot simulation matrices.
              </span>
            </div>
          </section>

          {/* Patient Details Card */}
          <section className="dash-card">
            <div className="dash-card__header mb-3">
              <div>
                <h3 className="dash-card__title">👤 Patient Information</h3>
                <span className="dash-card__subtitle">Stored securely with your account</span>
              </div>
            </div>

            <div className="field-grid">
              <div className="field">
                <label htmlFor="dob">Date of birth</label>
                <input id="dob" type="date" value={profile.dob} onChange={(e) => update("dob", e.target.value)} />
              </div>
              <div className="field">
                <label htmlFor="gender">Gender</label>
                <select id="gender" value={profile.gender} onChange={(e) => update("gender", e.target.value)}>
                  <option value="">Prefer not to say</option>
                  <option>Female</option>
                  <option>Male</option>
                  <option>Other</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="phone">Phone</label>
                <input id="phone" value={profile.phone} maxLength={30} onChange={(e) => update("phone", e.target.value)} />
              </div>
              <div className="field">
                <label htmlFor="pincode">Pincode</label>
                <input id="pincode" value={profile.pincode} maxLength={20} onChange={(e) => update("pincode", e.target.value)} />
              </div>
              <div className="field field--full">
                <label htmlFor="street">Street / address</label>
                <input id="street" value={profile.street} maxLength={200} onChange={(e) => update("street", e.target.value)} />
              </div>
              <div className="field">
                <label htmlFor="city">City</label>
                <input id="city" value={profile.city} maxLength={100} onChange={(e) => update("city", e.target.value)} />
              </div>
              <div className="field">
                <label htmlFor="state">State</label>
                <input id="state" value={profile.state} maxLength={100} onChange={(e) => update("state", e.target.value)} />
              </div>
            </div>

            <div className="mt-4 pt-3 border-top">
              <button className="btn-primary" type="submit" disabled={saving}>
                {saving ? "Saving settings…" : "💾 Save Changes"}
              </button>
            </div>
          </section>
        </form>
      </main>
    </div>
  );
}
