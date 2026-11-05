import os
for v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(v, "1")

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

# Tests must never reach the real Firebase project. Blank the credential
# variables before main is imported: load_dotenv() does not override variables
# that already exist, so Firebase Admin stays disabled and the import-time
# catalogue sync in main cannot backfill programmes into the live Firestore.
for v in ("FIREBASE_SERVICE_ACCOUNT", "FIREBASE_SERVICE_ACCOUNT_JSON", "FIREBASE_SERVICE_ACCOUNT_PATH"):
    os.environ[v] = ""

import pytest

import main


@pytest.fixture(autouse=True)
def _fresh_abuse_counters():
    """Each test starts with empty rate-limit and duplicate-submission memory."""
    main._recent_requests.clear()
    main._last_submission.clear()
    yield


@pytest.fixture(autouse=True)
def _no_firestore_writes(monkeypatch):
    """Recommendation results are never persisted during tests. A test that
    wants to observe the call patches _persist_recommendation again itself."""
    monkeypatch.setattr(main, "_persist_recommendation", lambda *a, **k: None)
    yield
