# Experiment 2 — Cluster-weighted-points feature (REJECTED)

Tested the cluster-score feature proposed in the original brainstorm: one
extra numeric feature per trained programme, equal to the student's real
KUCCPS Cluster Weighted Points for that programme's own cluster-subject set
minus that programme's real average cutoff (positive = above cutoff,
negative = below). Implementation: `synthetic_data_generator.build_cluster_score_features`,
wired into both training (`_build_profile_for_target`) and serving
(`main.py`'s `profile_to_feature_row`) so the two could never disagree.

## Result: did not help — reverted

| | Experiment 1 (deployed) | Experiment 2 (this one) |
|---|---|---|
| Accuracy | 87.21% | 86.84% |
| Weighted F1 | 87.09% | 86.69% |
| Software Engineering recall (weakest class) | 0.65 | **0.58** |

A small net regression, concentrated on the already-weakest class getting
weaker. Per the rule agreed before running any of this — *"if cluster scores
genuinely improve the model, keep them; if they don't, remove them"* — they
were removed. `INCLUDE_CLUSTER_SCORE_FEATURES` in `train_random_forest.py`
is back to `False`, and the deployed model was retrained back to
Experiment 1's exact configuration.

## Why it plausibly didn't help

The cluster-score feature is a linear-ish recombination of information the
model already had access to (the same per-subject grade points already feed
`NUMERIC_FEATURES` directly). Random Forest splits don't need that
recombination handed to them explicitly the way a linear model would - it
can already approximate "is this student near this programme's cutoff" by
splitting on the underlying grades. Adding a near-redundant feature just
gives the tree-building process more candidate features to split on without
adding new information, which can dilute rather than sharpen splits,
particularly for a class already starved for distinguishing signal (SE).

## A methodology note worth stating honestly

This run changed **two things at once** — the cluster-score feature *and* a
wider hyperparameter grid (`max_features` added) — rather than one variable
at a time, which was the explicit rule agreed for this whole staged
experiment plan. The result was negative either way, so both were reverted
together rather than spending further training runs isolating which one
contributed more. If revisited later, they should be tested separately.

## Files in this directory

- `metrics.json`, `classification_report.json`, `confusion_matrix.json` —
  the full result of this rejected run, kept for the record rather than
  deleted, so "we tried this and it didn't work" is demonstrable, not just
  asserted.
