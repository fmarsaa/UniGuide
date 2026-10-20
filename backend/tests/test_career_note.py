"""The note that explains why a programme for the student's chosen career is not in their results."""

import main
from kuccps import unmet_requirements

MBCHB = "Bachelor of Medicine and Bachelor of Surgery (MBChB)"
STRONG = {"Mathematics": "A", "English": "A", "Kiswahili": "A", "Chemistry": "A", "Biology": "A"}


def test_a_grade_below_the_requirement_is_named_with_both_grades():
    notes = unmet_requirements({"English": "D+"}, {"English": "B"})
    assert notes == ["English: asks for at least B, and your grade is D+"]


def test_a_subject_that_was_not_sat_is_said_plainly():
    notes = unmet_requirements({"English": "A"}, {"Biology": "B+"})
    assert notes == ["Biology: asks for at least B+, and you did not sit this subject"]


def test_nothing_is_reported_when_every_requirement_is_met():
    assert unmet_requirements({"English": "B", "Biology": "A"}, {"English": "B", "Biology": "B+"}) == []


def test_a_student_short_of_medicine_is_told_which_grade_is_short():
    grades = {**STRONG, "English": "D+"}
    notes = main.programmes_missed_for_career(grades, ["Medical Doctor (Physician/Surgeon)"])
    assert [n["programme"] for n in notes] == [MBCHB]
    assert any(r.startswith("English:") and "D+" in r for r in notes[0]["reasons"])


def test_a_student_who_qualifies_gets_no_note():
    assert main.programmes_missed_for_career(STRONG, ["Medical Doctor (Physician/Surgeon)"]) == []


def test_no_career_means_no_note():
    assert main.programmes_missed_for_career({"English": "D"}, []) == []


def test_a_career_the_system_does_not_know_is_ignored():
    assert main.programmes_missed_for_career({"English": "D"}, ["Not a listed career"]) == []


def test_a_deactivated_programme_is_not_mentioned():
    main.CATALOG_BY_TITLE[MBCHB]["status"] = "inactive"
    try:
        assert main.programmes_missed_for_career({**STRONG, "English": "D"}, ["Medical Doctor (Physician/Surgeon)"]) == []
    finally:
        del main.CATALOG_BY_TITLE[MBCHB]["status"]
