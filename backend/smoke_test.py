"""
End-to-end self-test of the backend (register -> login -> CVD profile ->
upload+analyse -> history -> stats -> reports -> logout). Uses a throw-away
database, so it never touches your real data.

    cd backend
    pip install httpx            # only needed for this test
    python smoke_test.py
"""
import glob
import os
import sys
import tempfile

# Throw-away DB must be set BEFORE the app is imported.
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_tmp, "test.db").replace("\\", "/")

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
samples = sorted(glob.glob(os.path.join(HERE, "..", "training", "dataset", "valid", "images", "*.jpg")))
if not samples:
    sys.exit("No sample image found in training/dataset/valid/images")

client = TestClient(app)
fails = 0


def check(name, cond, extra=""):
    global fails
    print(("PASS  " if cond else "FAIL  ") + name + (f"   {extra}" if extra and not cond else ""))
    fails += 0 if cond else 1


check("health", client.get("/api/health").json() == {"status": "ok"})

body = {"first_name": "Test", "last_name": "User", "email": "Test.User@Example.com", "password": "password123"}
r = client.post("/api/auth/register", json=body)
check("register", r.status_code == 201, r.text)
r = client.post("/api/auth/register", json=body)
check("duplicate email rejected with readable message", r.status_code == 400 and "already exists" in r.json()["detail"], r.text)
r = client.post("/api/auth/register", json={**body, "email": "x@y.com", "password": "short"})
check("short password -> readable 422", r.status_code == 422 and isinstance(r.json()["detail"], str), r.text)

r = client.post("/api/auth/login", json={"email": "test.user@example.com", "password": "wrong-pass"})
check("wrong password -> 401 message", r.status_code == 401 and r.json()["detail"], r.text)
r = client.post("/api/auth/login", json={"email": "TEST.USER@example.com", "password": "password123"})
check("login (case-insensitive email)", r.status_code == 200 and "access_token" in r.json(), r.text)
H = {"Authorization": "Bearer " + r.json()["access_token"]}

check("no token -> 401", client.get("/api/analysis/history").status_code == 401)
r = client.put("/api/profile/cvd", json={"type": "Deuteranopia", "severity": "moderate"}, headers=H)
check("save CVD profile", r.status_code == 200, r.text)

with open(samples[0], "rb") as f:
    r = client.post("/api/analysis/upload", files={"file": ("capture-1.jpg", f, "image/jpeg")}, headers=H)
check("upload + analyse (camera-style filename)", r.status_code == 200 and r.json()["status"] == "done", r.text[:300])
ana = r.json()
check("annotated + CVD images produced", bool(ana.get("annotated_url")) and bool(ana.get("cvd_url")))

r = client.post("/api/analysis/upload", files={"file": ("x.jpg", b"not an image", "image/jpeg")}, headers=H)
check("corrupt image -> 400", r.status_code == 400, r.text)
r = client.post("/api/analysis/upload", files={"file": ("x.gif", b"GIF89a", "image/gif")}, headers=H)
check("unsupported type -> 400", r.status_code == 400, r.text)

check("history", len(client.get("/api/analysis/history", headers=H).json()) >= 1)
check("stats", client.get("/api/analysis/stats", headers=H).json()["total_analyses"] >= 1)
check("get analysis", client.get(f"/api/analysis/{ana['ana_id']}", headers=H).status_code == 200)
for fmt in ("json", "csv", "pdf"):
    r = client.get(f"/api/analysis/{ana['ana_id']}/report?fmt={fmt}", headers=H)
    check(f"report {fmt}", r.status_code == 200 and len(r.content) > 50)

# ---- Admin Module Tests ----
check("regular user blocked from admin overview", client.get("/api/admin/overview", headers=H).status_code == 403)

# Elevate test user to admin
from app.database import SessionLocal
from app import models
_db = SessionLocal()
_u = _db.query(models.User).filter(models.User.email == "test.user@example.com").first()
_u.role = "admin"
_db.commit()
_db.close()

check("admin overview accessible", client.get("/api/admin/overview", headers=H).status_code == 200)
check("admin users list", client.get("/api/admin/users", headers=H).status_code == 200 and len(client.get("/api/admin/users", headers=H).json()) >= 1)
check("admin services status", client.get("/api/admin/services", headers=H).status_code == 200 and len(client.get("/api/admin/services", headers=H).json()["services"]) >= 5)
check("admin models info", client.get("/api/admin/models", headers=H).status_code == 200 and "model_name" in client.get("/api/admin/models", headers=H).json())
check("admin update model config", client.post("/api/admin/models/config", json={"conf_threshold": 0.40}, headers=H).status_code == 200)
check("admin audit logs", client.get("/api/admin/audit-logs", headers=H).status_code == 200 and len(client.get("/api/admin/audit-logs", headers=H).json()) >= 1)

check("logout", client.post("/api/auth/logout", headers=H).status_code == 200)

print("\nALL TESTS PASSED" if not fails else f"\n{fails} TEST(S) FAILED")
sys.exit(1 if fails else 0)
