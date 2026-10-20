"""Turns the observed student sessions into the numbers and sentences for Section 5.4.4.

    python ml/experiments/student_evaluation/analyse_sessions.py [sessions.csv]

Fill sessions.csv from sessions_template.csv, one row per student, with an ID such as S01 and
no names. The file is git-ignored. Columns:
  id, device (emulator or phone), mean_grade,
  placed_course, placed_university           the course the student was placed in or chose
  shown_1, shown_2, shown_3                  the three programmes the app showed
  finished_without_help (yes/no), minutes    time to a result
  rating_easy, rating_reasons, rating_consider, rating_recommend   each 1 to 5
  comment
Nothing is invented: every figure comes from the rows in the file, and with no file it stops.
"""
import csv
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "backend"))

RATINGS = {
    "rating_easy": "the application was easy to use",
    "rating_reasons": "they understood the reasons given",
    "rating_consider": "they would consider the suggested programmes",
    "rating_recommend": "they would recommend the application",
}


def normalise(name: str) -> str:
    text = (name or "").lower()
    text = re.sub(r"\(.*?\)", " ", text)
    text = re.sub(r"\b(bachelor|bsc|ba|beng|bcom|b\.|of|in|and|science|sciences|arts|degree|the)\b", " ", text)
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def same_programme(a: str, b: str) -> bool:
    x, y = normalise(a), normalise(b)
    return bool(x) and bool(y) and (x == y or x in y or y in x)


def is_yes(value: str) -> bool:
    return (value or "").strip().lower() in ("yes", "y", "true", "1")


def analyse(rows, catalogue_titles):
    n = len(rows)
    finished = sum(1 for r in rows if is_yes(r["finished_without_help"]))
    minutes = [float(r["minutes"]) for r in rows if (r.get("minutes") or "").strip()]
    covered = [r for r in rows if any(same_programme(r["placed_course"], t) for t in catalogue_titles)]
    hits = [r for r in covered if any(same_programme(r["placed_course"], r[f"shown_{i}"]) for i in (1, 2, 3))]
    ratings = {}
    for key in RATINGS:
        values = [int(r[key]) for r in rows if (r.get(key) or "").strip()]
        ratings[key] = {
            "n": len(values),
            "mean": round(statistics.mean(values), 2) if values else None,
            "agree": sum(1 for v in values if v >= 4),
        }
    return {
        "students": n,
        "finished_without_help": finished,
        "median_minutes": round(statistics.median(minutes), 1) if minutes else None,
        "placed_in_covered_programme": len(covered),
        "not_covered": n - len(covered),
        "hit_in_top_three": len(hits),
        "ratings": ratings,
        "devices": sorted({r.get("device", "").strip() for r in rows if r.get("device")}),
    }


def describe(result) -> str:
    n = result["students"]
    lines = [f"{n} students took part (device: {', '.join(result['devices']) or 'not recorded'})."]
    lines.append(f"{result['finished_without_help']} of {n} reached a result without help"
                 + (f", with a median time of {result['median_minutes']} minutes." if result["median_minutes"] is not None else "."))
    c = result["placed_in_covered_programme"]
    if c:
        lines.append(f"{c} of the {n} students had been placed in, or chose, a programme the system covers. "
                     f"For {result['hit_in_top_three']} of these {c} ({100 * result['hit_in_top_three'] / c:.0f}%), that programme was among the three shown.")
    lines.append(f"The other {result['not_covered']} chose a programme outside the 53 the system covers.")
    for key, label in RATINGS.items():
        r = result["ratings"][key]
        if r["n"]:
            lines.append(f"On average students rated that {label} {r['mean']} out of 5, and {r['agree']} of {r['n']} gave 4 or 5.")
    return " ".join(lines)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "sessions.csv")
    if not os.path.isfile(path):
        sys.exit(f"No session file at {path}. Copy sessions_template.csv to sessions.csv and fill it from the real sessions.")
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [r for r in csv.DictReader(f) if (r.get("id") or "").strip()]
    if not rows:
        sys.exit("The file has no student rows yet.")
    from programmes_catalog import PROGRAMMES
    result = analyse(rows, [p["title"] for p in PROGRAMMES])
    print(describe(result))
    print()
    for key, label in RATINGS.items():
        r = result["ratings"][key]
        print(f"{key:18s} mean {r['mean']}  (4 or 5: {r['agree']}/{r['n']})")
    print("\nComments:")
    for r in rows:
        if (r.get("comment") or "").strip():
            print(f"  {r['id']}: {r['comment'].strip()}")


if __name__ == "__main__":
    main()
