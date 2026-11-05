import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.main import (
    CATALOG_BY_TITLE,
    StudentProfilePayload,
    app,
    profile_to_feature_row,
    rate_limited_user,
    select_recommended_indices,
)
from backend.kuccps import grade_to_points, meets_minimum_requirements, points_to_grade


@pytest.fixture
def auth_override():
    app.dependency_overrides[rate_limited_user] = lambda: {"uid": "test_uid", "email": "test@strathmore.edu"}
    yield
    app.dependency_overrides.clear()


def test_select_recommended_indices_two_eligible():
    grades = {
        "Mathematics": "B+",
        "English": "B+",
        "Kiswahili": "B+",
        "Chemistry": "B+",
        "Biology": "B+",
        "Physics": "B+",
        "Geography": "B+",
    }
    mean_pts = round(sum(grade_to_points(g) for g in grades.values()) / len(grades))
    mean_grade = points_to_grade(mean_pts)
    assert grade_to_points(mean_grade) >= grade_to_points("C+")

    eligible = []
    ineligible = []
    for title, prog in CATALOG_BY_TITLE.items():
        if prog.get("status") == "inactive":
            continue
        reqs = prog.get("minimumSubjectRequirements", {})
        if meets_minimum_requirements(grades, reqs, mean_grade):
            eligible.append(title)
        else:
            ineligible.append(title)

    if len(eligible) < 2 or len(ineligible) < 1:
        pytest.fail(f"Could not find 2 eligible and 1 ineligible programmes (eligible={len(eligible)}, ineligible={len(ineligible)})")

    selected_classes = [eligible[0], eligible[1], ineligible[0]]
    classes = np.array(selected_classes)
    proba = np.array([0.60, 0.30, 0.10])

    top_idx, eligible_mask = select_recommended_indices(proba, classes, grades, mean_grade)
    selected_titles = [classes[i] for i in top_idx]

    assert selected_titles == [eligible[0], eligible[1]]
    assert len(selected_titles) == 2


def test_select_recommended_indices_none_eligible():
    grades = {
        "Mathematics": "C+",
        "English": "C+",
        "Kiswahili": "C+",
        "Chemistry": "C+",
        "Geography": "C+",
        "Business Studies": "C+",
        "Christian Religious Education (CRE)": "C+",
    }
    mean_pts = round(sum(grade_to_points(g) for g in grades.values()) / len(grades))
    mean_grade = points_to_grade(mean_pts)
    assert grade_to_points(mean_grade) >= grade_to_points("C+")

    ineligible = []
    for title, prog in CATALOG_BY_TITLE.items():
        if prog.get("status") == "inactive":
            continue
        reqs = prog.get("minimumSubjectRequirements", {})
        if not meets_minimum_requirements(grades, reqs, mean_grade):
            ineligible.append(title)

    if len(ineligible) < 3:
        pytest.fail(f"Could not find at least 3 ineligible programmes for student with mean >= C+ (found {len(ineligible)})")

    selected_classes = ineligible[:3]
    classes = np.array(selected_classes)
    proba = np.array([0.50, 0.30, 0.20])

    top_idx, eligible_mask = select_recommended_indices(proba, classes, grades, mean_grade)
    assert top_idx == []


def test_endpoint_excludes_ineligible_mbchb(auth_override):
    mbchb = CATALOG_BY_TITLE["Bachelor of Medicine and Bachelor of Surgery (MBChB)"]
    grades = {
        "Mathematics": "A",
        "English": "A",
        "Kiswahili": "A",
        "Chemistry": "A",
        "Physics": "A",
        "Geography": "A",
        "History & Government": "A",
    }
    payload = StudentProfilePayload(
        fullName="Test Candidate",
        kcseMeanGrade="A",
        grades=grades,
        interests=["Healthcare & Clinical Medicine"],
        strengths=["Perseverance & Discipline"],
        aspirations=["Medical Doctor (Physician/Surgeon)"],
    )

    _, _, mean_grade = profile_to_feature_row(payload)
    assert not meets_minimum_requirements(grades, mbchb["minimumSubjectRequirements"], mean_grade)

    client = TestClient(app)
    resp = client.post("/api/recommend", json=payload.model_dump())
    assert resp.status_code == 200
    data = resp.json()
    assert "recommendations" in data
    recs = data["recommendations"]
    titles = [r["programme"]["title"] for r in recs]
    assert mbchb["title"] not in titles
    for r in recs:
        assert meets_minimum_requirements(grades, r["programme"]["minimumSubjectRequirements"], mean_grade)
