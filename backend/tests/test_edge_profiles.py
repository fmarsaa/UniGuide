"""Robustness check with unusual profiles written for testing. These are test inputs, not a user
study: they check that the recommender never crashes, answers with at most three programmes the
student is eligible for (fewer when fewer are eligible), never tells a student they qualify when a
required subject grade is missing or too low, and refuses a mean grade below C+ with a clear message."""

import pytest

import main
from kuccps import COMPULSORY_SUBJECTS, GRADE_POINTS, grade_to_points, meets_minimum_requirements

pytestmark = pytest.mark.skipif(main._pipeline is None, reason="rf_model_pipeline.pkl not trained yet")

USER = {"uid": "edge-test", "email": "edge@example.com", "email_verified": True}
ALL = ["Mathematics", "English", "Kiswahili", "Chemistry", "Biology", "Physics", "History", "Geography", "Business Studies"]


def grades(level, subjects=None):
    return {s: level for s in (subjects or COMPULSORY_SUBJECTS)}


PROFILES = {
    "all A, every subject": dict(kcseMeanGrade="A", grades=grades("A", ALL)),
    "all A-, compulsory only": dict(kcseMeanGrade="A-", grades=grades("A-")),
    "all C-, every subject": dict(kcseMeanGrade="C-", grades=grades("C-", ALL)),
    "all E": dict(kcseMeanGrade="E", grades=grades("E")),
    "strong sciences, weak English": dict(kcseMeanGrade="B", grades={**grades("A", ["Mathematics", "Chemistry", "Biology", "Physics"]), "English": "D", "Kiswahili": "C"}),
    "strong arts, weak maths": dict(kcseMeanGrade="B", grades={**grades("A", ["English", "Kiswahili", "History", "Geography"]), "Mathematics": "D", "Chemistry": "D+"}),
    "business track": dict(kcseMeanGrade="B+", grades={**grades("B+", ["Mathematics", "English", "Kiswahili", "Chemistry"]), "Business Studies": "A", "Geography": "B"}),
    "no career, no choices": dict(kcseMeanGrade="C+", grades=grades("C+"), aspirations=[]),
    "career that clashes with the grades": dict(kcseMeanGrade="C+", grades=grades("C+"), aspirations=["Surgeon"]),
    "lowest passing mean, high maths": dict(kcseMeanGrade="C+", grades={**grades("C+"), "Mathematics": "A"}),
    "a mean grade in lower case": dict(kcseMeanGrade="b+", grades=grades("b+")),
    "extra unfamiliar subject": dict(kcseMeanGrade="B", grades={**grades("B"), "Computer Studies": "A"}),
}
for level in ("A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "E"):
    PROFILES[f"flat {level}"] = dict(kcseMeanGrade=level, grades=grades(level, ALL))


def _eligible_count(payload):
    count = 0
    for title in main._pipeline.classes_:
        programme = main.CATALOG_BY_TITLE.get(title, {})
        if programme.get("status") == "inactive":
            continue
        if meets_minimum_requirements(payload.grades, programme["minimumSubjectRequirements"], payload.kcseMeanGrade):
            count += 1
    return count


@pytest.mark.parametrize("name", sorted(PROFILES))
def test_an_unusual_profile_still_gets_three_honest_results(name):
    profile = PROFILES[name]
    if grade_to_points(profile["kcseMeanGrade"]) < GRADE_POINTS["C+"]:
        # Degree programmes only: a mean below C+ is refused at the request boundary.
        with pytest.raises(ValueError, match=r"minimum KCSE mean grade of C\+"):
            main.StudentProfilePayload(**profile)
        return

    payload = main.StudentProfilePayload(**profile)
    response = main.get_recommendations(payload, USER, preview=True)
    results = response["recommendations"]
    assert len(results) == min(3, _eligible_count(payload)), f"{name}: wrong number of results"
    assert len({r["programme"]["title"] for r in results}) == len(results)
    if not results:
        assert response["message"]
    for r in results:
        programme = r["programme"]
        assert r["meetsMinimumRequirements"] is True, f"{name}: {programme['title']} returned but not eligible"
        assert meets_minimum_requirements(
            payload.grades, programme.get("minimumSubjectRequirements") or {}, payload.kcseMeanGrade
        ), f"{name}: {programme['title']} marked as meeting requirements when it does not"
        assert "confidence" not in r["primaryReason"].lower()
