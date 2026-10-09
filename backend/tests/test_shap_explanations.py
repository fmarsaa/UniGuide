"""Regression tests for two real defects found while measuring NFR-03
(recommendation response time) and documenting Chapter 5:

1. describe_feature() mislabelled one-hot-encoded categorical features
   (currently just "aspiration") - every possible value of the category
   was unconditionally described as "Your stated aspiration of X", even
   for values the student never actually selected. A real explanation was
   observed naming "Aspiration: Biochemist" as the top reason behind a
   Computer Science recommendation for a student who stated "Software
   Engineer / AI Architect" and never mentioned Biochemist at all.

2. _explainer.shap_values() without approximate=True took ~37.6 seconds
   for this model (350 trees x 53 classes) - longer than the Flutter
   client's own 15-second request timeout, meaning every real request
   would have failed. approximate=True reduced this to ~19ms (~2000x).
   NOTE: the approximation is not guaranteed to rank features identically
   to exact SHAP; its fidelity was only spot-checked (see Chapter 5.7).
"""

import main


def test_describe_feature_marks_selected_aspiration_as_selected():
    row = {"aspiration": "Software Engineer / AI Architect"}
    category, feature_name, desc = main.describe_feature(
        "cat__aspiration_Software Engineer / AI Architect", row
    )
    assert category == "Aspirations"
    assert feature_name == "Aspiration: Software Engineer / AI Architect"
    assert "Your stated aspiration" in desc
    assert "not" not in desc.lower()


def test_describe_feature_marks_unselected_aspiration_as_not_selected():
    """The exact bug: a one-hot dummy for an aspiration the student did
    NOT state must never be described as something they stated."""
    row = {"aspiration": "Software Engineer / AI Architect"}
    category, feature_name, desc = main.describe_feature(
        "cat__aspiration_Biochemist", row
    )
    assert category == "Aspirations"
    assert feature_name == "Not aspiration: Biochemist"
    assert "not" in desc.lower()
    assert "Biochemist" in desc


def test_shap_values_use_approximate_mode_for_performance():
    """Locks in that /api/recommend calls shap_values with approximate=True
    - without it, response time exceeds the Flutter client's 15-second
    timeout (measured ~37.6s exact vs ~19ms approximate for this model).
    Checks the actual source rather than re-running the slow exact call
    in every test run."""
    import inspect

    source = inspect.getsource(main.get_recommendations)
    assert "approximate=True" in source
