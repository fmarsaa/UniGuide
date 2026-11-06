"""Task A step 1 checks for the v4 feature representation.

a) Prints the source of the eligibility and cluster-point functions and every call
   site in main.py and synthetic_data_generator.py, showing what they are given.
b) Replays the seed-42 generation of the v3 dataset in memory (nothing is written)
   and counts, per model subject column, the rows whose student did not take that
   subject and whose v3 column was filled with the mean grade points instead.

    python check_v4_inputs.py
"""
import inspect
import os
import re

import pandas as pd

import kuccps
from check_v3_labels import replay_generation

HERE = os.path.dirname(os.path.abspath(__file__))
V3_CSV = os.path.join(HERE, "xgboost_training_dataset_v3.csv")
FUNCTIONS = ["meets_minimum_requirements", "raw_cluster_points", "aggregate_points",
             "cluster_weighted_points", "find_grade_for_subject", "grade_to_points",
             "extract_ml_feature_points"]
CALL_PATTERN = re.compile(r"\b(" + "|".join(FUNCTIONS[:4] + ["extract_ml_feature_points"]) + r")\(")


def print_sources() -> None:
    print("a) Source of the functions in kuccps.py")
    for name in FUNCTIONS:
        print(f"\n--- kuccps.{name} ---")
        print(inspect.getsource(getattr(kuccps, name)).rstrip())

    print("\na) Every call site outside kuccps.py (file:line: code)")
    for filename in ["main.py", "synthetic_data_generator.py"]:
        with open(os.path.join(HERE, filename), encoding="utf-8") as f:
            for number, line in enumerate(f, start=1):
                if CALL_PATTERN.search(line) and not line.lstrip().startswith(("def ", "#")):
                    print(f"{filename}:{number}: {line.strip()}")


def count_filled_subjects() -> None:
    v3 = pd.read_csv(V3_CSV)
    replay, calls = replay_generation()
    print("\nb) Untaken subjects filled in the v3 dataset (seed-42 replay)")
    print(f"   replay rows: {len(replay)}, v3 rows: {len(v3)}, "
          f"student_id and labels identical: "
          f"{list(replay['student_id']) == list(v3['student_id']) and list(replay['programme_label']) == list(v3['programme_label'])}")
    for subject in kuccps.ML_FEATURE_SUBJECTS:
        column = kuccps.FEATURE_COLUMN[subject]
        untaken = 0
        filled_with_mean = 0
        for _, row in v3.iterrows():
            grades, mean_grade, _, _, _ = calls[row["student_id"]]
            if kuccps.find_grade_for_subject(grades, subject) is None:
                untaken += 1
                if row[column] == kuccps.grade_to_points(mean_grade):
                    filled_with_mean += 1
        print(f"   {subject:<17} ({column}): untaken in {untaken} of {len(v3)} rows; "
              f"filled with the mean grade points in {filled_with_mean}")


def main() -> None:
    print_sources()
    count_filled_subjects()


if __name__ == "__main__":
    main()
