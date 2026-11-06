"""End-to-end smoke test for the demo.

Part 1 talks to the running backend over the network (default http://127.0.0.1:8000):
health, the public programme list, the CORS preflight from the portal's origin, and a
recommendation request without a sign-in token, which must be refused.

Part 2 sends the app's own requests through the real FastAPI app in this process with
the v4 model: sign-in role check, saving a profile with recommendations, the what-if
preview, the career note, the programme data used by Compare, saving a programme,
feedback, and an administrator cutoff update with its audit log entry. Firebase sign-in
is replaced by a fixed demo student and demo administrator, and Firestore by an
in-memory copy, so no real account or record is read or changed. The PDF report and
the Compare screen are built inside the app from these responses and are checked on
the phone.

    python demo_smoke.py [backend_url] [portal_origin]
"""
import contextlib
import io
import itertools
import sys

import requests
from fastapi.testclient import TestClient

with contextlib.redirect_stdout(io.StringIO()):
    import main

BACKEND = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
PORTAL_ORIGIN = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:5000"
STUDENT = {"uid": "smoke-student", "email": "smoke-student@example.com", "email_verified": True}
ADMIN_EMAIL = next(iter(sorted(main.admin_emails())), "smoke-admin@example.com")
ADMIN = {"uid": "smoke-admin", "email": ADMIN_EMAIL, "email_verified": True}

failures = []


def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))
    if not ok:
        failures.append(name)


# ----------------------------------------------------------------- in-memory Firestore
_ids = itertools.count(1)


class Snap:
    def __init__(self, ref, data):
        self.reference, self.id, self._data = ref, ref.id, data

    @property
    def exists(self):
        return self._data is not None

    def to_dict(self):
        return None if self._data is None else dict(self._data)

    def get(self, field):
        return (self._data or {}).get(field)


class DocRef:
    def __init__(self, store, path, doc_id):
        self.store, self.path, self.id = store, path, doc_id

    @property
    def key(self):
        return f"{self.path}/{self.id}"

    @property
    def parent(self):
        return Query(self.store, self.path)

    def get(self):
        return Snap(self, self.store.docs.get(self.key))

    def set(self, data, merge=False):
        current = self.store.docs.get(self.key) if merge else None
        self.store.docs[self.key] = {**(current or {}), **data}

    def update(self, data):
        current = self.store.docs.setdefault(self.key, {})
        for k, v in data.items():
            if v is main.fb_firestore.DELETE_FIELD:
                current.pop(k, None)
            else:
                current[k] = v

    def delete(self):
        self.store.docs.pop(self.key, None)

    def collection(self, name):
        return Query(self.store, f"{self.key}/{name}")


class Query:
    def __init__(self, store, path, filters=(), order=None, count=None, group=False):
        self.store, self.path, self.filters, self.order, self.count, self.group = store, path, filters, order, count, group

    @property
    def parent(self):
        owner_path, _, owner_id = self.path.rpartition("/")[0].rpartition("/")
        return DocRef(self.store, owner_path, owner_id) if owner_id else None

    def document(self, doc_id=None):
        return DocRef(self.store, self.path, doc_id or f"auto{next(_ids)}")

    def add(self, data):
        ref = self.document()
        ref.set(data)
        return None, ref

    def where(self, field=None, op=None, value=None, filter=None):
        if filter is not None:
            field, op, value = filter.field_path, filter.op_string, filter.value
        return Query(self.store, self.path, self.filters + ((field, op, value),), self.order, self.count, self.group)

    def order_by(self, field, direction=None):
        return Query(self.store, self.path, self.filters, (field, direction), self.count, self.group)

    def limit(self, n):
        return Query(self.store, self.path, self.filters, self.order, n, self.group)

    def stream(self):
        rows = []
        for key, data in list(self.store.docs.items()):
            parent, _, doc_id = key.rpartition("/")
            matches = parent.split("/")[-1] == self.path if self.group else parent == self.path
            if matches and all(_passes(data.get(f), op, v) for f, op, v in self.filters):
                rows.append(Snap(DocRef(self.store, parent, doc_id), data))
        if self.order:
            field, direction = self.order
            rows.sort(key=lambda s: str(s.to_dict().get(field)), reverse=direction == "DESCENDING")
        return iter(rows[: self.count] if self.count else rows)

    def get(self):
        return list(self.stream())


def _passes(actual, op, value):
    ops = {"==": lambda: actual == value, "!=": lambda: actual != value, "in": lambda: actual in value,
           ">": lambda: actual is not None and actual > value, ">=": lambda: actual is not None and actual >= value,
           "<": lambda: actual is not None and actual < value, "<=": lambda: actual is not None and actual <= value}
    try:
        return ops[op]()
    except TypeError:
        return False


class Batch:
    def __init__(self):
        self.ops = []

    def set(self, ref, data, merge=False):
        self.ops.append(lambda: ref.set(data, merge))

    def update(self, ref, data):
        self.ops.append(lambda: ref.update(data))

    def delete(self, ref):
        self.ops.append(ref.delete)

    def commit(self):
        for op in self.ops:
            op()


class FakeDb:
    def __init__(self):
        self.docs = {}

    def collection(self, name):
        return Query(self, name)

    def collection_group(self, name):
        return Query(self, name, group=True)

    def batch(self):
        return Batch()

    def recursive_delete(self, ref):
        for key in [k for k in self.docs if k == ref.key or k.startswith(ref.key + "/")]:
            del self.docs[key]


