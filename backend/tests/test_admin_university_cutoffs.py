"""Admins edit each university's own cutoff for a programme - the figure students
are compared with. Uses an in-memory stand-in for Firestore, so nothing real is written."""

import pydantic
import pytest
from fastapi import HTTPException

import main

pytestmark = pytest.mark.skipif(main._pipeline is None, reason="rf_model_pipeline.pkl not trained yet")

ADMIN = {"uid": "admin-1", "email": "admin@example.com"}


class _Snap:
    def __init__(self, data):
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return self._data


class _ProgrammeDoc:
    def __init__(self, store, doc_id):
        self.store, self.id = store, doc_id

    def get(self):
        return _Snap(self.store.get(self.id))

    def set(self, data):
        self.store[self.id] = dict(data)

    def update(self, fields):
        self.store[self.id].update(fields)


class _AuditDoc:
    def __init__(self, log):
        self.log = log

    def set(self, entry):
        self.log.append(entry)


class _Collection:
    def __init__(self, docs=None, log=None):
        self.docs, self.log = docs, log

    def document(self, doc_id=None):
        return _AuditDoc(self.log) if self.log is not None else _ProgrammeDoc(self.docs, doc_id)


class _FakeDb:
    def __init__(self):
        self.programmes = {}
        self.audit = []

    def collection(self, name):
        return _Collection(log=self.audit) if name == "audit_logs" else _Collection(docs=self.programmes)


@pytest.fixture
def db(monkeypatch):
    fake = _FakeDb()
    monkeypatch.setattr(main, "get_db", lambda: fake)
    monkeypatch.setattr(main, "_load_live_catalog", lambda: None)  # the real reload reads Firestore
    return fake


def _first_programme_and_university():
    programme = next(p for p in main.PROGRAMMES if main.CATALOG_BY_ID[p["id"]]["offeringUniversities"])
    programme = main.CATALOG_BY_ID[programme["id"]]
    return programme, programme["offeringUniversities"][0]


def test_an_edit_changes_only_that_universitys_cutoffs(db):
    programme, uni = _first_programme_and_university()
    others_before = [dict(u) for u in programme["offeringUniversities"][1:]]
    main.update_university_cutoff(
        programme["id"], str(uni["kuccpsCode"]),
        main.UniversityCutoffPayload(latestCutoff=30.5, previousCutoff=29.25), ADMIN,
    )
    saved = db.programmes[programme["id"]]["offeringUniversities"]
    assert (saved[0]["latestCutoff"], saved[0]["previousCutoff"]) == (30.5, 29.25)
    assert saved[1:] == others_before


def test_the_edit_is_recorded_in_the_audit_log(db):
    programme, uni = _first_programme_and_university()
    main.update_university_cutoff(
        programme["id"], str(uni["kuccpsCode"]),
        main.UniversityCutoffPayload(latestCutoff=30.5, previousCutoff=29.25), ADMIN,
    )
    assert len(db.audit) == 1
    entry = db.audit[0]
    assert entry["action"] == "University Cutoff Updated"
    assert entry["actor"] == "admin@example.com"
    assert uni["universityName"] in entry["details"]


def test_an_unknown_university_code_is_refused(db):
    programme, _ = _first_programme_and_university()
    with pytest.raises(HTTPException) as err:
        main.update_university_cutoff(
            programme["id"], "0000000", main.UniversityCutoffPayload(latestCutoff=30, previousCutoff=30), ADMIN
        )
    assert err.value.status_code == 404
    assert db.programmes == {} and db.audit == []


def test_an_unknown_programme_is_refused(db):
    with pytest.raises(HTTPException) as err:
        main.update_university_cutoff(
            "prog_nope", "1", main.UniversityCutoffPayload(latestCutoff=30, previousCutoff=30), ADMIN
        )
    assert err.value.status_code == 404


@pytest.mark.parametrize("bad", [0, -3, 48.5, 450])
def test_cutoffs_outside_the_kuccps_scale_are_rejected(bad):
    with pytest.raises(pydantic.ValidationError):
        main.UniversityCutoffPayload(latestCutoff=bad, previousCutoff=30)
    with pytest.raises(pydantic.ValidationError):
        main.UniversityCutoffPayload(latestCutoff=30, previousCutoff=bad)


def test_the_in_memory_catalogue_is_not_changed_by_a_refused_edit(db):
    programme, uni = _first_programme_and_university()
    before = (uni["latestCutoff"], uni["previousCutoff"])
    with pytest.raises(HTTPException):
        main.update_university_cutoff(
            programme["id"], "0000000", main.UniversityCutoffPayload(latestCutoff=30, previousCutoff=30), ADMIN
        )
    assert (uni["latestCutoff"], uni["previousCutoff"]) == before
