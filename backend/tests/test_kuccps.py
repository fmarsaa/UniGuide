"""Unit tests for backend/kuccps.py's grading and eligibility math - the
rules that decide, for a real student, what they can and can't be admitted
to. These are the functions a wrong formula or a silent regression here
would be hardest to notice by eye, since results still "look plausible"."""

import pytest

from kuccps import (
    aggregate_points,
    cluster_weighted_points,
    cutoff_tier,
    eligibility_status,
    grade_to_points,
    meets_minimum_requirements,
    points_to_grade,
    raw_cluster_points,
    university_cutoff_summary,
)


class TestGradePointsRoundTrip:
    def test_all_grades_round_trip(self):
        for grade in ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "E"]:
            assert points_to_grade(grade_to_points(grade)) == grade

    def test_unknown_grade_falls_back_to_default(self):
        assert grade_to_points("not a real grade") == grade_to_points("C+")

    def test_missing_grade_falls_back_to_given_default(self):
        assert grade_to_points(None, default="B") == grade_to_points("B")

    def test_case_and_whitespace_insensitive(self):
        assert grade_to_points(" b+ ") == grade_to_points("B+")


class TestAggregatePoints:
    def test_seven_or_more_grades_takes_best_seven(self):
        grades = {f"Subject{i}": "A" for i in range(9)}
        grades["Weak1"] = "E"
        grades["Weak2"] = "E"
        # Best 7 of these are all A's (12 pts each) = 84, the two E's are dropped.
        assert aggregate_points(grades) == 84

    def test_fewer_than_seven_grades_scales_up(self):
        # 3 subjects at C+ (7 pts each) = 21 raw; scaled to 7 subjects: 21 * 7/3 = 49.
        grades = {"Mathematics": "C+", "English": "C+", "Kiswahili": "C+"}
        assert aggregate_points(grades) == 49

    def test_empty_grades_uses_mean_grade_times_seven(self):
        assert aggregate_points({}, mean_grade="B") == grade_to_points("B") * 7

    def test_result_always_within_valid_bounds(self):
        assert 14 <= aggregate_points({}, mean_grade="E") <= 84
        assert 14 <= aggregate_points({f"S{i}": "A" for i in range(9)}) <= 84


class TestRawClusterPoints:
    def test_sums_required_subjects(self):
        grades = {"Mathematics": "A", "Physics": "A"}  # 12 + 12 = 24
        assert raw_cluster_points(grades, ["Mathematics", "Physics"]) == 24

    def test_missing_subject_uses_mean_grade_default(self):
        grades = {"Mathematics": "A"}
        result = raw_cluster_points(grades, ["Mathematics", "Physics"], mean_grade="C")
        assert result == grade_to_points("A") + grade_to_points("C")

    def test_clamped_to_valid_range(self):
        grades = {f"S{i}": "A" for i in range(5)}
        assert raw_cluster_points(grades, list(grades.keys())) <= 48


class TestClusterWeightedPoints:
    def test_zero_inputs_return_zero(self):
        assert cluster_weighted_points(0, 50) == 0.0
        assert cluster_weighted_points(30, 0) == 0.0

    def test_perfect_score_gives_perfect_cwp(self):
        # raw=48 (max cluster points), agg=84 (max aggregate) -> CWP should hit 48.
        assert cluster_weighted_points(48, 84) == 48.0

    def test_higher_raw_points_never_decreases_cwp(self):
        low = cluster_weighted_points(20, 60)
        high = cluster_weighted_points(40, 60)
        assert high >= low


