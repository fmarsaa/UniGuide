"""The numbers behind the admin Insights page, checked on small hand-made data
where the right answer can be counted by eye."""

from datetime import datetime, timedelta, timezone

from analytics import build_overview, eligibility_bucket

NOW = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)


def _ago(days):
    return NOW - timedelta(days=days)


STUDENTS = [
    {"uid": "a", "createdAt": _ago(2), "kcseMeanGrade": "B+", "aspirations": ["Doctor"]},
    {"uid": "b", "createdAt": _ago(10), "kcseMeanGrade": "B+", "aspirations": []},
    {"uid": "c", "createdAt": _ago(45), "kcseMeanGrade": "C", "aspirations": []},
    {"uid": "d", "createdAt": _ago(1), "kcseMeanGrade": None, "aspirations": []},
]
RECS = [
    {"uid": "a", "createdAt": _ago(1), "items": [
        {"meetsMinimumRequirements": True, "universityCutoffs": {"meets": 1, "total": 2}},
        {"meetsMinimumRequirements": False},
    ]},
    {"uid": "b", "createdAt": _ago(12), "items": [{"meetsMinimumRequirements": True, "universityCutoffs": {"meets": 0, "total": 1}}]},
    {"uid": "c", "createdAt": _ago(60), "items": []},
]
FEEDBACK = [{"uid": "a", "rating": 5}, {"uid": "b", "rating": 3}, {"uid": "x", "rating": 0}]
SAVED = [{"uid": "a", "programmeId": "p1"}, {"uid": "b", "programmeId": "p1"}, {"uid": "b", "programmeId": "p2"}]
TITLES = {"p1": "Medicine", "p2": "Law"}


def overview():
    return build_overview(STUDENTS, RECS, FEEDBACK, SAVED, TITLES, now=NOW)


def test_the_headline_counts():
    totals = overview()["totals"]
    assert totals["students"] == 4
    assert totals["newLast7Days"] == 2  # a and d
    assert totals["recommendations"] == 3
    assert totals["savedProgrammes"] == 3
    assert totals["feedback"] == 3


def test_active_students_are_those_with_a_recommendation_in_the_window():
    totals = overview()["totals"]
    assert totals["active7Days"] == 1   # only a
    assert totals["active30Days"] == 2  # a and b


def test_the_average_rating_ignores_a_rating_outside_one_to_five():
    assert overview()["totals"]["averageRating"] == 4.0
    assert [r["count"] for r in overview()["ratingDistribution"]] == [0, 0, 1, 0, 1]


def test_no_feedback_gives_no_average_rather_than_zero():
    result = build_overview(STUDENTS, RECS, [], SAVED, TITLES, now=NOW)
    assert result["totals"]["averageRating"] is None


def test_growth_counts_earlier_students_in_the_running_total():
    growth = overview()["growth"]
    assert len(growth) == 30
    assert growth[0]["totalStudents"] == 1      # c registered before the 30 days
    assert growth[-1]["totalStudents"] == 4
    assert sum(day["newStudents"] for day in growth) == 3


def test_the_journey_narrows_step_by_step():
    stages = {s["stage"]: s["count"] for s in overview()["funnel"]}
    assert stages == {
        "Registered": 4,
        "Entered grades": 3,
        "Received recommendations": 3,
        "Saved a programme": 2,
        "Gave feedback": 3,
    }


def test_grades_are_counted_only_for_students_who_entered_them():
    counts = {g["grade"]: g["count"] for g in overview()["gradeDistribution"]}
    assert counts["B+"] == 2 and counts["C"] == 1 and sum(counts.values()) == 3


def test_undecided_students_are_counted_among_those_with_a_profile():
    assert overview()["careerChoice"] == {"decided": 1, "undecided": 2}


def test_recommended_programmes_are_grouped_by_whether_they_were_within_reach():
    assert overview()["eligibility"] == {"meetsCutoff": 1, "belowCutoff": 1, "missingSubject": 1}


def test_the_most_saved_programmes_come_first_with_their_names():
    assert overview()["topSaved"][0] == {"title": "Medicine", "count": 2}


def test_an_empty_system_gives_zeros_not_errors():
    result = build_overview([], [], [], [], {}, now=NOW)
    assert result["totals"]["students"] == 0
    assert result["funnel"][0]["count"] == 0
    assert result["eligibility"] == {"meetsCutoff": 0, "belowCutoff": 0, "missingSubject": 0}


def test_a_programme_without_university_figures_falls_back_to_the_cutoff_gap():
    assert eligibility_bucket({"meetsMinimumRequirements": True, "cutoffDiff": 1.5}) == "meetsCutoff"
    assert eligibility_bucket({"meetsMinimumRequirements": True, "cutoffDiff": -0.6}) == "belowCutoff"
