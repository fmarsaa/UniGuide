# Experiment 5 — Expand trained classes from 21 to all 53 catalogue programmes

## Motivation

Direct question raised in review: "what is the point of having [a programme]
in the catalogue if they are not being recommended?" Before this experiment,
`/api/recommend` could only ever suggest one of 21 programmes out of the 53
real, KUCCPS-verified programmes in `programmes_catalog.py` — the other 32
(e.g. Data Science & Analytics, Physiotherapy, Statistics, Sociology,
Business Management, Physics...) were browsable in the catalogue/directory
screens but structurally invisible to the recommender, no matter how well a
student's profile matched one of them. A curated subset would only relocate
the same problem onto whichever programmes were left out, so this closes the
gap for all 32 at once.

## What changed

`backend/synthetic_data_generator.py` gained, for all 32 new programmes:
one specific (exclusive-naming) career aspiration **plus** placement in a
shared, non-exclusive cluster aspiration — 4 new clusters ("Educator /
Teaching Professional (General)", "Social & Community Services Professional
(General)", "Applied & Physical Sciences Researcher (General)", "Tourism &
Hospitality Professional (General)") and 6 existing clusters extended
(Healthcare, Finance & Business, Built Environment, Agricultural &
Environmental, Quantitative Analyst, Public Policy). This deliberately
avoids repeating the aspiration-leakage bug fixed in
`experiment_1_profile_redesign/` — no new programme relies on a single
exclusive aspiration. ~20 new domain interests, ~22 new skills (each anchored
to that programme's own real `requiredSkills` text in the catalogue so
`_score_programme`'s existing substring match stays meaningful), and
extended strength associations (reusing the existing 7-strength pool, no new
strengths needed) were added the same way. `TRAINED_PROGRAMME_TITLES` now
lists all 53. `FALLBACK_ORDER` was recomputed by actually ranking every
programme's real minimum-requirement floor (not guessed) — it no longer
includes Nursing (real floor: a B), which was a strictly worse safety net
than several of the newly-available low-barrier programmes.

`train_random_forest.py`'s `DATASET_SIZE` was scaled 6000 → 15000 to roughly
preserve per-class density (~280/class) across 2.5x the classes; everything
else (hyperparameter grid, `THIN_CLASS_FLOOR`) was left unchanged so "more
classes" is the only real variable versus Experiment 4.

## Result: small, expected accuracy cost for full real-world coverage

| | Experiment 4 (21 classes) | **Experiment 5 (53 classes)** |
|---|---|---|
| Accuracy | 87.65% | **86.79%** |
| Weighted F1 | 87.52% | **86.65%** |
| Classes | 21 | **53** |
| Best params | `n_estimators=350, max_depth=None, max_features=log2, min_samples_leaf=1` | same |

A ~0.9pp drop for 2.5x the classes (many genuinely overlapping, e.g.
Chemistry/Industrial Chemistry/Biochemistry, or the various business-
management variants) is a good outcome for going from a 21-programme subset
to full real catalogue coverage. No **new** class stands out as unusually
confused: the weakest classes in this run (Software Engineering, F1 0.70;
Informatics and Computer Science, F1 0.75) were already the weakest classes
in Experiment 4 at nearly the same scores — a pre-existing ICS/SE overlap,
not something this expansion introduced. Every one of the 32 newly-trained
programmes lands with F1 ≥ 0.83, several above 0.90 (Social Work 0.94,
Forestry 0.93, Hospitality Management 0.93).

## Explicit, deliberate limitation this does NOT change

The real floor across the entire 53-programme catalogue is a plain "C" in
at least one subject — no programme in the catalogue requires less. A
genuinely straight-D/E student correctly still gets zero eligible matches
and the honest "Does Not Meet Minimum Subject Requirements" fallback
messaging added earlier — that's accurate to real KUCCPS admission rules,
not a bug this experiment should or does hide. What this experiment fixes is
the students who *do* clear "C"/"C+" tiers but whose best real fit was
previously invisible to the model simply because it wasn't one of the
original 21.

**This is now the model currently deployed** (`backend/rf_model_pipeline.pkl`
/ `backend/model_metrics.json` reflect this run), superseding Experiment 4.

## Files in this directory

- `metrics.json`, `classification_report.json`, `confusion_matrix.json` —
  full result of this run.
