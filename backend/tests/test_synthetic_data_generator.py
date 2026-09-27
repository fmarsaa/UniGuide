"""Regression tests for the training-data vocabulary in
synthetic_data_generator.py. Module-level asserts already enforce most of
this at import time, but a silent future edit could still narrow one of
these lists back down without anyone noticing until accuracy quietly drops
- these tests make the invariants explicit and give a readable failure
message instead of a bare AssertionError deep in module import."""

from programmes_catalog import PROGRAMME_TITLES
from synthetic_data_generator import (
    FALLBACK_ORDER,
    PROGRAMME_ASPIRATIONS,
    TRAINED_PROGRAMME_TITLES,
    assign_programme_label,
)


def test_all_53_catalogue_programmes_are_trained():
    """The whole point of the 53-class expansion: every real, catalogued
    programme must be reachable by the recommender, not just a subset."""
    assert len(TRAINED_PROGRAMME_TITLES) == 53
    assert set(TRAINED_PROGRAMME_TITLES) == set(PROGRAMME_TITLES)


def test_every_trained_programme_has_at_least_two_aspiration_options():
    """The exact bug this project fixed once already: a programme with
    only one aspiration option that maps to it exclusively lets the model
    "cheat" off that single field. Guard against it recurring for any of
    the 53 trained programmes."""
    for title in TRAINED_PROGRAMME_TITLES:
        options = PROGRAMME_ASPIRATIONS[title]
        assert len(options) >= 2, f"{title} only has {len(options)} aspiration option(s): {options}"


def test_fallback_order_only_contains_trained_programmes():
    assert all(title in TRAINED_PROGRAMME_TITLES for title in FALLBACK_ORDER)


def test_fallback_order_is_nonempty():
    """If this is ever emptied by accident, a student who fails every
    eligibility check gets an empty recommendation list instead of an
    honest fallback."""
    assert len(FALLBACK_ORDER) > 0


def test_assign_programme_label_returns_a_trained_programme():
    grades = {
        "Mathematics": "A", "English": "B+", "Kiswahili": "B", "Biology": "A-",
        "Chemistry": "A", "Physics": "A",
    }
    label = assign_programme_label(
        grades, mean_grade="A-",
        interests=["Healthcare & Clinical Medicine"],
        skills=["Clinical Diagnostics & Health Care"],
        strengths=["Empathy & Human Care"],
        aspiration="Medical Doctor (Physician/Surgeon)",
    )
    assert label in TRAINED_PROGRAMME_TITLES


def test_assign_programme_label_never_picks_an_ineligible_programme():
    """A profile that clears only low-bar requirements (plain C's) must
    never be labelled with a high-barrier programme like MBChB (real
    floor: B) - this is the exact invariant the /api/recommend eligibility
    gate in main.py also depends on holding true for the training data."""
    grades = {
        "Mathematics": "C", "English": "C", "Kiswahili": "C", "Biology": "C",
        "Chemistry": "C", "Physics": "C", "History": "C", "Business Studies": "C",
        "Geography": "C",
    }
    label = assign_programme_label(
        grades, mean_grade="C",
        interests=["Healthcare & Clinical Medicine"],
        skills=["Clinical Diagnostics & Health Care"],
        strengths=["Empathy & Human Care"],
        aspiration="Medical Doctor (Physician/Surgeon)",
    )
    assert label != "Bachelor of Medicine and Bachelor of Surgery (MBChB)"
