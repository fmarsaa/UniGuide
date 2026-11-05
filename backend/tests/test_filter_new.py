"""New tests for the eligibility filter and API response.

These tests are added before any source changes, so test (a) is expected to fail
with the old fallback behaviour. After the source edits are applied all tests
should pass.
"""

import numpy as np
import pytest
from backend.main import select_recommended_indices, profile_to_feature_row, app
from backend.kuccps import meets_minimum_requirements
from backend.programmes_catalog import CATALOG_BY_TITLE

# ---------------------------------------------------------------------------
# Pytest fixture that temporarily overrides the authentication dependency
# ---------------------------------------------------------------------------
@pytest.fixture
def auth_override():
    # The endpoint uses `rate_limited_user` to fetch the decoded token.
    # We'll replace it with a dummy that returns a fixed uid/email.
    from backend.main import rate_limited_user
    app.dependency_overrides[rate_limited_user] = lambda: {"uid": "test_user", "email": "test@example.com"}
    yield
    # Clear overrides after the test
    app.dependency_overrides.clear()

# ---------------------------------------------------------------------------
# Test (a) – exactly two eligible programmes, expect only those two returned
# ---------------------------------------------------------------------------
def test_select_recommended_indices_two_eligible():
    # Choose three real programmes from the catalogue
    prog_mbchb = CATALOG_BY_TITLE["Bachelor of Medicine and Bachelor of Surgery (MBChB)"]
    prog_ics = CATALOG_BY_TITLE["Bachelor of Science in Informatics and Computer Science"]
    prog_eee = CATALOG_BY_TITLE["Bachelor of Science in Electrical and Electronic Engineering"]

    # Grades that satisfy MBChB and ICS, but not EEE (missing Physics)
    grades = {
        "Mathematics": "A",
        "English": "A",
        "Kiswahili": "A",
        "Chemistry": "A",
        "Biology": "A",   # required for MBChB
        # No Physics –> fails EEE
    }

    # Pre‑condition: exactly two eligible programmes
    eligible_flags = [
        meets_minimum_requirements(grades, prog["minimumSubjectRequirements"], "C+")
        for prog in (prog_mbchb, prog_ics, prog_eee)
    ]
    assert eligible_flags == [True, True, False]

    # Build a 1‑D probability array (same shape as main.py passes)
    classes = np.array([prog_mbchb["title"], prog_ics["title"], prog_eee["title"]])
    proba = np.array([0.6, 0.35, 0.05])  # 1‑D

    top_idx, _ = select_recommended_indices(proba, classes, grades, "C+")
    selected_titles = [classes[i] for i in top_idx]

    assert selected_titles == [prog_mbchb["title"], prog_ics["title"]]
    assert len(selected_titles) == 2

# ---------------------------------------------------------------------------
# Test (b) – student fails every programme, expect empty result list
# ---------------------------------------------------------------------------
def test_select_recommended_indices_none_eligible():
    # Pick three programmes (any three real ones)
    prog_titles = [
        CATALOG_BY_TITLE["Bachelor of Medicine and Bachelor of Surgery (MBChB)"],
        CATALOG_BY_TITLE["Bachelor of Science in Informatics and Computer Science"],
        CATALOG_BY_TITLE["Bachelor of Science in Electrical and Electronic Engineering"],
    ]
    # Grades that are D in all compulsory subjects – will fail all minimum reqs
    grades = {"Mathematics": "D", "English": "D", "Kiswahili": "D", "Chemistry": "D"}

    # Pre‑condition: none eligible
    for prog in prog_titles:
        assert not meets_minimum_requirements(
            grades, prog["minimumSubjectRequirements"], "C+"
        )

    classes = np.array([p["title"] for p in prog_titles])
    proba = np.array([0.33, 0.33, 0.34])

    top_idx, _ = select_recommended_indices(proba, classes, grades, "C+")
    assert top_idx == []

# ---------------------------------------------------------------------------
# Test (c) – endpoint integration, MBChB not eligible but other programmes are
# ---------------------------------------------------------------------------
def test_endpoint_excludes_ineligible_mbchb(auth_override):
    mbchb = CATALOG_BY_TITLE["Bachelor of Medicine and Bachelor of Surgery (MBChB)"]
    # Grades missing Biology –> MBChB not eligible
    grades = {
        "Mathematics": "A",
        "English": "A",
        "Kiswahili": "A",
        "Chemistry": "A",
        # Biology omitted deliberately
    }
    payload = {
        "grades": grades,
        "interests": ["Healthcare & Clinical Medicine"],
        "strengths": ["Perseverance & Discipline"],
        "aspirations": ["Medical Doctor (Physician/Surgeon)"],
    }

    # Compute mean_grade using the same helper the endpoint uses
    _, _, mean_grade = profile_to_feature_row(payload)

    # Pre‑condition: MBChB should be ineligible
    assert not meets_minimum_requirements(
        grades, mbchb["minimumSubjectRequirements"], mean_grade
    )

    from fastapi.testclient import TestClient
    client = TestClient(app)
    resp = client.post("/api/recommend", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    titles = [r["programme"]["title"] for r in data["recommendations"]]
    assert mbchb["title"] not in titles
    # Every returned programme must satisfy its own requirements
    for r in data["recommendations"]:
        prog = r["programme"]
        assert meets_minimum_requirements(
            grades, prog["minimumSubjectRequirements"], mean_grade
        )
