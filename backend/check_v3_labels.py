"""Label checks on xgboost_training_dataset_v3.csv.

1. Gap (cluster-weighted points - averageCutoff) for each row's own label.
2. Profiles redirected by the cutoff rule: the best-scoring programme(s) among all
   subject-eligible programmes include none the student reaches, so the label is a
   reachable programme with a lower score. The CSV does not record which optional
   subjects were sat, so the seed-42 generation is replayed in memory (nothing is
   written) to recover each row's raw grades, and the replay must match the CSV exactly.
3. assign_programme_label on 1,000 fresh profiles drawn with a different seed, then on
   1,000 profiles with uniform random grades (mean C+ or above).

    python check_v3_labels.py
"""
import contextlib
import io
import os
import random
from collections import Counter

import numpy as np
import pandas as pd

import synthetic_data_generator as gen
from kuccps import meets_minimum_requirements

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "xgboost_training_dataset_v3.csv")
FRESH_SEED = 2026
FRESH_COUNT = 1000


def check_gaps(df: pd.DataFrame) -> None:
    gaps = np.array([row[gen.CLUSTER_SCORE_COLUMN[row["programme_label"]]] for _, row in df.iterrows()])
    print("1. Gap (cluster-weighted points - averageCutoff) for each row's label")
    print(f"   rows: {len(gaps)}")
    print(f"   minimum: {gaps.min():.4f}")
    print(f"   mean: {gaps.mean():.4f}")
    print(f"   maximum: {gaps.max():.4f}")
    print(f"   rows with gap < 0: {int((gaps < 0).sum())}")
    print(f"   minimum >= 0: {gaps.min() >= 0}")


def replay_generation() -> tuple:
    calls = {}
    original_label = gen.assign_programme_label
    original_build = gen._build_profile_for_target

    def recording_label(grades, mean_grade, interests, strengths, aspiration):
        recording_label.last = (dict(grades), mean_grade, list(interests), list(strengths), aspiration)
        return original_label(grades, mean_grade, interests, strengths, aspiration)

    def recording_build(profile_id, target_title):
        rec = original_build(profile_id, target_title)
        calls[rec["student_id"]] = recording_label.last
        return rec

    gen.assign_programme_label = recording_label
    gen._build_profile_for_target = recording_build
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            replay = gen.generate_dataset(seed=42)
    finally:
        gen.assign_programme_label = original_label
        gen._build_profile_for_target = original_build
    return replay, calls


def check_redirects(df: pd.DataFrame) -> None:
    replay, calls = replay_generation()
    csv_cols = list(df.columns)
    replay = replay[csv_cols]
    replay_csv = pd.read_csv(io.StringIO(replay.to_csv(index=False)))
    identical = replay_csv.equals(df)
    print("\n2. Profiles redirected to a reachable programme by the cutoff rule")
    print(f"   replay of seed 42 identical to the CSV: {identical}")
    if not identical:
        raise SystemExit("Replay does not match the CSV; redirect count not computed.")

    redirected = 0
    for _, row in df.iterrows():
        grades, mean_grade, interests, strengths, aspiration = calls[row["student_id"]]
        eligible = [
            title for title in gen.TRAINED_PROGRAMME_TITLES
            if meets_minimum_requirements(grades, gen.CATALOG_BY_TITLE[title]["minimumSubjectRequirements"], mean_grade)
        ]
        scores = {t: gen._score_programme(t, interests, strengths, aspiration) for t in eligible}
        best = max(scores.values())
        top = eligible if best <= 0 else [t for t in eligible if scores[t] == best]
        if not any(row[gen.CLUSTER_SCORE_COLUMN[t]] >= 0 for t in top):
            redirected += 1
    print(f"   redirected: {redirected} of {len(df)} ({100 * redirected / len(df):.2f}%)")


def check_fresh_profiles() -> None:
    random.seed(FRESH_SEED)
    np.random.seed(FRESH_SEED)
    outcomes = Counter()
    for i in range(FRESH_COUNT):
        rec = gen._build_profile_for_target(i + 1, random.choice(gen.TRAINED_PROGRAMME_TITLES))
        outcomes[gen._discard_reason(rec) or "labelled"] += 1
    print(f"\n3. assign_programme_label on {FRESH_COUNT} fresh profiles (seed {FRESH_SEED}, not saved)")
    for key in ["labelled", "reaches no programme's cutoff", "no eligible programme", "below C+"]:
        print(f"   {key}: {outcomes[key]}")


def check_unbiased_profiles() -> None:
    random.seed(FRESH_SEED + 1)
    grade_names = list(gen.GRADE_POINTS)
    outcomes = Counter()
    redrawn_below_cplus = 0
    while sum(outcomes.values()) < FRESH_COUNT:
        subjects = list(gen.COMPULSORY_SUBJECTS) + random.sample(list(gen.FULL_OPTIONAL_SUBJECTS), random.randint(3, 5))
        grades = {s: random.choice(grade_names) for s in subjects}
        best_seven = sorted((gen.GRADE_POINTS[g] for g in grades.values()), reverse=True)[:7]
        mean_points = int(round(sum(best_seven) / len(best_seven)))
        if mean_points < gen.GRADE_POINTS["C+"]:
            redrawn_below_cplus += 1
            continue
        label = gen.assign_programme_label(
            grades, gen.points_to_grade(mean_points),
            random.sample(gen.INTERESTS_POOL, random.randint(2, 3)),
            random.sample(gen.STRENGTHS_POOL, random.randint(2, 3)),
            random.choice(gen.ASPIRATIONS_POOL),
        )
        rec = {"programme_label": label, "_no_cutoff_reached": gen._LAST_LABEL_FLAGS["no_cutoff_reached"]}
        outcomes[gen._discard_reason(rec) or "labelled"] += 1
    print(f"\n3b. assign_programme_label on {FRESH_COUNT} profiles with uniform random grades "
          f"(seed {FRESH_SEED + 1}, mean C+ or above, not saved)")
    print(f"   draws redrawn because the mean was below C+: {redrawn_below_cplus}")
    for key in ["labelled", "reaches no programme's cutoff", "no eligible programme", "below C+"]:
        print(f"   {key}: {outcomes[key]}")


def main() -> None:
    df = pd.read_csv(CSV_PATH)
    print(f"Dataset: {CSV_PATH}")
    check_gaps(df)
    check_redirects(df)
    check_fresh_profiles()
    check_unbiased_profiles()


if __name__ == "__main__":
    main()
