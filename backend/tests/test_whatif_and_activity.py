"""The "what if" simulator asks for a real recommendation without saving it, and the
admin activity charts count recommendations, feedback and new students per day.
Uses in-memory stand-ins for Firestore, so nothing real is read or written."""

from datetime import datetime, timedelta, timezone

import pytest

import main

pytestmark = pytest.mark.skipif(main._pipeline is None, reason="rf_model_pipeline.pkl not trained yet")

USER = {"uid": "student-1", "email": "student@example.com", "email_verified": True}
ADMIN = {"uid": "admin-1", "email": "admin@example.com"}


def _payload():
    return main.StudentProfilePayload(
        kcseMeanGrade="B",
        grades={"Mathematics": "B", "English": "B", "Kiswahili": "B", "Chemistry": "B", "Physics": "B"},
        interests=["Software Development & Coding"],
        skills=["Python & Software Programming"],
        strengths=["Logical & Analytical Reasoning"],
        aspirations=[],
    )


# ----------------------------------------------------------------- what-if preview
def test_a_preview_request_saves_nothing(monkeypatch):
    saved = []
    monkeypatch.setattr(main, "_persist_recommendation", lambda *a, **k: saved.append(a))
    results = main.get_recommendations(_payload(), USER, preview=True)
    assert len(results) == 3
    assert saved == []


def test_a_normal_request_is_still_saved(monkeypatch):
    saved = []
    monkeypatch.setattr(main, "_persist_recommendation", lambda *a, **k: saved.append(a))
    main.get_recommendations(_payload(), USER)
    assert len(saved) == 1


def test_a_preview_gives_the_same_answer_as_a_real_request(monkeypatch):
    monkeypatch.setattr(main, "_persist_recommendation", lambda *a, **k: None)
    real = [r["programme"]["id"] for r in main.get_recommendations(_payload(), USER)]
    preview = [r["programme"]["id"] for r in main.get_recommendations(_payload(), USER, preview=True)]
    assert real == preview


# ------------------------------------------------------------------ admin activity
class _Doc:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return self._data


class _Stream:
    def __init__(self, docs):
        self._docs = docs

    def stream(self):
        return [_Doc(d) for d in self._docs]


class _FakeDb:
    def __init__(self, recommendations=(), feedback=(), students=()):
        self._recommendations, self._feedback, self._students = list(recommendations), list(feedback), list(students)

    def collection_group(self, name):
        return _Stream(self._recommendations if name == "recommendations" else self._feedback)

    def collection(self, name):
        return _Stream(self._students)


def _days_ago(n):
    return datetime.now(timezone.utc) - timedelta(days=n)


def _by_date(result):
    return {d["date"]: d for d in result["days"]}


def test_activity_is_counted_per_day(monkeypatch):
    monkeypatch.setattr(main, "get_db", lambda: _FakeDb(
        recommendations=[{"createdAt": _days_ago(0)}, {"createdAt": _days_ago(0)}, {"createdAt": _days_ago(2)}],
        feedback=[{"submittedAt": _days_ago(1), "rating": 4}],
        students=[{"createdAt": _days_ago(2)}, {"createdAt": _days_ago(2)}],
    ))
    result = main.activity_analytics(days=30, decoded=ADMIN)
    days = _by_date(result)
    today, two_days_ago, yesterday = (
        _days_ago(n).date().isoformat() for n in (0, 2, 1)
    )
    assert days[today]["recommendations"] == 2
    assert days[two_days_ago]["recommendations"] == 1
    assert days[yesterday]["feedback"] == 1
    assert days[two_days_ago]["newStudents"] == 2


def test_the_window_has_one_entry_per_day_oldest_first(monkeypatch):
    monkeypatch.setattr(main, "get_db", lambda: _FakeDb())
    result = main.activity_analytics(days=30, decoded=ADMIN)
    dates = [d["date"] for d in result["days"]]
    assert len(dates) == 30
    assert dates == sorted(dates)
    assert dates[-1] == datetime.now(timezone.utc).date().isoformat()


def test_totals_include_activity_older_than_the_window(monkeypatch):
    monkeypatch.setattr(main, "get_db", lambda: _FakeDb(
        recommendations=[{"createdAt": _days_ago(200)}, {"createdAt": _days_ago(1)}],
        feedback=[{"submittedAt": _days_ago(300), "rating": 5}, {"submittedAt": _days_ago(1), "rating": 3}],
        students=[{"createdAt": _days_ago(400)}],
    ))
    totals = main.activity_analytics(days=30, decoded=ADMIN)["totals"]
    assert totals == {"students": 1, "recommendations": 2, "feedback": 2, "averageRating": 4.0}


def test_the_average_rating_is_empty_when_there_is_no_feedback(monkeypatch):
    monkeypatch.setattr(main, "get_db", lambda: _FakeDb())
    assert main.activity_analytics(days=30, decoded=ADMIN)["totals"]["averageRating"] is None


@pytest.mark.parametrize("asked, expected", [(1, 7), (3, 7), (30, 30), (500, 90)])
def test_the_number_of_days_is_kept_in_a_sensible_range(monkeypatch, asked, expected):
    monkeypatch.setattr(main, "get_db", lambda: _FakeDb())
    assert len(main.activity_analytics(days=asked, decoded=ADMIN)["days"]) == expected


def test_records_with_no_timestamp_do_not_break_the_counts(monkeypatch):
    monkeypatch.setattr(main, "get_db", lambda: _FakeDb(recommendations=[{}, {"createdAt": None}], students=[{}]))
    result = main.activity_analytics(days=30, decoded=ADMIN)
    assert result["totals"]["recommendations"] == 2
    assert sum(d["recommendations"] for d in result["days"]) == 0
