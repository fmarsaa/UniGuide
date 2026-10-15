"""Tests for the plain-language reasons shown to students, the optional career
("Not sure yet") handling, and the saved-programmes shortlist endpoints. The
shortlist tests use an in-memory stand-in for Firestore, so nothing is written
to the real database."""

import pytest
from fastapi import HTTPException

import main
from kuccps import UNDECIDED_ASPIRATION
from synthetic_data_generator import TRAIT_COLUMN_INFO, UNDECIDED_RATE, _build_profile_for_target

pytestmark = pytest.mark.skipif(main._pipeline is None, reason="rf_model_pipeline.pkl not trained yet")


# ---------------------------------------------------------------- plain reasons
def _programme(requirements=None):
    return {"minimumSubjectRequirements": requirements or {}}


def _interest_column():
    return next(col for col, (cat, word, label) in TRAIT_COLUMN_INFO.items() if word == "Interest")


def test_a_selected_interest_becomes_a_plain_sentence():
    col = _interest_column()
    label = TRAIT_COLUMN_INFO[col][2]
    shap = [{"rawName": f"num__{col}", "shapValue": 0.2}]
    reasons = main.build_plain_reasons(shap, {col: 1}, _programme(), {}, "B")
    assert reasons == [f"You said you are interested in {label}."]


def test_factors_that_pushed_the_result_down_are_never_listed():
    col = _interest_column()
    shap = [{"rawName": f"num__{col}", "shapValue": -0.2}]
    reasons = main.build_plain_reasons(shap, {col: 1}, _programme(), {}, "B")
    assert reasons == ["This programme fits the overall pattern of your grades and answers."]


def test_a_subject_the_student_did_not_sit_is_never_described_as_having_a_grade():
    shap = [{"rawName": "num__bio_score", "shapValue": 0.5}]
    grades = {"Mathematics": "A", "English": "A", "Kiswahili": "A", "Chemistry": "A"}  # no Biology
    reasons = main.build_plain_reasons(shap, {"bio_score": 8}, _programme({"Biology": "C+"}), grades, "A")
    assert not any("Biology" in r for r in reasons)


def test_a_subject_grade_that_meets_the_requirement_says_so():
    shap = [{"rawName": "num__chem_score", "shapValue": 0.5}]
    grades = {"Chemistry": "B+"}
    reasons = main.build_plain_reasons(shap, {"chem_score": 10}, _programme({"Chemistry": "C+"}), grades, "B")
    assert reasons == ["Your Chemistry grade (B+) meets the C+ this programme asks for."]


def test_a_career_the_student_did_not_pick_is_never_mentioned():
    shap = [{"rawName": "cat__aspiration_Pharmacist", "shapValue": 0.4}]
    reasons = main.build_plain_reasons(shap, {"aspiration": "Dentist"}, _programme(), {}, "B")
    assert not any("Pharmacist" in r for r in reasons)


def test_the_career_the_student_picked_is_mentioned():
    shap = [{"rawName": "cat__aspiration_Dentist", "shapValue": 0.4}]
    reasons = main.build_plain_reasons(shap, {"aspiration": "Dentist"}, _programme(), {}, "B")
    assert reasons == ["You picked Dentist as a career you have in mind."]


def test_an_undecided_student_is_told_the_match_comes_from_their_grades_and_answers():
    shap = [{"rawName": f"cat__aspiration_{UNDECIDED_ASPIRATION}", "shapValue": 0.4}]
    reasons = main.build_plain_reasons(shap, {"aspiration": UNDECIDED_ASPIRATION}, _programme(), {}, "B")
    assert "not picked a career" in reasons[0]


def test_at_most_three_reasons_are_given():
    cols = [c for c, (cat, word, label) in TRAIT_COLUMN_INFO.items() if word == "Interest"][:5]
    shap = [{"rawName": f"num__{c}", "shapValue": 0.5 - i * 0.01} for i, c in enumerate(cols)]
    reasons = main.build_plain_reasons(shap, {c: 1 for c in cols}, _programme(), {}, "B")
    assert len(reasons) == 3


# ----------------------------------------------------- optional career handling
def test_no_career_picked_is_sent_to_the_model_as_not_sure_yet():
    payload = main.StudentProfilePayload(
        kcseMeanGrade="B", grades={"Mathematics": "B", "English": "B", "Kiswahili": "B", "Chemistry": "B"}, aspirations=[]
    )
    row_df, _grades, _mean = main.profile_to_feature_row(payload)
    assert row_df.iloc[0]["aspiration"] == UNDECIDED_ASPIRATION


