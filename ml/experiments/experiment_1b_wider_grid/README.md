# Experiment 1b — Wider hyperparameter grid (isolated from Experiment 2)

Same dataset, same features, same labelling rule as Experiment 1 - the only
change is adding `classifier__max_features` (`sqrt` vs `log2`) to the
GridSearchCV grid in `train_random_forest.py`. Run in isolation, deliberately
separated from Experiment 2's cluster-score feature, after that combined run
showed a net regression and the two changes needed to be told apart.

## Result: genuine small improvement — this is now the deployed model

| | Experiment 1 | Experiment 2 (grid + cluster score) | **Experiment 1b (grid alone)** |
|---|---|---|---|
| Accuracy | 87.21% | 86.84% | **87.52%** |
| Weighted F1 | 87.09% | 86.69% | **87.40%** |
| Best params | `max_features` not searched (sklearn default `sqrt`) | `max_features=log2` | `max_features=log2` |

Isolating the two Experiment 2 changes shows clearly: the wider grid
(`max_features=log2` beating the default `sqrt`) is a genuine, if modest,
improvement on its own (+0.31pp accuracy over Experiment 1); the
cluster-score feature was actively harmful (comparing Experiment 2 to this
one: removing only the cluster-score feature recovers +0.68pp). Bundling
both together in Experiment 2 masked this - exactly why changes need to be
tested one at a time, per the plan agreed before this staged experiment
series began.

This was the deployed model until `ml/experiments/experiment_4_catalogue_corrected_retrain/`
superseded it (retrain on the same grid after `programmes_catalog.py`'s cutoff
figures were corrected against real KUCCPS data - no meaningful metric change,
see that experiment for why). `ml/experiments/experiment_1_profile_redesign/`
remains the record of the profile-generation methodology change; this
directory records the subsequent hyperparameter refinement on top of it.

## Files in this directory

- `metrics.json`, `classification_report.json`, `confusion_matrix.json` —
  full result of this run.
