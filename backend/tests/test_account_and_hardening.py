"""Account deletion, the guards against abuse (too many requests, oversized requests,
the same profile saved twice by a double tap) and the model version that is recorded
with every result. Uses in-memory stand-ins for Firestore and Firebase Auth."""

import json

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import main
import train_random_forest as trainer


# ------------------------------------------------------------ in-memory Firestore
class _Snap:
    def __init__(self, doc_id, data):
        self.id, self._data, self.exists = doc_id, data, data is not None

    def to_dict(self):
        return self._data


class _Doc:
    def __init__(self, db, path):
        self.db, self.path = db, path

    def collection(self, name):
        return _Coll(self.db, self.path + (name,))

    def get(self):
        return _Snap(self.path[-1], self.db.docs.get(self.path))

    def set(self, data, merge=False):
        self.db.docs[self.path] = data

    def delete(self):
        self.db.docs.pop(self.path, None)


class _Coll:
    def __init__(self, db, path):
        self.db, self.path = db, path

    def document(self, doc_id=None):
        return _Doc(self.db, self.path + (doc_id or f"auto{len(self.db.docs)}",))

    def stream(self):
        n = len(self.path)
        return [_Snap(p[-1], d) for p, d in list(self.db.docs.items()) if len(p) == n + 1 and p[:n] == self.path]


class _FakeDb:
    def __init__(self):
        self.docs = {}

    def collection(self, name):
        return _Coll(self, (name,))

    def put(self, *path):
        self.docs[path] = {"x": 1}


@pytest.fixture
def db(monkeypatch):
    fake = _FakeDb()
    monkeypatch.setattr(main, "get_db", lambda: fake)
    monkeypatch.setattr(main, "admin_emails", lambda: {"boss@example.com"})
    return fake


@pytest.fixture
def auth_deleted(monkeypatch):
    deleted = []
    monkeypatch.setattr(main, "delete_auth_user", lambda uid: deleted.append(uid))
    return deleted


def _student_with_data(db, uid):
    db.put("students", uid)
    db.put("students", uid, "recommendations", "r1")
    db.put("students", uid, "shortlist", "p1")
    db.put("students", uid, "feedback", "f1")


# ----------------------------------------------------------- account deletion
def test_deleting_an_account_removes_everything_stored_about_the_student(db, auth_deleted):
    _student_with_data(db, "s1")
    result = main.delete_my_account(main.DeleteAccountPayload(confirm="DELETE"), {"uid": "s1", "email": "s1@example.com"})
    assert result == {"deleted": True}
    assert not [p for p in db.docs if p[:2] == ("students", "s1")]
    assert auth_deleted == ["s1"]


def test_deleting_one_account_leaves_other_students_alone(db, auth_deleted):
    _student_with_data(db, "s1")
    _student_with_data(db, "s2")
    main.delete_my_account(main.DeleteAccountPayload(confirm="DELETE"), {"uid": "s1", "email": "s1@example.com"})
    assert len([p for p in db.docs if p[:2] == ("students", "s2")]) == 4


def test_deletion_needs_the_explicit_confirmation_word(db, auth_deleted):
    _student_with_data(db, "s1")
    with pytest.raises(HTTPException) as err:
        main.delete_my_account(main.DeleteAccountPayload(confirm=""), {"uid": "s1", "email": "s1@example.com"})
    assert err.value.status_code == 400
    assert auth_deleted == [] and ("students", "s1") in db.docs


def test_an_administrator_cannot_delete_their_account_here(db, auth_deleted):
    with pytest.raises(HTTPException) as err:
        main.delete_my_account(main.DeleteAccountPayload(confirm="DELETE"), {"uid": "a1", "email": "Boss@example.com"})
    assert err.value.status_code == 403
    assert auth_deleted == []


