"""Robustness check with unusual profiles written for testing. These are test inputs, not a user
study: they check that the recommender never crashes, always answers with three programmes, and never
tells a student they qualify when a required subject grade is missing or too low."""

import pytest

import main
from kuccps import COMPULSORY_SUBJECTS, meets_minimum_requirements

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
    "career that clashes with the grades": dict(kcseMeanGrade="D", grades=grades("D"), aspirations=["Surgeon"]),
    "lowest passing mean, high maths": dict(kcseMeanGrade="C", grades={**grades("C"), "Mathematics": "A"}),
    "a mean grade in lower case": dict(kcseMeanGrade="b+", grades=grades("b+")),
    "extra unfamiliar subject": dict(kcseMeanGrade="B", grades={**grades("B"), "Computer Studies": "A"}),
}
for level in ("A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "E"):
    PROFILES[f"flat {level}"] = dict(kcseMeanGrade=level, grades=grades(level, ALL))


@pytest.mark.parametrize("name", sorted(PROFILES))
def test_an_unusual_profile_still_gets_three_honest_results(name):
    payload = main.StudentProfilePayload(**PROFILES[name])
    results = main.get_recommendations(payload, USER, preview=True)
    assert len(results) == 3
    assert len({r["programme"]["title"] for r in results}) == 3
    for r in results:
        if r["meetsMinimumRequirements"]:
            programme = r["programme"]
            assert meets_minimum_requirements(payload.grades, programme.get("minimumSubjectRequirements") or {}), (
                f"{name}: {programme['title']} marked as meeting requirements when it does not"
            )
        else:
            assert r["eligibilityStatus"] == "Does Not Meet Minimum Subject Requirements"
        assert "confidence" not in r["primaryReason"].lower()
