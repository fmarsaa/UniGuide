"""DR-05 (Data Validation & Preprocessing) regression tests: the proposal
requires that invalid or incomplete academic records are never processed
for a recommendation. Before this validation existed, grade_to_points()
silently defaulted any unrecognized grade string to "C+" rather than
rejecting it - a malformed or tampered grade would quietly generate a real
recommendation off a value the student never actually entered. These tests
lock in that StudentProfilePayload now refuses such input outright."""

import pydantic
import pytest

import main


def _valid_grades():
    return {"Mathematics": "A", "English": "B+", "Kiswahili": "B", "Biology": "A-", "Chemistry": "A"}


def test_valid_payload_constructs_without_error():
    payload = main.StudentProfilePayload(kcseMeanGrade="B+", grades=_valid_grades())
    assert payload.kcseMeanGrade == "B+"


def test_rejects_invalid_mean_grade():
    with pytest.raises(pydantic.ValidationError):
        main.StudentProfilePayload(kcseMeanGrade="Z9", grades=_valid_grades())


def test_rejects_invalid_subject_grade():
    grades = _valid_grades()
    grades["Mathematics"] = "Z9"
    with pytest.raises(pydantic.ValidationError):
        main.StudentProfilePayload(kcseMeanGrade="B+", grades=grades)


def test_rejects_missing_compulsory_subject():
    """Covers the 'incomplete' half of DR-05, not just malformed values -
    a profile missing one of the 5 compulsory KCSE subjects must be
    refused too, not silently processed with a guessed default."""
    incomplete = {"Mathematics": "A", "English": "B+"}  # missing Kiswahili/Biology/Chemistry
    with pytest.raises(pydantic.ValidationError):
        main.StudentProfilePayload(kcseMeanGrade="B+", grades=incomplete)


def test_accepts_extra_non_compulsory_subjects():
    """Validation should only enforce the 5 compulsory subjects are present
    and every stated grade is real - it must not reject a profile just for
    including optional subjects beyond those."""
    grades = _valid_grades()
    grades["Physics"] = "B"
    grades["Geography"] = "B-"
    payload = main.StudentProfilePayload(kcseMeanGrade="B+", grades=grades)
    assert payload.grades["Physics"] == "B"


def test_error_message_is_a_clean_string_not_a_structured_list():
    """IR-06 requires standardized, user-friendly error responses - the
    custom RequestValidationError handler in main.py reformats Pydantic's
    normally verbose, structured error list into a single clean string
    so the Flutter side's existing error-display code needs no special
    case for this endpoint family. This test exercises that handler
    function directly (it's a plain function, not a live HTTP call)."""
    from fastapi.exceptions import RequestValidationError

    try:
        main.StudentProfilePayload(kcseMeanGrade="Z9", grades=_valid_grades())
        assert False, "expected a ValidationError"
    except pydantic.ValidationError as e:
        fake_exc = RequestValidationError(e.errors())
        import asyncio
        response = asyncio.run(main._validation_exception_handler(None, fake_exc))
        import json
        body = json.loads(response.body)
        assert isinstance(body["detail"], str)
        assert "Z9" in body["detail"]
        assert "Value error" not in body["detail"]
