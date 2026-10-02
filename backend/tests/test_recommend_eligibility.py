"""Regression test for the real bug found during manual testing: a student
whose grades don't clear a programme's real KUCCPS minimum subject
requirements must never be ranked into that programme's recommendation
slot on raw model confidence alone - eligibility_status has to say so
honestly rather than a misleading 'high risk'. Exercises
main.select_recommended_indices directly (no HTTP layer, no Firebase Auth,
no Firestore writes) - needs backend/rf_model_pipeline.pkl to already
exist (run train_random_forest.py first if this errors on import).
"""

import numpy as np
import pytest

import main
from kuccps import eligibility_status, meets_minimum_requirements

pytestmark = pytest.mark.skipif(main._pipeline is None, reason="rf_model_pipeline.pkl not trained yet")


def _feature_row(grades, mean_grade):
    payload = main.StudentProfilePayload(kcseMeanGrade=mean_grade, grades=grades)
    return main.profile_to_feature_row(payload)


def test_straight_c_minus_student_gets_zero_eligible_programmes():
    """No programme in the whole 53-programme catalogue requires below a
    plain 'C' - a straight C- student must correctly get zero eligible
    matches, not a lucky high-confidence hit on a high-barrier programme."""
    grades = {
        "Mathematics": "C-", "English": "C-", "Kiswahili": "C-", "Biology": "C-",
        "Chemistry": "C-", "Physics": "C-", "History": "C-", "Business Studies": "C-",
        "Geography": "C-",
    }
    row_df, g, mean_grade = _feature_row(grades, "C-")
    proba = main._pipeline.predict_proba(row_df)[0]
    classes = main._pipeline.classes_

    top_idx, eligible_mask = main.select_recommended_indices(proba, classes, g, mean_grade)

    assert sum(eligible_mask) == 0
    assert len(top_idx) == 3  # fallback still fills all 3 slots

    for idx in top_idx:
        title = classes[idx]
        programme = main.CATALOG_BY_TITLE[title]
        status = eligibility_status(0, programme["averageCutoff"], meets_requirements=eligible_mask[idx])
        assert status == "Does Not Meet Minimum Subject Requirements"


def test_high_barrier_programme_never_appears_for_low_grade_student():
    """The exact scenario this fix targets: MBChB (real floor: B in
    Biology/Chemistry/English) must never be recommended to a C- student,
    regardless of how the model scores it on the other signals."""
    grades = {
        "Mathematics": "C-", "English": "C-", "Kiswahili": "C-", "Biology": "C-",
        "Chemistry": "C-", "Physics": "C-",
    }
    row_df, g, mean_grade = _feature_row(grades, "C-")
    proba = main._pipeline.predict_proba(row_df)[0]
    classes = main._pipeline.classes_

    top_idx, eligible_mask = main.select_recommended_indices(proba, classes, g, mean_grade)
    recommended_titles = {classes[i] for i in top_idx}

    assert "Bachelor of Medicine and Bachelor of Surgery (MBChB)" not in recommended_titles
    assert "Bachelor of Veterinary Medicine (BVM)" not in recommended_titles


def test_eligible_student_gets_only_eligible_top_picks():
    """A strong, well-rounded profile should have plenty of genuinely
    eligible programmes, and every top pick returned should be one of
    them (not a fallback) - eligible_mask should be True for all 3."""
    grades = {
        "Mathematics": "A", "English": "A", "Kiswahili": "A-", "Biology": "A",
        "Chemistry": "A", "Physics": "A", "Business Studies": "A-", "Geography": "B+",
    }
    row_df, g, mean_grade = _feature_row(grades, "A-")
    proba = main._pipeline.predict_proba(row_df)[0]
    classes = main._pipeline.classes_

    top_idx, eligible_mask = main.select_recommended_indices(proba, classes, g, mean_grade)

    assert sum(eligible_mask) > 0
    assert all(eligible_mask[i] for i in top_idx)


