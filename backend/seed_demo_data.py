"""Adds clearly labelled demonstration students to Firestore so the admin portal's
Insights, Feedback and popularity pages have something to show in a demo, and
removes them again afterwards.

    python seed_demo_data.py             # dry run: shows what would be added
    python seed_demo_data.py --yes       # adds the demo students
    python seed_demo_data.py --remove    # dry run: lists the demo students that would be deleted
    python seed_demo_data.py --remove --yes

Every demo student has a uid starting with "demoseed-", an @example.com email
(a reserved domain, so no real person) and demoSeed: true. Their profiles are
fictional, but their recommendations come from the real model and catalogue,
exactly as a real request would. No Firebase Auth accounts are created and no
audit log entries are written, so the audit log stays a true record.
"""
import contextlib
import io
import random
import sys
from datetime import datetime, timedelta, timezone

with contextlib.redirect_stdout(io.StringIO()):
    import main
from kuccps import COMPULSORY_SUBJECTS, UNDECIDED_ASPIRATION, grade_to_points, points_to_grade
from synthetic_data_generator import (
    ASPIRATION_LIKELY_OPTIONALS,
    PROGRAMME_ASPIRATIONS,
    PROGRAMME_INTERESTS,
    PROGRAMME_STRENGTHS,
    TRAINED_PROGRAMME_TITLES,
)

PREFIX = "demoseed-"
N_STUDENTS = 40
DAYS = 30
GRADES = ["C", "C+", "B-", "B", "B+", "A-", "A"]
OTHER_OPTIONALS = ["Biology", "Physics", "Geography", "History & Government", "Business Studies",
                   "Christian Religious Education (CRE)", "Computer Studies", "Agriculture"]
COMMENTS = [
    "The explanations helped me understand why each programme was suggested.",
    "Good matches. I would like more information about fees.",
    "The cutoff comparison was very useful.",
    "Two of the three were what I expected; the third was a nice surprise.",
    "Easy to use. The what-if tool showed me what to aim for.",
    "",
]
USER = {"uid": "demo-seed", "email_verified": True}


def _profile(rng: random.Random) -> main.StudentProfilePayload:
    target = rng.choice(TRAINED_PROGRAMME_TITLES)
    level = rng.choice([2, 3, 3, 4, 4, 4, 5, 5, 6])  # index into GRADES, centred on B/B+

    def grade():
        return GRADES[max(0, min(len(GRADES) - 1, level + rng.choice([-1, 0, 0, 1])))]

    undecided = rng.random() < 0.3
    aspiration = UNDECIDED_ASPIRATION if undecided else rng.choice(PROGRAMME_ASPIRATIONS[target])
    optionals = list(ASPIRATION_LIKELY_OPTIONALS.get(aspiration, []))[:3]
    for subject in rng.sample(OTHER_OPTIONALS, len(OTHER_OPTIONALS)):
        if len(optionals) >= 3:
            break
        if subject not in optionals:
            optionals.append(subject)
    grades = {s: grade() for s in COMPULSORY_SUBJECTS + optionals}
    mean = points_to_grade(round(sum(grade_to_points(g) for g in grades.values()) / len(grades)))
    if grade_to_points(mean) < grade_to_points("C+"):
        grades = {s: "C+" for s in grades}
        mean = "C+"
    return main.StudentProfilePayload(
        kcseMeanGrade=mean,
        grades=grades,
        interests=rng.sample(PROGRAMME_INTERESTS[target], min(2, len(PROGRAMME_INTERESTS[target]))),
        strengths=rng.sample(PROGRAMME_STRENGTHS[target], min(2, len(PROGRAMME_STRENGTHS[target]))),
        aspirations=[] if undecided else [aspiration],
    )