class TestMeetsMinimumRequirements:
    def test_passes_when_all_subjects_clear_the_bar(self):
        grades = {"Mathematics": "B", "Physics": "B"}
        reqs = {"Mathematics": "C+", "Physics": "C+"}
        assert meets_minimum_requirements(grades, reqs) is True

    def test_fails_when_one_subject_is_below_the_bar(self):
        grades = {"Mathematics": "B", "Physics": "C-"}
        reqs = {"Mathematics": "C+", "Physics": "C+"}
        assert meets_minimum_requirements(grades, reqs) is False

    def test_missing_subject_fails_the_requirement_whatever_the_mean_grade(self):
        # A subject the student never sat (e.g. Biology, now optional) cannot
        # satisfy a minimum-grade requirement for it, even with a high mean.
        reqs = {"Biology": "C+"}
        assert meets_minimum_requirements({}, reqs, mean_grade="A") is False
        assert meets_minimum_requirements({"Mathematics": "A"}, reqs, mean_grade="A") is False
        assert meets_minimum_requirements({"Biology": "B"}, reqs, mean_grade="D") is True

    def test_student_without_biology_fails_every_real_programme_that_needs_it(self):
        """Biology is optional, so a student may not have sat it. Every real
        catalogue programme that gates on Biology must then be unreachable."""
        from programmes_catalog import PROGRAMMES

        no_biology = {"Mathematics": "A", "English": "A", "Kiswahili": "A", "Chemistry": "A", "Physics": "A"}
        gated = [p for p in PROGRAMMES if "Biology" in (p.get("minimumSubjectRequirements") or {})]
        assert gated, "expected some programmes to require Biology"
        for p in gated:
            assert meets_minimum_requirements(no_biology, p["minimumSubjectRequirements"], mean_grade="A") is False

    def test_no_requirements_always_passes(self):
        assert meets_minimum_requirements({}, {}) is True

    def test_real_world_c_minus_student_fails_every_common_bar(self):
        """The exact scenario that motivated the eligibility-gate fix: a
        straight C- student must not clear any 'C' or higher requirement."""
        grades = {"Mathematics": "C-", "English": "C-", "Biology": "C-", "Chemistry": "C-"}
        assert meets_minimum_requirements(grades, {"Mathematics": "C"}) is False
        assert meets_minimum_requirements(grades, {"English": "C+"}) is False


class TestEligibilityStatus:
    def test_meets_requirements_and_above_cutoff(self):
        status = eligibility_status(45.0, 40.0, meets_requirements=True)
        assert "Likely Admission" in status

    def test_meets_requirements_and_borderline(self):
        status = eligibility_status(39.0, 40.0, meets_requirements=True)
        assert "Competitive" in status or "Borderline" in status

    def test_meets_requirements_and_far_below_cutoff(self):
        status = eligibility_status(20.0, 40.0, meets_requirements=True)
        assert "Reach" in status or "High Risk" in status

    def test_does_not_meet_requirements_overrides_score_based_messaging(self):
        """Even with a CWP comfortably above cutoff, failing the hard
        minimum-subject gate must produce the honest disqualification
        message, never 'Likely Admission'."""
        status = eligibility_status(50.0, 40.0, meets_requirements=False)
        assert status == "Does Not Meet Minimum Subject Requirements"

    def test_default_meets_requirements_is_true_for_backwards_compatibility(self):
        status = eligibility_status(45.0, 40.0)
        assert "Likely Admission" in status


UNIS = [
    {"universityName": "A", "latestCutoff": 45.6},
    {"universityName": "B", "latestCutoff": 45.0},
    {"universityName": "C", "latestCutoff": 45.1},
]


class TestUniversityCutoffs:
    """The same programme has a different cutoff at each university, so a
    student is compared with each one rather than a single average."""

    def test_counts_how_many_universities_are_met(self):
        summary = university_cutoff_summary(45.3, UNIS)
        assert (summary["total"], summary["meets"], summary["lowest"]) == (3, 2, 45.0)

    def test_status_names_how_many_universities_are_met(self):
        summary = university_cutoff_summary(45.3, UNIS)
        assert eligibility_status(45.3, 40.0, True, summary) == "Meets the latest cutoff at 2 of 3 universities"
        assert eligibility_status(46.0, 40.0, True, university_cutoff_summary(46.0, UNIS)) == "Meets the latest cutoff at all 3 universities"

    def test_just_below_the_lowest_cutoff_is_a_close_call_not_a_match(self):
        status = eligibility_status(44.4, 40.0, True, university_cutoff_summary(44.4, UNIS))
        assert status.startswith("Close call: 0.6 pts below the lowest cutoff")

    def test_far_below_is_a_reach(self):
        status = eligibility_status(30.0, 40.0, True, university_cutoff_summary(30.0, UNIS))
        assert status.startswith("Reach:")

    def test_failing_minimum_subjects_still_overrides_everything(self):
        summary = university_cutoff_summary(60.0, UNIS)
        assert eligibility_status(60.0, 40.0, False, summary) == "Does Not Meet Minimum Subject Requirements"

    def test_tiers_order_meets_then_close_then_reach(self):
        assert cutoff_tier(university_cutoff_summary(45.3, UNIS)) == 0
        assert cutoff_tier(university_cutoff_summary(44.4, UNIS)) == 1
        assert cutoff_tier(university_cutoff_summary(30.0, UNIS)) == 2

    def test_falls_back_to_the_programme_average_when_no_university_data(self):
        summary = university_cutoff_summary(41.0, [], fallback_cutoff=40.0)
        assert (summary["total"], summary["meets"]) == (1, 1)
        assert university_cutoff_summary(41.0, [], None) is None
