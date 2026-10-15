"""
UniGuide - KUCCPS Grading and Cluster Weighted Points (CWP) Utilities
Shared by the synthetic dataset generator, the training pipeline, and the
FastAPI inference service so that grade handling stays consistent everywhere.
"""

import math
from typing import Dict, Iterable, Optional

GRADE_POINTS: Dict[str, int] = {
    "A": 12, "A-": 11, "B+": 10, "B": 9, "B-": 8,
    "C+": 7, "C": 6, "C-": 5, "D+": 4, "D": 3, "D-": 2, "E": 1,
}
POINTS_TO_GRADE: Dict[int, str] = {v: k for k, v in GRADE_POINTS.items()}

# What the model sees as the "aspiration" when a student has not picked a career
# yet. UniGuide is for students who may not have decided, so the career step is
# optional; the training data includes profiles with this value so the model
# learns to decide from grades, interests, skills and strengths alone.
UNDECIDED_ASPIRATION = "Not sure yet"

# The 4 subjects every candidate must provide a grade for. Biology is
# deliberately NOT here: it is an optional subject a student may not have
# sat, so it lives in CLUSTER_OPTIONAL_SUBJECTS / FULL_OPTIONAL_SUBJECTS below.
COMPULSORY_SUBJECTS = ["Mathematics", "English", "Kiswahili", "Chemistry"]

# Every subject referenced by at least one programme's clusterSubjects/
# minimumSubjectRequirements in programmes_catalog.py, beyond the compulsory
# 4. A student picks these as part of their optional subjects; when they do,
# the grade is used both for real KUCCPS cluster scoring AND as a genuine
# Random Forest feature (see train_random_forest.py). Keep in sync with
# programmes_catalog.py - a `python -c "from programmes_catalog import
# PROGRAMMES; ..."` scan is how this list was derived.
CLUSTER_OPTIONAL_SUBJECTS = ["Biology", "Physics", "History", "Business Studies", "Geography"]

# All subjects the Random Forest model takes as numeric input features.
ML_FEATURE_SUBJECTS = COMPULSORY_SUBJECTS + CLUSTER_OPTIONAL_SUBJECTS

# Stable short column names for each ML feature subject - used by both the
# training pipeline and main.py's inference feature extraction so they can
# never disagree on a column name.
FEATURE_COLUMN: Dict[str, str] = {
    "Mathematics": "math_score",
    "English": "eng_score",
    "Kiswahili": "kis_score",
    "Biology": "bio_score",
    "Chemistry": "chem_score",
    "Physics": "phys_score",
    "History": "history_score",
    "Business Studies": "business_score",
    "Geography": "geography_score",
}
assert set(FEATURE_COLUMN) == set(ML_FEATURE_SUBJECTS)

# The full KNEC optional subject list offered in the app's subject picker,
# beyond the 4 compulsory ones. Only the CLUSTER_OPTIONAL_SUBJECTS above feed
# the ML model directly; the rest still count fully toward the real KCSE
# aggregate/mean grade (see aggregate_points) and toward matching a student's
# actual subject combination, they're just not individual model features
# since no programme in the catalog currently keys eligibility off them.
FULL_OPTIONAL_SUBJECTS = [
    "Biology", "Physics", "History & Government", "Geography",
    "Christian Religious Education (CRE)", "Islamic Religious Education (IRE)",
    "Business Studies", "Agriculture", "Computer Studies",
    "French", "German", "Home Science", "Art & Design", "Music",
    "Building Construction", "Woodwork", "Metalwork", "Electricity",
    "Power Mechanics", "Aviation Technology",
]


def grade_to_points(grade: Optional[str], default: str = "C+") -> int:
    if not grade:
        grade = default
    return GRADE_POINTS.get(grade.strip().upper() if isinstance(grade, str) else grade, GRADE_POINTS[default])


def points_to_grade(points: int) -> str:
    points = max(1, min(12, round(points)))
    return POINTS_TO_GRADE.get(points, "C+")


def find_grade_for_subject(grades: Dict[str, str], subject: str) -> Optional[str]:
    """Case/substring-tolerant lookup, e.g. 'Chemistry/Computer' cluster labels."""
    subject_l = subject.lower()
    for name, grade in grades.items():
        name_l = name.lower()
        if name_l == subject_l or name_l in subject_l or subject_l in name_l:
            return grade
    return None


def raw_cluster_points(grades: Dict[str, str], cluster_subjects: Iterable[str], mean_grade: str = "C+") -> int:
    """Sum of grade points across a programme's required cluster subjects (max 48)."""
    total = 0
    for subject in cluster_subjects:
        grade = find_grade_for_subject(grades, subject)
        total += grade_to_points(grade, default=mean_grade)
    return max(4, min(48, total))


def aggregate_points(grades: Dict[str, str], mean_grade: str = "C+") -> int:
    """Approximates the KCSE aggregate (best-7 subjects, max 84) from what was captured.

    Real KUCCPS aggregate is the sum of a candidate's best 7 subjects, not
    every subject sat (some candidates sit 8-9). If more than 7 grades are
    given, take the top 7 by points rather than diluting the aggregate with
    weaker optional subjects. If fewer than 7 are given, scale up so a
    partially-filled profile still produces a reasonable estimate.
    """
    if grades:
        points = sorted((grade_to_points(g, default=mean_grade) for g in grades.values()), reverse=True)
        n = len(points)
        if n >= 7:
            return max(14, min(84, sum(points[:7])))
        scaled = round(sum(points) * (7 / n))
        return max(14, min(84, scaled))
    return max(14, min(84, grade_to_points(mean_grade) * 7))


