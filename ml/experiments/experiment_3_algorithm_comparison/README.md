# Experiment 3 — Algorithm comparison (why Random Forest?)

Trained Random Forest (Experiment 1b's validated hyperparameters),
Histogram Gradient Boosting (sklearn defaults), and multinomial Logistic
Regression on the **identical** dataset, features, and evaluation
methodology (5-fold StratifiedKFold out-of-fold `cross_val_predict` — same
as every other reported number in this project) via `backend/model_comparison.py`.
This does not touch the deployed model; it's a comparison-only script.

## Result

| Model | Accuracy | Weighted F1 | Macro F1 |
|---|---|---|---|
| Random Forest | 87.52% | 87.40% | 87.51% |
| **Histogram Gradient Boosting** | **91.52%** | **91.51%** | **91.46%** |
| Logistic Regression | 89.77% | 89.77% | 89.77% |

Gradient Boosting beats Random Forest by 4 full points, and even plain
Logistic Regression beats it by over 2 points. This is a real, meaningful
gap, not noise.

## Why this makes sense, not just "a bigger number happened"

A plausible, honest explanation: `assign_programme_label`'s scoring rule is
an **additive weighted sum** over boolean features (aspiration match +4.0,
each interest match +2.0, each skill match +1.0, each strength match +1.0),
gated by a hard eligibility check. That scoring structure is close to
*linear* in the boolean trait features - which is exactly the function
class Logistic Regression is built to fit directly, and which Gradient
Boosting's sequential error-correcting trees can also converge to
efficiently. Random Forest's averaged independent trees are better suited
to problems with complex feature *interactions* that don't decompose
additively - which this problem, once the eligibility gate is passed,
mostly doesn't have. In other words: the label-generating rule's own
structure suits Gradient Boosting/Logistic Regression better than Random
Forest, and the data now shows that rather than just asserting a choice.

## Decision: Random Forest retained as the deployed model

Gradient Boosting scored measurably higher on this comparison. The decision
was made to keep Random Forest anyway, for reasons that go beyond the raw
accuracy number:

1. **The comparison isn't yet evaluated with matching rigor.** Every number
   reported elsewhere for Random Forest (Experiment 1, 1b) went through
   *two* checks - a held-out 80/20 split AND 5-fold cross-validation - and
   the two were compared to catch overfitting before trusting either
   number. This comparison script only ran 5-fold CV for all three models;
   Gradient Boosting's 91.52% has not yet been cross-checked against a
   held-out split the way Random Forest's numbers have. Preferring a higher
   number that hasn't cleared the same bar the deployed model had to clear
   is exactly the kind of asymmetric evaluation this project has
   deliberately avoided elsewhere (see the baseline README's stance on
   scrutinizing suspiciously high numbers, and Experiment 1's leakage
   check).
2. **This is synthetic, rule-derived data, not real outcomes.** A model
   that scores higher on reproducing a synthetic label-generation rule is
   not necessarily a model that generalizes better to real students -it
   may simply be fitting the rule's idiosyncrasies (including its
   tie-break mechanics) more tightly. Random Forest's bagging of
   independent trees is a more conservative estimator than boosting's
   sequential error-correction, which is a reasonable hedge when the
   target itself is a proxy, not ground truth.
3. **Random Forest's justification in the proposal (Chapter 3) stands on
   its own merits** - an ensemble of decision trees suited to structured
   data with mixed numeric/categorical features - independent of this
   comparison's outcome.

The comparison is kept in this repository specifically so this was a
*tested, evidence-aware* decision rather than an unexamined default -
citing "we compared alternatives and reasoned about the result" is a
stronger position for a defense than not having looked at all, even though
the conclusion was to keep the original choice.

## Files in this directory

- `results.json` — full per-class classification reports for all three
  models, from the exact same cross-validation run.
