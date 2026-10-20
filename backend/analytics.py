"""Aggregates behind the admin Insights page. Everything here works on plain lists
of dictionaries and returns only counts, never names, emails or grades of an
individual student, so the page can be shown to any administrator."""

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

GRADE_ORDER = ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "E"]
GROWTH_DAYS = 30


def day_of(timestamp) -> Optional[str]:
    """A Firestore timestamp as a YYYY-MM-DD day in UTC, or None if it is not a timestamp."""
    if not hasattr(timestamp, "astimezone"):
        return None
    return timestamp.astimezone(timezone.utc).date().isoformat()


def eligibility_bucket(item: dict) -> str:
    """Whether a recommended programme was within reach of the student when it was shown."""
    if item.get("meetsMinimumRequirements") is False:
        return "missingSubject"
    summary = item.get("universityCutoffs")
    if summary:
        return "meetsCutoff" if summary.get("meets", 0) > 0 else "belowCutoff"
    diff = item.get("cutoffDiff")
    if isinstance(diff, (int, float)):
        return "meetsCutoff" if diff >= 0 else "belowCutoff"
    return "belowCutoff"


def build_overview(
    students: List[dict],
    recommendations: List[dict],
    feedback: List[dict],
    saved: List[dict],
    titles_by_id: Dict[str, str],
    now: Optional[datetime] = None,
) -> dict:
    """students: {uid, createdAt, kcseMeanGrade, aspirations}
    recommendations: {uid, createdAt, items: [recommended programme dicts]}
    feedback: {uid, rating}    saved: {uid, programmeId}"""
    now = now or datetime.now(timezone.utc)
    today = now.astimezone(timezone.utc).date()
    last7 = (today - timedelta(days=6)).isoformat()
    last30 = (today - timedelta(days=29)).isoformat()

    # --- people
    registered_by_day = Counter(d for d in (day_of(s.get("createdAt")) for s in students) if d)
    before_window = sum(c for d, c in registered_by_day.items() if d < (today - timedelta(days=GROWTH_DAYS - 1)).isoformat())
    growth, running = [], before_window
    for offset in range(GROWTH_DAYS - 1, -1, -1):
        day = (today - timedelta(days=offset)).isoformat()
        running += registered_by_day.get(day, 0)
        growth.append({"date": day, "newStudents": registered_by_day.get(day, 0), "totalStudents": running})

    active7, active30 = set(), set()
    for rec in recommendations:
        day = day_of(rec.get("createdAt"))
        if day and day >= last30:
            active30.add(rec["uid"])
        if day and day >= last7:
            active7.add(rec["uid"])

    ratings = [f["rating"] for f in feedback if isinstance(f.get("rating"), (int, float)) and 1 <= f["rating"] <= 5]
    rating_counts = Counter(int(r) for r in ratings)

    # --- journey: how many students reach each step
    with_profile = {s["uid"] for s in students if s.get("kcseMeanGrade")}
    with_recs = {r["uid"] for r in recommendations}
    with_saved = {s["uid"] for s in saved}
    with_feedback = {f["uid"] for f in feedback}
    funnel = [
        {"stage": "Registered", "count": len(students)},
        {"stage": "Entered grades", "count": len(with_profile)},
        {"stage": "Received recommendations", "count": len(with_recs)},
        {"stage": "Saved a programme", "count": len(with_saved)},
        {"stage": "Gave feedback", "count": len(with_feedback)},
    ]

    # --- who the students are (counts only)
    grades = Counter(s["kcseMeanGrade"] for s in students if s.get("kcseMeanGrade") in GRADE_ORDER)
    grade_distribution = [{"grade": g, "count": grades.get(g, 0)} for g in GRADE_ORDER]
    profiled = [s for s in students if s.get("kcseMeanGrade")]
    decided = sum(1 for s in profiled if s.get("aspirations"))
    career_choice = {"decided": decided, "undecided": len(profiled) - decided}

    # --- what they were shown and what they kept
    outcome = Counter(eligibility_bucket(item) for rec in recommendations for item in rec.get("items", []))
    saved_counts = Counter(s["programmeId"] for s in saved)
    top_saved = [
        {"title": titles_by_id.get(pid, pid), "count": count}
        for pid, count in saved_counts.most_common(5)
    ]

    return {
        "totals": {
            "students": len(students),
            "newLast7Days": sum(c for d, c in registered_by_day.items() if d >= last7),
            "active7Days": len(active7),
            "active30Days": len(active30),
            "recommendations": len(recommendations),
            "savedProgrammes": len(saved),
            "feedback": len(feedback),
            "averageRating": round(sum(ratings) / len(ratings), 2) if ratings else None,
        },
        "growth": growth,
        "funnel": funnel,
        "gradeDistribution": grade_distribution,
        "careerChoice": career_choice,
        "eligibility": {
            "meetsCutoff": outcome.get("meetsCutoff", 0),
            "belowCutoff": outcome.get("belowCutoff", 0),
            "missingSubject": outcome.get("missingSubject", 0),
        },
        "ratingDistribution": [{"rating": r, "count": rating_counts.get(r, 0)} for r in range(1, 6)],
        "topSaved": top_saved,
    }