def plan(rng: random.Random, now: datetime) -> list:
    students = []
    for n in range(1, N_STUDENTS + 1):
        uid = f"{PREFIX}{n:03d}"
        created = now - timedelta(days=rng.uniform(0, DAYS - 1), hours=rng.uniform(0, 8))
        entry = {"uid": uid, "email": f"demo.student{n:02d}@example.com", "fullName": f"Demo Student {n:02d}",
                 "createdAt": created, "profile": None, "recommendations": [], "saved": [], "feedback": None}
        students.append(entry)
        if rng.random() < 0.15:
            continue  # registered but never entered grades
        payload = _profile(rng)
        entry["profile"] = payload
        when = created + timedelta(minutes=rng.uniform(5, 40))
        for _ in range(rng.choice([1, 1, 2, 2, 3])):
            if when > now:
                break
            results = main.get_recommendations(payload, USER, preview=True)["recommendations"]
            entry["recommendations"].append((when, results))
            when += timedelta(days=rng.uniform(0.2, 5))
        shown = entry["recommendations"][-1][1] if entry["recommendations"] else []
        if shown and rng.random() < 0.6:
            picks = rng.sample(shown, rng.choice([1, 1, 2]) if len(shown) > 1 else 1)
            entry["saved"] = [(p["programme"]["id"], entry["recommendations"][-1][0] + timedelta(minutes=3)) for p in picks]
        if shown and rng.random() < 0.45:
            entry["feedback"] = {
                "rating": rng.choice([3, 4, 4, 5, 5, 5]),
                "comments": rng.choice(COMMENTS),
                "submittedAt": entry["recommendations"][-1][0] + timedelta(minutes=6),
            }
    return students


def write(db, students: list) -> None:
    for s in students:
        ref = db.collection("students").document(s["uid"])
        doc = {"uid": s["uid"], "email": s["email"], "fullName": s["fullName"], "role": "student",
               "createdAt": s["createdAt"], "demoSeed": True}
        p = s["profile"]
        if p is not None:
            doc.update({"kcseMeanGrade": p.kcseMeanGrade, "grades": p.grades, "interests": p.interests,
                        "strengths": p.strengths, "aspirations": p.aspirations, "updatedAt": s["createdAt"]})
        ref.set(doc)
        for when, results in s["recommendations"]:
            ref.collection("recommendations").add({
                "recommendations": results,
                "modelVersion": results[0].get("modelVersion") if results else None,
                "createdAt": when,
            })
        for programme_id, when in s["saved"]:
            ref.collection("shortlist").document(programme_id).set({"savedAt": when})
        if s["feedback"]:
            ref.collection("feedback").add({"recommendationId": None, **s["feedback"]})


def remove(db, confirmed: bool) -> None:
    targets = [d.id for d in db.collection("students").stream() if d.id.startswith(PREFIX)]
    print(f"Demo students found: {len(targets)}")
    if not confirmed:
        print("Dry run - nothing deleted. Add --yes to delete them.")
        return
    for uid in targets:
        main.delete_student_data(db, uid)
    print(f"Deleted {len(targets)} demo students and their recommendations, saved programmes and feedback.")


def run(argv: list) -> None:
    db = main.get_db()
    if db is None:
        raise SystemExit("Firestore is not configured.")
    confirmed = "--yes" in argv
    if "--remove" in argv:
        remove(db, confirmed)
        return
    existing = [d.id for d in db.collection("students").stream() if d.id.startswith(PREFIX)]
    if existing:
        raise SystemExit(f"{len(existing)} demo students already exist. Remove them first with --remove --yes.")
    students = plan(random.Random(2026), datetime.now(timezone.utc))
    profiled = [s for s in students if s["profile"] is not None]
    print(f"Demo students: {len(students)} ({len(profiled)} with grades, {len(students) - len(profiled)} registered only)")
    print(f"Recommendation records: {sum(len(s['recommendations']) for s in students)}")
    print(f"Saved programmes: {sum(len(s['saved']) for s in students)}")
    print(f"Feedback entries: {sum(1 for s in students if s['feedback'])}")
    print(f"Registration dates: last {DAYS} days")
    if not confirmed:
        print("Dry run - nothing written. Add --yes to write these to Firestore.")
        return
    write(db, students)
    print("Written to Firestore.")


if __name__ == "__main__":
    run(sys.argv[1:])
