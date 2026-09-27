# Experiment 0 — Baseline (21 classes, current generation method)

Frozen snapshot of the currently-deployed model, preserved before any changes
to the synthetic data generation methodology. `backend/model_metrics.json`
and `backend/rf_model_pipeline.pkl` are both `.gitignore`d and get
overwritten in place on every training run, so nothing about this state
survives past the next retrain unless captured here first.

## Headline numbers

- **Accuracy: 68.91%** | **Weighted F1: 68.44%** | **Macro F1: 70.25%**
- 5-fold `StratifiedKFold` cross-validated, out-of-fold predictions across
  the full dataset (not a single 80/20 holdout split — see
  `metrics.json.evaluation_method`)
- 6,612 total profiles / 21 classes (see `class_distribution.json`)
- 53 numeric features + 1 one-hot categorical feature (see
  `feature_config.json`)

## What this baseline represents, honestly

Every label was assigned by a deterministic rule (`assign_programme_label`
in `backend/synthetic_data_generator.py`), not by real KUCCPS placement
outcomes or human raters — no such dataset exists publicly. The rule gates
on real KUCCPS subject-grade minimums, then scores eligible programmes by
matching a synthetic student's interests/skills/strengths/aspiration
against the programme, then breaks ties by closeness of Cluster Weighted
Points to the real cutoff. The Random Forest is trained to reproduce that
rule. **68.9% accuracy measures how well the model learned the rule, not
validated real-world predictive accuracy.**

## Known issue driving Experiment 1

10 of these 21 classes have an aspiration option that maps to them
*exclusively* (e.g. "Dentist" → Bachelor of Dental Surgery only), worth
+4.0 in the labeling score versus +2.0 for an interest match or +1.0 for a
skill/strength match. For those classes, when a synthetic profile states
the matching aspiration, the model's job is close to a single-feature
lookup rather than genuine reasoning over the full profile. This wasn't
caught until after those 10 classes were added and is the primary thing
Experiment 1 (improved profile generation) is meant to fix — see
`feature_config.json.scoring_weights_in_label_assignment.note`.

## Five smallest classes were targeted-oversampled

MBChB, BDS, EEE, Pharmacy, and Civil Engineering were all naturally too
rare (35-117 profiles) under pure random generation for their per-class
test metrics to be trustworthy (a single misclassification could swing a
7-example test slice's recall by ~14 points). Each was boosted to a floor
of 175 via biased-but-not-forced targeted generation (see
`oversample_thin_classes` in `synthetic_data_generator.py`) — their
resulting counts do not represent naturally-occurring KUCCPS eligibility
frequency the way the other 16 classes' counts do. Flagged explicitly in
`class_distribution.json` (`"oversampled": true`).

## Files in this directory

- `metrics.json` — accuracy, weighted/macro F1, best hyperparameters,
  evaluation method, reference 80/20 holdout numbers
- `classification_report.json` — full per-class precision/recall/F1/support
- `confusion_matrix.json` — full 21x21 confusion matrix with labels
- `class_distribution.json` — per-class profile counts, flagging which 5
  were targeted-oversampled and their pre-oversampling counts
- `feature_config.json` — exact feature list, scoring weights, classifier
  hyperparameters and search method
