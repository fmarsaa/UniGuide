# Experiment 1 — Redesigned profile generation (same 21 classes)

Same 21 trained programmes as the baseline, same labelling rule
(`assign_programme_label`, unchanged weights), same feature schema. What
changed is the generator: `programme_profiles.md` in this directory captures
the design discussion; this README and the JSON files next to it capture
what actually got built and measured from it.

## Headline numbers

- **Accuracy: 87.21%** | **Weighted F1: 87.09%** | **Macro F1: 87%**
- 5-fold `StratifiedKFold` cross-validated, out-of-fold predictions across
  the full dataset (same evaluation method as the baseline — see
  `metrics.json.evaluation_method`)
- Reference 80/20 holdout (fit on train split only): **88.26% accuracy /
  88.20% weighted F1** — close to the CV number, which is reassuring on its
  own (a large gap between the two would suggest the CV number was
  optimistic)
- 6,050 total profiles / 21 classes, ranging 200–536 per class (see
  `class_distribution.json`) — versus the baseline's 137–985 range

**Baseline comparison:**

| | Baseline (21 classes) | Experiment 1 |
|---|---|---|
| Accuracy | 68.91% | 87.21% |
| Weighted F1 | 68.44% | 87.09% |
| Macro F1 | 70.25% | ~87% |
| Class count range | 137–985 | 200–536 |
| Classes needing oversampling | 5 of 21 | ~1 of 21 (only 50/6050 profiles came from the top-up pass) |

## What changed, and why the number moved this much

The baseline's known issue: only 5 of 21 classes (the hardest KCSE-grade
gated ones) ever got programme-biased generation. Every other class's
interests/skills/strengths were drawn **uniformly at random from the full
pool, completely decoupled from which programme the profile would end up
labelled as** — so for those 16 classes, a synthetic profile's stated
aspiration (worth +4.0 in the scoring rule, and mapped 1:1 exclusively to a
single programme for most of them) was close to the only usable signal.

This experiment replaces that two-stage approach with one mechanism applied
to all 21 classes uniformly: pick a target programme first, then draw
interests/skills/strengths weighted toward that programme's own associated
tags (55–70% probability per pick, vs. a shared cross-cutting pool or the
full pool otherwise — the three-tier model from `programme_profiles.md`),
draw the aspiration from that programme's now-**non-exclusive** aspiration
list 75% of the time, and floor-enforce KCSE grades against the target's
real KUCCPS minimums. `assign_programme_label` — completely unchanged —
then decides the actual label, which can and does land on a different
programme when the random draws genuinely point there.

Every class now carries real, multi-attribute correlated signal instead of
noise, which is why accuracy moved this much without touching the labelling
rule, its weights, or adding any new engineered feature.

## Why this is (probably) not a new leak, not just a bigger number

An 18-point jump is exactly the kind of result that deserves suspicion
before it gets trusted, not celebration — the whole point of this staged
experiment was to be able to tell the difference. Two checks done before
accepting this number:

1. **No class is at or near 100% recall/precision.** Per-class recall ranges
   65% (Software Engineering, the lowest) to 97% (Journalism, Pharmacy).
   If a single feature had come to dominate a class's prediction the way
   aspiration did in the baseline, that class would sit near 100%, not 65%.
2. **Misclassifications land on the programmes the profile-redesign audit
   already flagged as genuinely confusable, not scattered randomly.**
   Software Engineering's 71 misclassifications: 51 (72%) go to
   Informatics & Computer Science — its documented closest neighbour — with
   1-5 stray counts elsewhere. BBIT's misclassifications concentrate on
   BCom (9) and ICS (8) — also its documented neighbours. See
   `confusion_matrix.json` for the full 21×21 table.

Both are the expected signature of a model that has learned real,
overlapping-but-distinguishable programme clusters — which is exactly what
Top-3 ranking is supposed to help with — rather than a new single-feature
shortcut replacing the old one.

## What this does NOT resolve

- **The 21-of-40 scope limitation is unchanged.** This experiment
  deliberately did not touch the catalogue size — see
  `programme_profiles.md`'s locked staging (profile quality first, catalogue
  expansion only after the generation method is validated).
- **The cluster-weighted-points feature idea is still untested** — it was
  explicitly deferred to its own A/B experiment, not bundled in here, so
  this result isn't confounded by it.
- **This is still a rule-derived synthetic label**, same honesty caveat as
  the baseline: 87% measures how well the model reproduces the (now richer,
  multi-signal) rule, not validated real-world placement accuracy.

## Files in this directory

- `programme_profiles.md` — the locked profile-design audit for all 40
  catalogue programmes (design artifact, predates this training run)
- `metrics.json` — accuracy, weighted F1, best hyperparameters, evaluation
  method, reference holdout numbers
- `classification_report.json` — full per-class precision/recall/F1/support
- `confusion_matrix.json` — full 21×21 confusion matrix with labels
- `class_distribution.json` — per-class profile counts, before/after the
  top-up pass
- `feature_config.json` — feature list, generation-change summary, the
  leakage check performed, classifier hyperparameters and search method