def test_a_student_with_no_career_still_gets_three_recommendations():
    payload = main.StudentProfilePayload(
        kcseMeanGrade="B",
        grades={"Mathematics": "B", "English": "B", "Kiswahili": "B", "Chemistry": "B", "Physics": "B"},
        interests=["Software Development & Coding"],
        skills=["Python & Software Programming"],
        strengths=["Logical & Analytical Reasoning"],
        aspirations=[],
    )
    row_df, grades, mean_grade = main.profile_to_feature_row(payload)
    proba = main._pipeline.predict_proba(row_df)[0]
    top_idx, _ = main.select_recommended_indices(proba, main._pipeline.classes_, grades, mean_grade)
    assert len(top_idx) == 3


def test_training_data_includes_a_realistic_share_of_undecided_students():
    import random

    import numpy as np

    random.seed(7)
    np.random.seed(7)
    title = main._pipeline.classes_[0]
    undecided = sum(_build_profile_for_target(i, title)["aspiration"] == UNDECIDED_ASPIRATION for i in range(400))
    assert abs(undecided / 400 - UNDECIDED_RATE) < 0.08


# ------------------------------------------------------------------ shortlist
class _Snap:
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return self._data


class _Ref:
    def __init__(self, store, doc_id):
        self.store, self.id = store, doc_id

    def get(self):
        return _Snap(self.id, self.store.get(self.id))

    def set(self, data):
        self.store[self.id] = {"savedAt": f"2026-01-01T00:00:{len(self.store):02d}"}

    def delete(self):
        self.store.pop(self.id, None)


class _Collection:
    def __init__(self, store):
        self.store = store

    def document(self, doc_id):
        return _Ref(self.store, doc_id)

    def stream(self):
        return [_Snap(k, v) for k, v in self.store.items()]


class _Student:
    def __init__(self, db, uid):
        self.db, self.uid = db, uid

    def collection(self, name):
        return _Collection(self.db.stores.setdefault((self.uid, name), {}))


class _Students:
    def __init__(self, db):
        self.db = db

    def document(self, uid):
        return _Student(self.db, uid)


class _FakeDb:
    def __init__(self):
        self.stores = {}

    def collection(self, name):
        return _Students(self)


@pytest.fixture
def fake_db(monkeypatch):
    db = _FakeDb()
    monkeypatch.setattr(main, "get_db", lambda: db)
    return db


USER = {"uid": "student-1"}


def _two_ids():
    ids = [p["id"] for p in main.PROGRAMMES if main.CATALOG_BY_ID[p["id"]].get("status") != "inactive"]
    return ids[0], ids[1]


def test_saved_programmes_come_back_in_the_order_they_were_saved(fake_db):
    first, second = _two_ids()
    main.add_to_shortlist(first, USER)
    main.add_to_shortlist(second, USER)
    assert [p["id"] for p in main.get_shortlist(USER)] == [first, second]


def test_saving_the_same_programme_twice_keeps_one_copy(fake_db):
    first, _ = _two_ids()
    main.add_to_shortlist(first, USER)
    main.add_to_shortlist(first, USER)
    assert len(main.get_shortlist(USER)) == 1


def test_removing_a_programme_takes_it_off_the_shortlist(fake_db):
    first, second = _two_ids()
    main.add_to_shortlist(first, USER)
    main.add_to_shortlist(second, USER)
    main.remove_from_shortlist(first, USER)
    assert [p["id"] for p in main.get_shortlist(USER)] == [second]


def test_one_student_never_sees_anothers_shortlist(fake_db):
    first, _ = _two_ids()
    main.add_to_shortlist(first, USER)
    assert main.get_shortlist({"uid": "someone-else"}) == []


def test_saving_an_unknown_programme_is_refused(fake_db):
    with pytest.raises(HTTPException) as err:
        main.add_to_shortlist("prog_does_not_exist", USER)
    assert err.value.status_code == 404


def test_a_deactivated_programme_cannot_be_saved_and_disappears_from_the_list(fake_db):
    first, second = _two_ids()
    main.add_to_shortlist(first, USER)
    try:
        main.CATALOG_BY_ID[first]["status"] = "inactive"
        assert main.get_shortlist(USER) == []
        with pytest.raises(HTTPException):
            main.add_to_shortlist(first, USER)
    finally:
        del main.CATALOG_BY_ID[first]["status"]


def test_the_shortlist_has_a_size_limit(fake_db, monkeypatch):
    first, second = _two_ids()
    third = next(p["id"] for p in main.PROGRAMMES if p["id"] not in (first, second))
    monkeypatch.setattr(main, "SHORTLIST_LIMIT", 2)
    main.add_to_shortlist(first, USER)
    main.add_to_shortlist(second, USER)
    with pytest.raises(HTTPException) as err:
        main.add_to_shortlist(third, USER)
    assert err.value.status_code == 409
