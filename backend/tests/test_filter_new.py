"""Eligibility filtering of model output, checked against the real catalogue.

The programmes used here are picked by scanning the live catalogue with
meets_minimum_requirements(), not hard-coded, so the tests keep working when
catalogue requirements change. Each test fails with a clear message if the
catalogue no longer contains programmes suitable for the scenario.
"""
import numpy as np
import pytest
from fastapi.testclient import TestClient

import main
from kuccps import GRADE_POINTS, grade_to_points, meets_minimum_requirements
from main import (
    CATALOG_BY_TITLE,
    StudentProfilePayload,
    app,
    profile_to_feature_row,
    rate_limited_user,
    select_recommended_indices,
)

MBCHB = "Bachelor of Medicine and Bachelor of Surgery (MBChB)"


@pytest.fixture
def auth_override():
    app.dependency_overrides[rate_limited_user] = lambda: {"uid": "test_uid", "email": "test@strathmore.edu"}
    yield
    app.dependency_overrides.clear()


def _mean_grade_as_endpoint_computes_it(payload: StudentProfilePayload) -> str:
    _, _, mean_grade = profile_to_feature_row(payload)
    assert grade_to_points(mean_grade) >= GRADE_POINTS["C+"], f"mean grade {mean_grade} is below C+"
    return mean_grade


def _split_catalogue(grades, mean_grade):
    eligible, ineligible = [], []
    for title, prog in CATALOG_BY_TITLE.items():
        if prog.get("status") == "inactive":
            continue
        if meets_minimum_requirements(grades, prog["minimumSubjectRequirements"], mean_grade):
            eligible.append(title)
        else:
            ineligible.append(title)
    return eligible, ineligible


def test_select_recommended_indices_returns_only_eligible_in_probability_order():
    payload = StudentProfilePayload(
        kcseMeanGrade="B",
        grades={
            "Mathematics": "B",
            "English": "B",
            "Kiswahili": "B",
            "Chemistry": "B",
            "History & Government": "B",
            "Business Studies": "B",
            "Christian Religious Education (CRE)": "B",
        },
    )
    mean_grade = _mean_grade_as_endpoint_computes_it(payload)
    eligible, ineligible = _split_catalogue(payload.grades, mean_grade)
    if len(eligible) < 2 or len(ineligible) < 1:
        pytest.fail(
            "Could not find 2 eligible and 1 ineligible programme in the catalogue for this student "
            f"(eligible={len(eligible)}, ineligible={len(ineligible)})"
        )

    # The ineligible programme gets the highest probability, and the eligible
    # ones are listed in the opposite order to their probabilities, so a
    # result that ignored eligibility or kept array order would fail.
    classes = np.array([eligible[0], ineligible[0], eligible[1]])
    proba = np.array([0.20, 0.50, 0.30])
    assert proba.ndim == 1

    top_idx, eligible_mask = select_recommended_indices(proba, classes, payload.grades, mean_grade)

    assert [classes[i] for i in top_idx] == [eligible[1], eligible[0]]
    assert eligible_mask == [True, False, True]


def test_select_recommended_indices_empty_when_student_fails_every_candidate():
    payload = StudentProfilePayload(
        kcseMeanGrade="C+",
        grades={
            "Mathematics": "C+",
            "English": "C+",
            "Kiswahili": "C+",
            "Chemistry": "C+",
            "Geography": "C+",
            "Business Studies": "C+",
            "Christian Religious Education (CRE)": "C+",
        },
    )
    mean_grade = _mean_grade_as_endpoint_computes_it(payload)
    _, ineligible = _split_catalogue(payload.grades, mean_grade)
    if len(ineligible) < 3:
        pytest.fail(f"Could not find 3 programmes this C+ student fails in the catalogue (found {len(ineligible)})")

    classes = np.array(ineligible[:3])
    proba = np.array([0.50, 0.30, 0.20])

    top_idx, eligible_mask = select_recommended_indices(proba, classes, payload.grades, mean_grade)

    assert top_idx == []
    assert eligible_mask == [False, False, False]


def test_endpoint_never_returns_ineligible_mbchb(auth_override, monkeypatch):
    monkeypatch.setattr(main, "_persist_recommendation", lambda *a, **k: None)

    # Straight As but no Biology, which MBChB requires.
    payload = StudentProfilePayload(
        fullName="Test Candidate",
        kcseMeanGrade="A",
        grades={
            "Mathematics": "A",
            "English": "A",
            "Kiswahili": "A",
            "Chemistry": "A",
            "Physics": "A",
            "Geography": "A",
            "History & Government": "A",
        },
        interests=["Healthcare & Clinical Medicine"],
        strengths=["Perseverance & Discipline"],
        aspirations=["Medical Doctor (Physician/Surgeon)"],
    )
    mean_grade = _mean_grade_as_endpoint_computes_it(payload)
    if MBCHB not in CATALOG_BY_TITLE:
        pytest.fail(f"{MBCHB} is not in the catalogue")
    assert not meets_minimum_requirements(
        payload.grades, CATALOG_BY_TITLE[MBCHB]["minimumSubjectRequirements"], mean_grade
    ), "this student was meant to be ineligible for MBChB"

    resp = TestClient(app).post("/api/recommend", json=payload.model_dump())

    assert resp.status_code == 200, resp.text
    recs = resp.json()["recommendations"]
    titles = [r["programme"]["title"] for r in recs]
    assert MBCHB not in titles
    for r in recs:
        assert meets_minimum_requirements(payload.grades, r["programme"]["minimumSubjectRequirements"], mean_grade), (
            f"{r['programme']['title']} was returned but the student does not meet its requirements"
        )