def cluster_weighted_points(raw_points: int, agg_points: int, max_cluster_points: int = 48) -> float:
    """Official KUCCPS CWP formula: sqrt((r/m) * (t/48)) * 48."""
    if raw_points <= 0 or agg_points <= 0:
        return 0.0
    t = (agg_points / 84.0) * 48.0
    cwp = math.sqrt((raw_points / max_cluster_points) * (t / 48.0)) * 48.0
    return round(cwp, 3)


def meets_minimum_requirements(grades: Dict[str, str], minimum_requirements: Dict[str, str], mean_grade: str = "C+") -> bool:
    for subject, min_grade in minimum_requirements.items():
        candidate_grade = find_grade_for_subject(grades, subject)
        # A subject the student did not sit cannot satisfy a minimum-grade
        # requirement for it (e.g. no Biology -> no Medicine). This used to
        # fall back to the mean grade, which was harmless while every gated
        # subject was compulsory, but would let a student who skipped an
        # optional subject (Biology, Physics, Geography) clear its gate.
        if candidate_grade is None:
            return False
        if grade_to_points(candidate_grade) < grade_to_points(min_grade):
            return False
    return True


def extract_ml_feature_points(grades: Dict[str, str], mean_grade: str = "C+") -> Dict[str, int]:
    """Returns {subject: points} for every ML_FEATURE_SUBJECTS entry.

    A subject the student didn't take defaults to their mean grade (the same
    fallback used everywhere else in this module) rather than a fabricated
    weak grade - the model then treats it roughly as "about average", not
    "failed this subject". Used identically by the training pipeline
    (synthetic_data_generator.py) and by main.py at inference time, so the
    two can never drift apart.
    """
    return {
        subject: grade_to_points(find_grade_for_subject(grades, subject), default=mean_grade)
        for subject in ML_FEATURE_SUBJECTS
    }


def university_cutoff_summary(student_score: float, offerings, fallback_cutoff: Optional[float] = None):
    """How a student's Cluster Weighted Points compare with each university's
    own latest cutoff for the same programme (cutoffs differ by university and
    change every year). Returns None when there is nothing to compare with.

    `offerings` is a programme's offeringUniversities list. If it has no usable
    latestCutoff values, `fallback_cutoff` (the programme-level average) is used
    as a single stand-in so a programme is never left unranked."""
    cutoffs = [
        (float(u["latestCutoff"]), u.get("universityName") or "")
        for u in (offerings or [])
        if (u.get("latestCutoff") or 0) > 0
    ]
    if not cutoffs and fallback_cutoff:
        cutoffs = [(float(fallback_cutoff), "")]
    if not cutoffs:
        return None
    lowest, lowest_name = min(cutoffs)
    return {
        "total": len(cutoffs),
        "meets": sum(1 for c, _ in cutoffs if student_score >= c),
        "lowest": round(lowest, 2),
        "lowestUniversity": lowest_name,
        "gap": round(student_score - lowest, 1),
    }


# A student this close to (but under) the lowest cutoff still has a realistic
# chance, because cutoffs move from year to year.
CLOSE_CALL_MARGIN = 1.5


def cutoff_tier(summary) -> int:
    """0 = meets at least one university's cutoff, 1 = just under the lowest,
    2 = a real reach. Programmes with no cutoff data rank as 1 (neutral)."""
    if summary is None:
        return 1
    if summary["meets"] > 0:
        return 0
    return 1 if summary["gap"] >= -CLOSE_CALL_MARGIN else 2


def eligibility_status(
    student_score: float, cutoff: float, meets_requirements: bool = True, university_summary=None
) -> str:
    """`meets_requirements` is the hard KUCCPS minimum-subject-grade gate
    (see meets_minimum_requirements above) - a student who fails it cannot
    be admitted regardless of how close their Cluster Weighted Points are
    to the cutoff, so that case gets its own explicit message rather than
    being folded into "High Risk", which would wrongly imply admission is
    merely unlikely rather than impossible without improving specific
    subject grades.

    When `university_summary` (see university_cutoff_summary) is given, the
    message compares the student with each university's own latest cutoff
    instead of one programme-wide average, and never promises admission -
    cutoffs change every year."""
    if not meets_requirements:
        return "Does Not Meet Minimum Subject Requirements"
    if university_summary is not None:
        total, meets = university_summary["total"], university_summary["meets"]
        lowest = university_summary["lowest"]
        if meets > 0:
            if total == 1:
                return "Meets the latest cutoff"
            where = "all" if meets == total else f"{meets} of"
            return f"Meets the latest cutoff at {where} {total} universities"
        short = abs(university_summary["gap"])
        if university_summary["gap"] >= -CLOSE_CALL_MARGIN:
            return f"Close call: {short} pts below the lowest cutoff ({lowest})"
        return f"Reach: {short} pts below the lowest cutoff ({lowest})"
    diff = round(student_score - cutoff, 1)
    if diff >= 0.0:
        return f"Likely Admission (+{diff} pts margin)"
    if diff >= -1.5:
        return f"Competitive / Borderline ({diff} pts from cutoff)"
    return f"Reach / High Risk ({diff} pts from cutoff)"