# ------------------------------------------------------------------------------ part 1
def live_checks():
    print(f"Part 1 - running backend at {BACKEND}")
    try:
        health = requests.get(f"{BACKEND}/api/health", timeout=10).json()
    except requests.RequestException as exc:
        check("GET /api/health answers", False, str(exc))
        return
    check("GET /api/health answers", True,
          f"model_loaded={health.get('model_loaded')} version={health.get('model_version')} "
          f"firestore_configured={health.get('firestore_configured')}")
    check("model is v4 and loaded", health.get("model_loaded") is True and str(health.get("model_version", "")).startswith("xgb-v4-"))
    programmes = requests.get(f"{BACKEND}/api/programmes", timeout=10)
    check("GET /api/programmes", programmes.status_code == 200, f"{len(programmes.json())} programmes")
    preflight = requests.options(f"{BACKEND}/api/recommend", timeout=10, headers={
        "Origin": PORTAL_ORIGIN, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type"})
    allowed = preflight.headers.get("access-control-allow-origin")
    check(f"CORS allows the portal origin {PORTAL_ORIGIN}", allowed == PORTAL_ORIGIN, f"allow-origin={allowed}")
    refused = requests.post(f"{BACKEND}/api/recommend", json={}, timeout=10)
    check("POST /api/recommend without sign-in is refused", refused.status_code == 401, f"status {refused.status_code}")


# ------------------------------------------------------------------------------ part 2
def app_flow_checks():
    print("\nPart 2 - app requests through the backend code (demo sign-in, in-memory database)")
    db = FakeDb()
    main.get_db = lambda: db
    main.init_firebase = lambda: True
    main._load_live_catalog()
    current = {"user": STUDENT}
    main.app.dependency_overrides[main.require_auth] = lambda: current["user"]
    client = TestClient(main.app)
    profile = {
        "kcseMeanGrade": "A-",
        "grades": {"Mathematics": "A", "English": "B+", "Kiswahili": "B", "Chemistry": "A",
                   "Biology": "A", "Physics": "A-", "Geography": "B+"},
        "interests": ["Healthcare & Clinical Medicine"], "strengths": ["Logical & Analytical Reasoning"],
        "aspirations": ["Medical Doctor (Physician/Surgeon)"],
    }

    r = client.post("/api/auth/whoami")
    check("student sign-in role", r.status_code == 200 and r.json()["role"] == "student", r.json().get("role", r.text))

    r = client.post("/api/recommend", json=profile)
    recs = r.json().get("recommendations", []) if r.status_code == 200 else []
    check("profile -> recommendations", r.status_code == 200 and 0 < len(recs) <= 3,
          "; ".join(f"{x['rank']}. {x['programme']['title']}" for x in recs) or r.text[:200])
    saved = [k for k in db.docs if k.startswith("students/smoke-student/recommendations/")]
    check("recommendation saved to the student's history", len(saved) == 1, f"{len(saved)} record(s)")

    whatif = dict(profile, grades=dict(profile["grades"], Physics="B"))
    r = client.post("/api/recommend?preview=true", json=whatif)
    still = [k for k in db.docs if k.startswith("students/smoke-student/recommendations/")]
    check("what-if preview answers and saves nothing", r.status_code == 200 and len(still) == 1,
          "; ".join(x["programme"]["title"] for x in r.json().get("recommendations", [])))

    r = client.post("/api/career-note", json=profile)
    check("career note", r.status_code == 200, str(r.json())[:160])

    r = client.get("/api/programmes")
    ids = [recs[0]["programme"]["id"], recs[1]["programme"]["id"]] if len(recs) > 1 else []
    by_id = {p["id"]: p for p in r.json()} if r.status_code == 200 else {}
    check("compare data for two programmes", bool(ids) and all(i in by_id for i in ids), ", ".join(ids))

    if recs:
        pid = recs[0]["programme"]["id"]
        r = client.post(f"/api/shortlist/{pid}")
        listed = client.get("/api/shortlist")
        check("save a programme to the shortlist", r.status_code == 200 and listed.status_code == 200
              and pid in str(listed.json()), pid)
        r = client.post("/api/feedback", json={"recommendation_id": pid, "rating": 5, "comments": "smoke test"})
        check("feedback", r.status_code == 200 and r.json().get("status") == "success", str(r.json()))

    current["user"] = ADMIN
    r = client.post("/api/auth/whoami")
    check("administrator sign-in role", r.status_code == 200 and r.json()["role"] == "administrator",
          f"{ADMIN_EMAIL}: {r.json().get('role', r.text)}")
    programme = next(p for p in main.CATALOG_BY_ID.values() if p.get("offeringUniversities"))
    uni = programme["offeringUniversities"][0]
    new_latest = round(float(uni["latestCutoff"]) + 0.5, 3)
    r = client.put(f"/api/admin/programmes/{programme['id']}/universities/{uni['kuccpsCode']}",
                   json={"latestCutoff": new_latest, "previousCutoff": float(uni["previousCutoff"])})
    after = next((u for u in r.json().get("offeringUniversities", []) if str(u["kuccpsCode"]) == str(uni["kuccpsCode"])), {}) \
        if r.status_code == 200 else {}
    check("admin cutoff update", r.status_code == 200 and after.get("latestCutoff") == new_latest,
          f"{programme['title']} at {uni['universityName']}: {uni['latestCutoff']} -> {after.get('latestCutoff')}")
    logs = client.get("/api/admin/audit-logs")
    check("audit log records the cutoff update", logs.status_code == 200 and "University Cutoff Updated" in logs.text)
    r = client.get("/api/admin/analytics/overview")
    check("admin analytics overview", r.status_code == 200, f"status {r.status_code}")
    main.app.dependency_overrides.clear()


if __name__ == "__main__":
    live_checks()
    app_flow_checks()
    print(f"\n{'ALL CHECKS PASSED' if not failures else 'FAILED: ' + ', '.join(failures)}")
    sys.exit(1 if failures else 0)
