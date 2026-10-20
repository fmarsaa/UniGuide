"""Compares ways of choosing the three programmes shown to a student, on generated profiles.

The deployed rule ranks every programme the student can reach (cutoff met) ahead of any programme that is a
better fit but just out of reach. This script replays 3,000 generated profiles through that rule and through
alternatives, and reports how often the programme the profile was labelled with appears among the three shown
and how many of the three shown are within reach.

Each profile is scored by a model that never saw it (five-fold out-of-fold probabilities), because the deployed
model was fitted on all the profiles and would simply remember their labels.

    python ml/experiments/experiment_9_ranking_strategies/compare_ranking.py
"""
import os
import sys

import numpy as np
from sklearn.base import clone
from sklearn.model_selection import StratifiedKFold, cross_val_predict

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(HERE, "..", "..", "..", "backend")
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

import main  # noqa: E402
from kuccps import (aggregate_points, cluster_weighted_points, cutoff_tier, meets_minimum_requirements,  # noqa: E402
                    points_to_grade, raw_cluster_points, university_cutoff_summary)
from synthetic_data_generator import create_synthetic_dataset  # noqa: E402
from train_random_forest import DATASET_SIZE, FEATURE_COLUMNS  # noqa: E402

COLUMNS = {"math_score": "Mathematics", "eng_score": "English", "kis_score": "Kiswahili", "chem_score": "Chemistry",
           "bio_score": "Biology", "phys_score": "Physics", "history_score": "History", "business_score": "Business Studies",
           "geography_score": "Geography"}


def context(row, classes, proba):
    grades = {name: points_to_grade(int(row[col])) for col, name in COLUMNS.items() if row[col] and row[col] > 0}
    mean_grade = points_to_grade(int(round(row["mean_points"])))
    eligible = [i for i, c in enumerate(classes) if main.meets_minimum_requirements(
        grades, main.CATALOG_BY_TITLE[c]["minimumSubjectRequirements"], mean_grade)]
    agg = aggregate_points(grades, mean_grade)
    info = {}
    for i in eligible:
        prog = main.CATALOG_BY_TITLE[classes[i]]
        cwp = cluster_weighted_points(raw_cluster_points(grades, prog["clusterSubjects"], mean_grade), agg)
        info[i] = cutoff_tier(university_cutoff_summary(cwp, prog.get("offeringUniversities"), prog.get("averageCutoff")))
    return eligible, info


def current(eligible, info, p):
    return sorted(eligible, key=lambda i: (info[i] + (3 if p[i] < 0.02 else 0), -p[i]))[:3]


def best_fit_slot(eligible, info, p):
    """Two places by the current rule, and the third goes to the best fit even if it is a reach."""
    best = max(eligible, key=lambda i: p[i])
    first = [i for i in current(eligible, info, p) if i != best][:2]
    return first + [best]


def best_fit_first(eligible, info, p):
    """The best fit is shown first (even if it is a stretch), then the two best programmes the student can reach."""
    best = max(eligible, key=lambda i: p[i])
    rest = [i for i in current(eligible, info, p) if i != best][:2]
    return [best] + rest


def fit_floor(eligible, info, p, share=0.5):
    """Reachable programmes only count if they fit at least half as well as the best fit."""
    top = max(p[i] for i in eligible)
    keep = [i for i in eligible if p[i] >= share * top]
    chosen = sorted(keep, key=lambda i: (info[i], -p[i]))[:3]
    for i in sorted(eligible, key=lambda i: -p[i]):
        if len(chosen) == 3:
            break
        if i not in chosen:
            chosen.append(i)
    return chosen


def fit_only(eligible, info, p):
    return sorted(eligible, key=lambda i: -p[i])[:3]


STRATEGIES = {"current rule": current, "best fit gets one place (last)": best_fit_slot,
              "best fit first, two reachable": best_fit_first,
              "reachable only if a good fit": fit_floor, "fit only (ignores cutoffs)": fit_only}

if __name__ == "__main__":
    full = create_synthetic_dataset(DATASET_SIZE)
    classes = main._pipeline.classes_
    oof = cross_val_predict(clone(main._pipeline), full[FEATURE_COLUMNS], full["programme_label"],
                            cv=StratifiedKFold(5, shuffle=True, random_state=42), method="predict_proba", n_jobs=1)
    picked = full.sample(3000, random_state=3).index
    df = full.loc[picked].reset_index(drop=True)
    proba = oof[picked]
    stats = {k: dict(top1=0, top3=0, reach=0, shown=0) for k in STRATEGIES}
    n = 0
    for k in range(len(df)):
        eligible, info = context(df.iloc[k], classes, proba[k])
        if len(eligible) < 3:
            continue
        n += 1
        label = list(classes).index(df.iloc[k]["programme_label"])
        for name, fn in STRATEGIES.items():
            chosen = fn(eligible, info, proba[k])
            s = stats[name]
            s["top1"] += chosen[0] == label
            s["top3"] += label in chosen
            s["reach"] += sum(1 for i in chosen if info[i] == 0)
            s["shown"] += len(chosen)
    print(f"profiles with at least three eligible programmes: {n}")
    print(f"{'strategy':36s} {'label first':>12s} {'label in top 3':>15s} {'shown that are within reach':>28s}")
    for name, s in stats.items():
        print(f"{name:36s} {100 * s['top1'] / n:11.1f}% {100 * s['top3'] / n:14.1f}% {100 * s['reach'] / s['shown']:27.1f}%")
