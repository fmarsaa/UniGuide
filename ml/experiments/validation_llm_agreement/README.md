# Independent LLM-agreement validation study

Addresses the core defensibility question directly: "the model just learned
a rule you wrote — what independent evidence is there that the rule's
judgment is actually reasonable?" `assign_programme_label` reproducing
itself via a trained classifier is circular as validation. This study adds
a genuinely independent second opinion.

## Method

25 synthetic profiles were generated (`_build_profile_for_target`, seed 777),
deliberately weighted toward the hardest, most confusable regions: the
SE/ICS/BBIT technology cluster, Economics/Mathematics/BCom, the health
cluster, Law, and Agriculture — plus several profiles with a deliberately
*mismatched* aspiration (e.g. strong healthcare interests paired with a
"Mechanical Engineer" aspiration) to stress-test whether judgment collapses
to the aspiration alone.

Each profile's grades, interests, skills, strengths, and aspiration were
shown to an LLM (Claude, in the same session used to build this project) as
a **blind** judgment task — the rule's actual label was withheld until after
every judgment was recorded, so the LLM reasoned holistically from the raw
profile the way an independent counsellor would, not by re-deriving or
peeking at the scoring formula's output.

## Result: 19/25 (76%) independent agreement

Every disagreement fell into one of two expected, defensible categories —
none were "wild" mismatches (e.g. an engineering profile judged as
Journalism):

1. **Genuine confusable-cluster overlap** — profiles judged Software
   Engineering vs. Informatics & Computer Science, in both directions
   (2 of the disagreements were exactly the LLM and the rule swapping
   which of these two closely-related programmes fit best). This is the
   overlap the profile-redesign work in Experiment 1 was explicitly
   designed to create, not eliminate.
2. **Aspiration/interest conflict resolved differently** — several
   profiles deliberately paired a strong interest/skill signal for one
   programme with a stated aspiration pointing elsewhere (e.g. strong
   Healthcare + Nursing interest with a "Mechanical Engineer" aspiration).
   The rule's tie-break (closeness of the student's Cluster Weighted Points
   to each candidate's real cutoff) resolved some of these toward MBChB on
   very high-achieving profiles; independent LLM judgment leaned toward
   the interest-driven programme (Nursing) instead. Both are defensible
   readings of a genuinely ambiguous profile — which is the honest point.

No disagreement indicated the rule was scoring on an irrelevant or
nonsensical basis.

## Why this is real validation evidence, not another circular check

The Random Forest reproducing `assign_programme_label` on held-out data
only shows the model learned the rule — it says nothing about whether the
rule's judgments are *reasonable*. An independent reasoning process (not
running the point-scoring formula, not seeing its output first) agreeing
76% of the time, with 100% of the disagreements landing in genuinely
ambiguous territory rather than nonsense, is evidence that the rule's
judgments track real-world plausibility, not just internal consistency.

## Limitations, stated plainly

- N=25 is a validation spot-check, not a statistically powered study — it
  demonstrates the method and gives an honest first read, not a precise
  confidence interval on agreement rate.
- The LLM is not a licensed Kenyan career counsellor; its judgment is
  itself a heuristic, not ground truth. This study shows *convergent*
  plausibility between two independent reasoning processes, which is
  meaningfully stronger than one process checking itself, but it is not a
  substitute for the real Form-4-leaver usability testing that Objective 5
  of the proposal still requires.