def test_newly_trained_programme_is_reachable():
    """Business Management (added in the 53-class expansion) was
    structurally impossible to recommend before that change - a profile
    strongly biased toward it should now actually get it as the top pick."""
    grades = {
        "Mathematics": "C", "English": "C+", "Kiswahili": "C+", "Biology": "C+",
        "Chemistry": "C", "Physics": "C", "Business Studies": "B-", "Geography": "B-",
    }
    payload = main.StudentProfilePayload(
        kcseMeanGrade="C+", grades=grades,
        interests=["General Business Administration & Strategy"],
        skills=["Financial Modeling & Accounting", "Team Collaboration & Leadership"],
        strengths=["Leadership & Strategic Direction"],
        aspirations=["Business Manager / Administrator"],
    )
    row_df, g, mean_grade = main.profile_to_feature_row(payload)
    proba = main._pipeline.predict_proba(row_df)[0]
    classes = main._pipeline.classes_

    top_idx, eligible_mask = main.select_recommended_indices(proba, classes, g, mean_grade)
    top_title = classes[top_idx[0]]

    assert top_title == "Bachelor of Business Management"
    assert eligible_mask[top_idx[0]] is True


def test_live_catalogue_edit_is_reflected_in_eligibility():
    """Regression test for the live-catalogue bug: CATALOG_BY_TITLE used to
    be a static, process-startup-time copy, so an admin's PUT
    /api/admin/programmes/{id} edit updated Firestore (and the student
    browse catalogue) but never reached get_recommendations()'s eligibility
    gate. CATALOG_BY_ID/CATALOG_BY_TITLE are now live, mutable dicts kept in
    sync by _load_live_catalog() - this directly exercises that an edit to
    the in-memory dict (exactly what update_programme does after its
    Firestore write) changes what meets_minimum_requirements() sees,
    without needing a real Firestore round-trip or a server restart."""
    title = "Bachelor of Science in Agriculture"
    original_reqs = dict(main.CATALOG_BY_TITLE[title]["minimumSubjectRequirements"])
    assert original_reqs == {"Biology": "C+", "Chemistry": "C", "Mathematics": "C"}
    grades = {
        "Mathematics": "C", "English": "C", "Kiswahili": "C", "Biology": "C+",
        "Chemistry": "C",
    }
    try:
        # Clears the real floor (Biology C+, Chemistry C, Mathematics C).
        assert meets_minimum_requirements(grades, main.CATALOG_BY_TITLE[title]["minimumSubjectRequirements"]) is True

        # Simulate an admin tightening the requirement (exactly what
        # update_programme does to this same dict object after its
        # Firestore write) - the SAME grades must now fail.
        main.CATALOG_BY_TITLE[title]["minimumSubjectRequirements"] = {"Mathematics": "B", "Biology": "B"}
        assert meets_minimum_requirements(grades, main.CATALOG_BY_TITLE[title]["minimumSubjectRequirements"]) is False

        # And CATALOG_BY_ID must see the identical change - same object,
        # not a stale separate copy.
        programme_id = next(pid for pid, p in main.CATALOG_BY_ID.items() if p["title"] == title)
        assert main.CATALOG_BY_ID[programme_id]["minimumSubjectRequirements"] == {"Mathematics": "B", "Biology": "B"}
    finally:
        main.CATALOG_BY_TITLE[title]["minimumSubjectRequirements"] = original_reqs


def test_deactivated_programme_is_never_recommended():
    """A deactivated programme must be excluded from both the eligible
    ranking and the fallback list, even for a profile that would otherwise
    strongly match it - exercises the exact filtering
    select_recommended_indices applies for a programme an admin deactivated."""
    title = "Bachelor of Business Management"
    assert main.CATALOG_BY_TITLE[title].get("status") != "inactive"
    try:
        main.CATALOG_BY_TITLE[title]["status"] = "inactive"
        grades = {
            "Mathematics": "C", "English": "C+", "Kiswahili": "C+", "Biology": "C+",
            "Chemistry": "C", "Physics": "C", "Business Studies": "B-", "Geography": "B-",
        }
        payload = main.StudentProfilePayload(
            kcseMeanGrade="C+", grades=grades,
            interests=["General Business Administration & Strategy"],
            skills=["Financial Modeling & Accounting", "Team Collaboration & Leadership"],
            strengths=["Leadership & Strategic Direction"],
            aspirations=["Business Manager / Administrator"],
        )
        row_df, g, mean_grade = main.profile_to_feature_row(payload)
        proba = main._pipeline.predict_proba(row_df)[0]
        classes = main._pipeline.classes_

        top_idx, eligible_mask = main.select_recommended_indices(proba, classes, g, mean_grade)
        recommended_titles = {classes[i] for i in top_idx}

        assert title not in recommended_titles
    finally:
        del main.CATALOG_BY_TITLE[title]["status"]