def test_the_audit_log_records_a_deletion_without_naming_the_student(db, auth_deleted):
    _student_with_data(db, "s1")
    main.delete_my_account(main.DeleteAccountPayload(confirm="DELETE"), {"uid": "s1", "email": "s1@example.com"})
    entries = [d for p, d in db.docs.items() if p[0] == "audit_logs"]
    assert len(entries) == 1
    assert "s1" not in json.dumps(entries[0], default=str)


# ------------------------------------------------------------------ rate limit
def test_requests_beyond_the_limit_are_refused_until_the_window_passes():
    for i in range(main.RATE_LIMIT_REQUESTS):
        main.check_rate_limit("u", now=100.0 + i * 0.01)
    with pytest.raises(HTTPException) as err:
        main.check_rate_limit("u", now=101.0)
    assert err.value.status_code == 429
    main.check_rate_limit("u", now=100.0 + main.RATE_LIMIT_WINDOW_SECONDS + 5)  # window has passed


def test_one_users_requests_do_not_count_against_another():
    for _ in range(main.RATE_LIMIT_REQUESTS):
        main.check_rate_limit("busy", now=1.0)
    main.check_rate_limit("quiet", now=1.0)


# ---------------------------------------------------------- oversized requests
def test_a_request_that_is_far_too_large_is_refused():
    client = TestClient(main.app)
    response = client.post(
        "/api/recommend", content=b"x" * (main.MAX_BODY_BYTES + 1), headers={"content-type": "application/json"}
    )
    assert response.status_code == 413


# ------------------------------------------------------ repeated submissions
def _payload(mean="B"):
    return main.StudentProfilePayload(
        kcseMeanGrade=mean,
        grades={"Mathematics": "B", "English": "B", "Kiswahili": "B", "Chemistry": "B"},
    )


def test_the_same_profile_sent_twice_in_a_moment_is_one_duplicate():
    assert main._is_duplicate_submission("u", _payload(), now=10.0) is False
    assert main._is_duplicate_submission("u", _payload(), now=11.0) is True


def test_the_same_profile_sent_again_later_is_not_a_duplicate():
    main._is_duplicate_submission("u", _payload(), now=10.0)
    assert main._is_duplicate_submission("u", _payload(), now=10.0 + main.DUPLICATE_WINDOW_SECONDS + 1) is False


def test_a_changed_profile_is_not_a_duplicate():
    main._is_duplicate_submission("u", _payload("B"), now=10.0)
    assert main._is_duplicate_submission("u", _payload("A"), now=11.0) is False


# --------------------------------------------------------------- model version
def test_the_run_record_ties_a_model_to_its_code_data_and_libraries():
    import pandas as pd

    record = trainer.build_run_record(pd.DataFrame({"a": [1, 2, 3]}))
    assert record["model_version"].startswith("rf-")
    assert len(record["dataset"]["sha256_of_row_hashes"]) == 64
    assert {"python", "scikit-learn", "numpy", "pandas"} <= set(record["versions"])
    assert record["seeds"]["model"] == 42


def test_the_dataset_fingerprint_changes_when_the_data_changes():
    import pandas as pd

    a = trainer.build_run_record(pd.DataFrame({"a": [1, 2, 3]}))["dataset"]["sha256_of_row_hashes"]
    b = trainer.build_run_record(pd.DataFrame({"a": [1, 2, 4]}))["dataset"]["sha256_of_row_hashes"]
    assert a != b


def test_a_model_without_a_recorded_version_still_reports_one(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "METRICS_PATH", str(tmp_path / "missing.json"))
    assert main.model_version().startswith("rf-") or main.model_version() == "unknown"


def test_a_recorded_version_is_the_one_reported(monkeypatch, tmp_path):
    path = tmp_path / "m.json"
    path.write_text(json.dumps({"model_version": "rf-20261020-abc1234"}))
    monkeypatch.setattr(main, "METRICS_PATH", str(path))
    assert main.model_version() == "rf-20261020-abc1234"
