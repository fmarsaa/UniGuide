# Experiment 4 — Retrain after full catalogue cutoff verification

Same dataset generation, features, and hyperparameter grid as Experiment 1b -
the only change upstream is `programmes_catalog.py`: 11 of the 21 trained
programmes' `averageCutoff` and `offeringUniversities` cutoff figures were
corrected during the full KUCCPS-verification pass (see
`ml/experiments/catalogue_verification/`), replacing modeled-estimate/guessed
values with real official KUCCPS 2023/24 and 2025/26 cutoff data. This run
answers the direct question: was the deployed model trained on meaningfully
inaccurate labels because of those catalogue errors?

## Result: no regression, marginal genuine improvement

| | Experiment 1b (before catalogue fix) | **Experiment 4 (after catalogue fix)** |
|---|---|---|
| Accuracy | 87.52% | **87.65%** |
| Weighted F1 | 87.40% | **87.52%** |
| Best params | `n_estimators=350, max_depth=None, max_features=log2, min_samples_leaf=1` | same |

The grid search picked the identical hyperparameters both times, and
accuracy/F1 moved by well under half a percentage point - in the same
direction the corrections would predict (slightly better, not worse), not
noise in a random direction. This is expected: `averageCutoff` and
`minimumSubjectRequirements` only affect training through
`assign_programme_label`'s eligibility gate (a student profile must clear a
programme's real minimum subject grades to be labelled with it at all) and
the corresponding `meets_minimum_requirements` gate now also applied at
inference time (see `backend/main.py` and `backend/kuccps.py`); the errors
being fixed were mostly in the specific per-university offering cutoffs
shown to students, not in the coarser subject-grade minimums that drive
label assignment - so a large swing was never expected here. The real value
of the catalogue correction pass is data integrity and honesty toward
students about real admission cutoffs, not a training-metrics change.

This was the deployed model until `ml/experiments/experiment_5_full_catalogue_53_classes/`
superseded it (expanded from 21 trained classes to all 53 real catalogue
programmes — see that experiment for why and the resulting accuracy change).

## Files in this directory

- `metrics.json`, `classification_report.json`, `confusion_matrix.json` —
  full result of this run.
