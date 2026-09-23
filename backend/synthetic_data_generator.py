"""
UniGuide - Synthetic Student Profile Dataset Generator
Author: Fatuma Omar Marsa (159056)
Supervised by: Deperias Webula Kerre
Strathmore University - School of Computing and Engineering Sciences

Implements the synthetic data generation pipeline described in Chapter 3:
- Realistic Kenyan form-four leaver KCSE grade distributions across the six
  subjects actually captured by the Flutter profile setup screen (Mathematics,
  English, Kiswahili, Biology, Chemistry, Physics).
- Interests, skills, strengths, and career aspirations drawn from the exact
  option lists presented to students in the mobile app, so the trained model's
  vocabulary matches what the app can ever submit.
- Programme labels are assigned using the multi-criteria rule described in the
  proposal: first gate on KUCCPS minimum subject requirements, then match the
  student's stated interests/skills/aspirations against each eligible
  programme, and finally break ties by closeness of the computed Cluster
  Weighted Points (CWP) to the programme's average cutoff. The LLM/random
  generator is only responsible for producing realistic profiles; this
  deterministic rule assigns the ground-truth label used to train the Random
  Forest classifier.
"""

import random
import re
from typing import Dict, List

import numpy as np
import pandas as pd

from kuccps import (
    COMPULSORY_SUBJECTS,
    FEATURE_COLUMN,
    FULL_OPTIONAL_SUBJECTS,
    ML_FEATURE_SUBJECTS,
    aggregate_points,
    cluster_weighted_points,
    extract_ml_feature_points,
    grade_to_points,
    meets_minimum_requirements,
    points_to_grade,
    raw_cluster_points,
)
from programmes_catalog import CATALOG_BY_TITLE, PROGRAMME_TITLES

INTERESTS_POOL = [
    "Healthcare & Clinical Medicine",
    "Patient Care & Nursing",
    "Pharmaceutical Sciences",
    "Software Development & Coding",
    "Artificial Intelligence & Machine Learning",
    "Data Analytics & Statistics",
    "Cybersecurity & Network Defense",
    "Civil Infrastructure & Structural Engineering",
    "Electrical & Electronic Systems",
    "Robotics, Mechatronics & Automation",
    "Corporate Law & Constitutional Advocacy",
    "Financial Markets & Investment Banking",
    "Actuarial Modeling & Risk Analysis",
    "Agribusiness & Food Sustainability",
    "Dental & Oral Health Care",
    "Veterinary & Animal Health Care",
    "Food Science & Nutrition",
    "Mechanical Systems & Manufacturing",
    "Architecture & Building Design",
    "Mathematical Research & Data Science",
    "Economic Policy & Market Analysis",
    "Journalism & Media Production",
    "Business Systems & Enterprise Technology",
]

SKILLS_POOL = [
    "Clinical Diagnostics & Health Care",
    "Python & Software Programming",
    "Mathematical & Quantitative Analysis",
    "Scientific Laboratory Research",
    "Problem Solving & Analytical Logic",
    "Critical Thinking & Persuasive Debate",
    "CAD Modeling & Spatial Engineering",
    "Financial Modeling & Accounting",
    "Attention to Detail",
    "Team Collaboration & Leadership",
    "Agricultural & Environmental Science",
    "News Writing & Media Research",
    "Cost Estimation & Construction Economics",
]

STRENGTHS_POOL = [
    "Perseverance & Discipline",
    "Logical & Analytical Reasoning",
    "Attention to Precision",
    "Empathy & Human Care",
    "Creative Problem Solving",
    "Leadership & Strategic Direction",
    "Team Collaboration",
]

ASPIRATIONS_POOL = [
    "Medical Doctor (Physician/Surgeon)",
    "Pharmacist",
    "Registered Nursing Specialist",
    "Software Engineer / AI Architect",
    "Civil Infrastructure Engineer",
    "Electrical Power Engineer",
    "Advocate of the High Court / Corporate Lawyer",
    "Actuary / Risk Strategist",
    "Financial Analyst / Investment Banker",
    "Cybersecurity Architect",
    "Dentist",
    "Veterinary Doctor",
    "Nutritionist / Dietitian",
    "Mechanical Engineer",
    "Architect",
    "Quantity Surveyor",
    "Mathematician / Data Analyst",
    "Economist / Policy Analyst",
    "Journalist / Media Professional",
    "Agricultural Officer / Agronomist",
    "Business Systems Analyst / IT Project Manager",
]


def _slug(label: str) -> str:
    """Short, stable identifier for a pool label, e.g. 'Healthcare & Clinical
    Medicine' -> 'healthcare_clinical_medicine'. Used to build ML column
    names - never shown to the user, so it just needs to be unique/stable."""
    slug = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    return slug


# Short, stable ML column name for every interest/skill/strength a student
# can select. Unlike the old "primary_interest" (only the 1st of 2-3 picks),
# every one of these is a genuine boolean feature - so the model can actually
# see everything assign_programme_label() used to decide the label, instead
# of an information-lossy single sample of it.
INTEREST_COLUMN: Dict[str, str] = {i: f"int_{_slug(i)}" for i in INTERESTS_POOL}
SKILL_COLUMN: Dict[str, str] = {s: f"skl_{_slug(s)}" for s in SKILLS_POOL}
STRENGTH_COLUMN: Dict[str, str] = {s: f"str_{_slug(s)}" for s in STRENGTHS_POOL}
TRAIT_FEATURE_COLUMNS: List[str] = (
    list(INTEREST_COLUMN.values()) + list(SKILL_COLUMN.values()) + list(STRENGTH_COLUMN.values())
)
# Reverse lookup used by main.py to build a human-readable SHAP explanation
# for a trait feature, e.g. "int_healthcare_clinical_medicine" -> ("Interests",
# "Interest", "Healthcare & Clinical Medicine").
TRAIT_COLUMN_INFO: Dict[str, tuple] = {}
for _label, _col in INTEREST_COLUMN.items():
    TRAIT_COLUMN_INFO[_col] = ("Interests", "Interest", _label)
for _label, _col in SKILL_COLUMN.items():
    TRAIT_COLUMN_INFO[_col] = ("Skills", "Skill", _label)
for _label, _col in STRENGTH_COLUMN.items():
    TRAIT_COLUMN_INFO[_col] = ("Strengths", "Strength", _label)


def build_trait_features(interests: List[str], skills: List[str], strengths: List[str]) -> Dict[str, int]:
    """One boolean (0/1) column per pool entry - shared by training (every
    sampled interest/skill/strength) and serving (main.py, from the real
    profile a student submitted) so the two can never disagree on schema."""
    row = {col: 0 for col in TRAIT_FEATURE_COLUMNS}
    for i in interests:
        if i in INTEREST_COLUMN:
            row[INTEREST_COLUMN[i]] = 1
    for s in skills:
        if s in SKILL_COLUMN:
            row[SKILL_COLUMN[s]] = 1
    for s in strengths:
        if s in STRENGTH_COLUMN:
            row[STRENGTH_COLUMN[s]] = 1
    return row

# Which optional KNEC subjects a student with a given aspiration realistically
# tends to have picked (used to generate coherent synthetic profiles - e.g. an
# engineering aspirant plausibly sat Physics, a law aspirant plausibly sat
# History). Not guaranteed - real students don't always follow the "expected"
# combination, so this only biases the random pick, it doesn't force it.
ASPIRATION_LIKELY_OPTIONALS: Dict[str, List[str]] = {
    "Medical Doctor (Physician/Surgeon)": [],
    "Pharmacist": [],
    "Registered Nursing Specialist": [],
    "Software Engineer / AI Architect": ["Physics", "Computer Studies"],
    "Civil Infrastructure Engineer": ["Physics", "Building Construction"],
    "Electrical Power Engineer": ["Physics", "Electricity"],
    "Advocate of the High Court / Corporate Lawyer": ["History & Government", "Christian Religious Education (CRE)"],
    "Actuary / Risk Strategist": ["Physics", "Business Studies"],
    "Financial Analyst / Investment Banker": ["Business Studies", "Geography"],
    "Cybersecurity Architect": ["Physics", "Computer Studies"],
    "Dentist": [],
    "Veterinary Doctor": ["Agriculture"],
    "Nutritionist / Dietitian": ["Home Science"],
    "Mechanical Engineer": ["Physics"],
    "Architect": ["Physics", "Art & Design"],
    "Quantity Surveyor": ["Physics", "Building Construction"],
    "Mathematician / Data Analyst": ["Physics", "Computer Studies"],
    "Economist / Policy Analyst": ["Business Studies", "Geography"],
    "Journalist / Media Professional": ["History & Government"],
    "Agricultural Officer / Agronomist": ["Agriculture", "Geography"],
    "Business Systems Analyst / IT Project Manager": ["Computer Studies", "Business Studies"],
}

_MBCHB = "Bachelor of Medicine and Bachelor of Surgery (MBChB)"
_BPHARM = "Bachelor of Pharmacy (BPharm)"
_NURSING = "Bachelor of Science in Nursing"
_ICS = "Bachelor of Science in Informatics and Computer Science"
_SE = "Bachelor of Science in Software Engineering"
_BBIT = "Bachelor of Science in Business Information Technology (BBIT)"
_EEE = "Bachelor of Science in Electrical and Electronic Engineering"
_CIVIL = "Bachelor of Science in Civil Engineering"
_LAW = "Bachelor of Laws (LLB)"
_ACTUARIAL = "Bachelor of Science in Actuarial Science"
_BCOM = "Bachelor of Commerce (BCom) - Finance & Accounting"
_DENTAL = "Bachelor of Dental Surgery (BDS)"
_VET = "Bachelor of Veterinary Medicine (BVM)"
_NUTRITION = "Bachelor of Science in Food, Nutrition and Dietetics"
_MECH = "Bachelor of Science in Mechanical Engineering"
_ARCH = "Bachelor of Architecture"
_QS = "Bachelor of Quantity Surveying"
_MATH = "Bachelor of Science in Mathematics"
_ECON = "Bachelor of Economics"
_JMC = "Bachelor of Arts in Journalism and Mass Communication"
_AGRI = "Bachelor of Science in Agriculture"

# Strong signal: a stated career aspiration votes heavily for its natural programme(s).
ASPIRATION_MAP: Dict[str, List[str]] = {
    "Medical Doctor (Physician/Surgeon)": [_MBCHB],
    "Pharmacist": [_BPHARM],
    "Registered Nursing Specialist": [_NURSING],
    "Software Engineer / AI Architect": [_ICS, _SE],
    "Civil Infrastructure Engineer": [_CIVIL],
    "Electrical Power Engineer": [_EEE],
    "Advocate of the High Court / Corporate Lawyer": [_LAW],
    "Actuary / Risk Strategist": [_ACTUARIAL],
    "Financial Analyst / Investment Banker": [_BCOM, _ACTUARIAL],
    "Cybersecurity Architect": [_ICS],
    "Dentist": [_DENTAL],
    "Veterinary Doctor": [_VET],
    "Nutritionist / Dietitian": [_NUTRITION],
    "Mechanical Engineer": [_MECH],
    "Architect": [_ARCH],
    "Quantity Surveyor": [_QS],
    "Mathematician / Data Analyst": [_MATH],
    "Economist / Policy Analyst": [_ECON],
    "Journalist / Media Professional": [_JMC],
    "Agricultural Officer / Agronomist": [_AGRI],
    "Business Systems Analyst / IT Project Manager": [_BBIT],
}

# Secondary signal: stated interests nudge scoring toward related programmes.
INTEREST_MAP: Dict[str, List[str]] = {
    "Healthcare & Clinical Medicine": [_MBCHB, _NURSING],
    "Patient Care & Nursing": [_NURSING, _MBCHB],
    "Pharmaceutical Sciences": [_BPHARM],
    "Software Development & Coding": [_SE, _ICS],
    "Artificial Intelligence & Machine Learning": [_ICS],
    "Data Analytics & Statistics": [_ICS, _ACTUARIAL, _MATH],
    "Cybersecurity & Network Defense": [_ICS],
    "Civil Infrastructure & Structural Engineering": [_CIVIL],
    "Electrical & Electronic Systems": [_EEE],
    "Robotics, Mechatronics & Automation": [_EEE, _ICS],
    "Corporate Law & Constitutional Advocacy": [_LAW],
    "Financial Markets & Investment Banking": [_BCOM, _ACTUARIAL],
    "Actuarial Modeling & Risk Analysis": [_ACTUARIAL],
    "Agribusiness & Food Sustainability": [_BCOM, _BBIT, _AGRI],
    "Dental & Oral Health Care": [_DENTAL],
    "Veterinary & Animal Health Care": [_VET],
    "Food Science & Nutrition": [_NUTRITION],
    "Mechanical Systems & Manufacturing": [_MECH],
    "Architecture & Building Design": [_ARCH, _QS],
    "Mathematical Research & Data Science": [_MATH],
    "Economic Policy & Market Analysis": [_ECON],
    "Journalism & Media Production": [_JMC],
    "Business Systems & Enterprise Technology": [_BBIT],
}

# Tertiary signal: a personal strength nudges scoring toward programmes where
# it's a genuinely relevant trait (e.g. precision for surgery/surveying).
STRENGTH_MAP: Dict[str, List[str]] = {
    "Perseverance & Discipline": [_MBCHB, _DENTAL, _VET, _LAW],
    "Logical & Analytical Reasoning": [_ICS, _SE, _ACTUARIAL, _MATH, _ECON],
    "Attention to Precision": [_BPHARM, _DENTAL, _QS, _ACTUARIAL],
    "Empathy & Human Care": [_NURSING, _MBCHB, _VET, _NUTRITION],
    "Creative Problem Solving": [_ARCH, _SE, _JMC],
    "Leadership & Strategic Direction": [_BCOM, _ECON, _LAW],
    "Team Collaboration": [_CIVIL, _EEE, _MECH, _BBIT],
}

# Fallback ordering when no eligible programme scores above zero (lowest admission bars first).
FALLBACK_ORDER = [_AGRI, _BBIT, _BCOM, _NURSING, _ICS, _SE]

# Scoped to the 21 programmes the classifier is currently trained on. The
# catalog has grown to 40 (programmes_catalog.py), but the newest 19 don't
# have their own aspiration/interest vocabulary yet (no ASPIRATION_MAP/
# INTEREST_MAP entries) - see Chapter 5.3/Future Work's stated 21-of-40
# limitation. Without this scoping, meets_minimum_requirements() would let
# eligibility+cutoff-tiebreak silently leak those 19 in as unintended
# "bycatch" training labels with no real thematic signal behind them.
# Extending to all 40 later just means widening this list once their
# vocabulary is built, not restructuring the labeling rule itself.
TRAINED_PROGRAMME_TITLES: List[str] = [
    _MBCHB, _BPHARM, _NURSING, _ICS, _SE, _BBIT, _EEE, _CIVIL, _LAW,
    _ACTUARIAL, _BCOM, _DENTAL, _VET, _NUTRITION, _MECH, _ARCH, _QS,
    _MATH, _ECON, _JMC, _AGRI,
]
assert len(TRAINED_PROGRAMME_TITLES) == 21
assert all(t in PROGRAMME_TITLES for t in TRAINED_PROGRAMME_TITLES)

assert set(ASPIRATION_MAP) == set(ASPIRATIONS_POOL)
assert set(INTEREST_MAP) == set(INTERESTS_POOL)
assert set(STRENGTH_MAP) == set(STRENGTHS_POOL)
assert set(ASPIRATION_LIKELY_OPTIONALS) == set(ASPIRATIONS_POOL)
assert all(title in PROGRAMME_TITLES for titles in ASPIRATION_MAP.values() for title in titles)
assert all(title in PROGRAMME_TITLES for titles in INTEREST_MAP.values() for title in titles)
assert all(title in PROGRAMME_TITLES for titles in STRENGTH_MAP.values() for title in titles)
assert all(s in FULL_OPTIONAL_SUBJECTS for subs in ASPIRATION_LIKELY_OPTIONALS.values() for s in subs)


def _choose_optional_subjects(aspiration: str, n_optional: int) -> List[str]:
    """Picks n_optional subjects from the full KNEC list, biased toward ones
    that plausibly fit the student's stated aspiration."""
    boosted = list(ASPIRATION_LIKELY_OPTIONALS.get(aspiration, []))
    random.shuffle(boosted)
    chosen: List[str] = [s for s in boosted if random.random() < 0.75][:n_optional]

    remaining_pool = [s for s in FULL_OPTIONAL_SUBJECTS if s not in chosen]
    random.shuffle(remaining_pool)
    while len(chosen) < n_optional and remaining_pool:
        chosen.append(remaining_pool.pop())

    return chosen[:n_optional]


def _score_programme(title: str, interests: List[str], skills: List[str], strengths: List[str],
                      aspiration: str) -> float:
    programme = CATALOG_BY_TITLE[title]
    score = 0.0

    if title in ASPIRATION_MAP.get(aspiration, []):
        score += 4.0

    for interest in interests:
        if title in INTEREST_MAP.get(interest, []):
            score += 2.0

    haystack = " ".join(programme["requiredSkills"] + [programme["description"]]).lower()
    for skill in skills:
        # Match on the first meaningful token of the skill label (e.g. "Python" from
        # "Python & Software Programming") so it lines up with catalog skill phrasing.
        token = skill.split(" & ")[0].split(" ")[0].lower()
        if token and token in haystack:
            score += 1.0

    for strength in strengths:
        if title in STRENGTH_MAP.get(strength, []):
            score += 1.0

    return score


def assign_programme_label(grades: Dict[str, str], mean_grade: str, interests: List[str],
                            skills: List[str], strengths: List[str], aspiration: str) -> str:
    agg = aggregate_points(grades, mean_grade)

    eligible = [
        title for title in TRAINED_PROGRAMME_TITLES
        if meets_minimum_requirements(grades, CATALOG_BY_TITLE[title]["minimumSubjectRequirements"], mean_grade)
    ]
    if not eligible:
        eligible = FALLBACK_ORDER

    scored = [(title, _score_programme(title, interests, skills, strengths, aspiration)) for title in eligible]
    best_score = max(s for _, s in scored)

    if best_score <= 0:
        # No thematic match among eligible programmes: fall back to the closest
        # academic fit (smallest gap between the student's CWP and the cutoff).
        candidates = eligible
    else:
        candidates = [title for title, s in scored if s == best_score]

    def cutoff_gap(title: str) -> float:
        programme = CATALOG_BY_TITLE[title]
        raw = raw_cluster_points(grades, programme["clusterSubjects"], mean_grade)
        cwp = cluster_weighted_points(raw, agg)
        return abs(cwp - programme["averageCutoff"])

    return min(candidates, key=cutoff_gap)


_JITTER_SPREADS = {
    "Mathematics": [-1, 0, 1, 2],
    "English": [-1, 0, 1],
    "Kiswahili": [-1, 0, 1],
    "Biology": [-2, -1, 0, 1],
    "Chemistry": [-2, -1, 0, 1],
}
_DEFAULT_OPTIONAL_SPREAD = [-2, -1, 0, 1]


def _build_profile(profile_id: int) -> dict:
    mean_points = int(np.clip(np.random.normal(8.5, 2.0), 4, 12))
    mean_grade = points_to_grade(mean_points)

    def jitter(spread):
        return int(np.clip(mean_points + np.random.choice(spread), 1, 12))

    interests = random.sample(INTERESTS_POOL, k=random.randint(2, 3))
    skills = random.sample(SKILLS_POOL, k=random.randint(2, 3))
    strengths = random.sample(STRENGTHS_POOL, k=random.randint(2, 3))
    aspiration = random.choice(ASPIRATIONS_POOL)

    # Real KCSE candidates sit 7-9 subjects: the 5 compulsory ones plus 2-4
    # optional ones, chosen with a bias toward whatever plausibly fits the
    # student's stated aspiration (see _choose_optional_subjects).
    total_subjects = random.choice([7, 7, 8, 8, 9])
    n_optional = total_subjects - len(COMPULSORY_SUBJECTS)
    optional_subjects = _choose_optional_subjects(aspiration, n_optional)

    grades: Dict[str, str] = {
        subject: points_to_grade(jitter(_JITTER_SPREADS[subject]))
        for subject in COMPULSORY_SUBJECTS
    }
    for subject in optional_subjects:
        grades[subject] = points_to_grade(jitter(_DEFAULT_OPTIONAL_SPREAD))

    label = assign_programme_label(grades, mean_grade, interests, skills, strengths, aspiration)

    feature_points = extract_ml_feature_points(grades, mean_grade)

    record = {"student_id": f"std_{profile_id:04d}"}
    for subject in ML_FEATURE_SUBJECTS:
        record[FEATURE_COLUMN[subject]] = feature_points[subject]
    record["mean_points"] = mean_points
    record.update(build_trait_features(interests, skills, strengths))
    record["aspiration"] = aspiration
    record["programme_label"] = label
    return record


def create_synthetic_dataset(n_samples: int = 1500, seed: int = 42) -> pd.DataFrame:
    # Seeded so the training pipeline is reproducible run-to-run - important
    # for a thesis where reported accuracy/F1 numbers should be reproducible.
    random.seed(seed)
    np.random.seed(seed)
    records = [_build_profile(i) for i in range(1, n_samples + 1)]
    df = pd.DataFrame(records)
    return oversample_thin_classes(df)


# ---------------------------------------------------------------------------
# Targeted oversampling for classes too rare under pure random generation to
# evaluate reliably (see Chapter 5.3's stated limitation). Pure random
# profile generation makes B/B+-gated programmes (MBChB, BPharm, BDS, Civil,
# EEE) naturally scarce, since few randomly-generated profiles clear all of
# a strict programme's subject-grade minimums at once. Below a certain count,
# that class's held-out test slice becomes too small (single digits) for its
# precision/recall/F1 to mean anything - one misclassification can swing the
# metric by 10+ points.
#
# This does NOT duplicate existing rows (which would just repeat identical
# evidence) and does NOT hand-assign labels. It generates genuinely new
# profiles - their own independently randomly-varied grades, interests,
# skills, strengths - but biases generation toward a target programme's
# eligibility band and matching career aspiration, then lets the exact same
# assign_programme_label() rule as every other profile decide the label. A
# biased-generation profile can still land on a different class if its
# random draws point elsewhere; nothing here forces the outcome.
#
# IMPORTANT for Chapter 5.3: the resulting counts for these five classes do
# NOT represent naturally-occurring KUCCPS eligibility frequency the way the
# rest of the dataset does - they're deliberately supplemented for reliable
# evaluation. State that explicitly rather than presenting them at face value.
# ---------------------------------------------------------------------------

_MBCHB_T = "Bachelor of Medicine and Bachelor of Surgery (MBChB)"
_BPHARM_T = "Bachelor of Pharmacy (BPharm)"
_DENTAL_T = "Bachelor of Dental Surgery (BDS)"
_CIVIL_T = "Bachelor of Science in Civil Engineering"
_EEE_T = "Bachelor of Science in Electrical and Electronic Engineering"

# Each target's anchor aspiration (from ASPIRATION_MAP) - generation biases
# strongly toward this so the +4.0 aspiration-match score usually dominates
# scoring, without forcing the label.
_TARGETED_OVERSAMPLE_ANCHORS: Dict[str, str] = {
    _MBCHB_T: "Medical Doctor (Physician/Surgeon)",
    _BPHARM_T: "Pharmacist",
    _DENTAL_T: "Dentist",
    _CIVIL_T: "Civil Infrastructure Engineer",
    _EEE_T: "Electrical Power Engineer",
}

THIN_CLASS_FLOOR = 175


def _build_targeted_profile(profile_id: int, target_title: str) -> dict:
    """Like _build_profile, but biases generation toward target_title's
    eligibility band and matching aspiration. See module-level comment
    above for why this exists and what it does and doesn't do."""
    programme = CATALOG_BY_TITLE[target_title]
    min_reqs = programme["minimumSubjectRequirements"]

    # Skewed higher than the general population's Normal(8.5, 2.0) so a
    # profile plausibly clears a B/B+ gate, while keeping real variance
    # rather than clustering everyone at the exact same grade.
    mean_points = int(np.clip(np.random.normal(10.0, 1.3), 6, 12))
    mean_grade = points_to_grade(mean_points)

    def jitter(spread):
        return int(np.clip(mean_points + np.random.choice(spread), 1, 12))

    anchor_aspiration = _TARGETED_OVERSAMPLE_ANCHORS[target_title]
    aspiration = anchor_aspiration if random.random() < 0.85 else random.choice(ASPIRATIONS_POOL)

    matching_interests = [i for i, titles in INTEREST_MAP.items() if target_title in titles]
    interests = random.sample(INTERESTS_POOL, k=random.randint(2, 3))
    if matching_interests and random.random() < 0.7:
        interests[0] = random.choice(matching_interests)
    skills = random.sample(SKILLS_POOL, k=random.randint(2, 3))
    strengths = random.sample(STRENGTHS_POOL, k=random.randint(2, 3))

    total_subjects = random.choice([7, 7, 8, 8, 9])
    n_optional = total_subjects - len(COMPULSORY_SUBJECTS)
    optional_subjects = _choose_optional_subjects(aspiration, n_optional)

    # Guarantee any gated subject that isn't compulsory was actually sat,
    # so eligibility isn't left to a mean-grade fallback guess.
    required_optionals = [s for s in min_reqs if s not in COMPULSORY_SUBJECTS and s in FULL_OPTIONAL_SUBJECTS]
    for subject in required_optionals:
        if subject not in optional_subjects:
            if optional_subjects:
                optional_subjects[-1] = subject
            else:
                optional_subjects = [subject]

    def biased_points(subject: str, spread: List[int]) -> int:
        points = jitter(spread)
        if subject in min_reqs:
            floor = grade_to_points(min_reqs[subject])
            points = max(points, floor + int(np.random.choice([0, 0, 1, 2])))
        return points

    grades: Dict[str, str] = {
        subject: points_to_grade(biased_points(subject, _JITTER_SPREADS[subject]))
        for subject in COMPULSORY_SUBJECTS
    }
    for subject in optional_subjects:
        grades[subject] = points_to_grade(biased_points(subject, _DEFAULT_OPTIONAL_SPREAD))

    label = assign_programme_label(grades, mean_grade, interests, skills, strengths, aspiration)
    feature_points = extract_ml_feature_points(grades, mean_grade)

    record = {"student_id": f"std_t{profile_id:04d}"}
    for subject in ML_FEATURE_SUBJECTS:
        record[FEATURE_COLUMN[subject]] = feature_points[subject]
    record["mean_points"] = mean_points
    record.update(build_trait_features(interests, skills, strengths))
    record["aspiration"] = aspiration
    record["programme_label"] = label
    return record


def oversample_thin_classes(df: pd.DataFrame, floor: int = THIN_CLASS_FLOOR, seed: int = 4200) -> pd.DataFrame:
    """Appends targeted-generation profiles until each class in
    _TARGETED_OVERSAMPLE_ANCHORS reaches `floor`. Uses its own seed so the
    supplementary generation is reproducible independent of how many draws
    the main pool consumed. See module-level comment above."""
    rng_state = random.getstate()
    np_state = np.random.get_state()
    random.seed(seed)
    np.random.seed(seed)

    counts = df["programme_label"].value_counts().to_dict()
    extra_records = []
    next_id = 1
    for title in _TARGETED_OVERSAMPLE_ANCHORS:
        current = counts.get(title, 0)
        needed = max(0, floor - current)
        attempts = 0
        max_attempts = needed * 20 + 200  # generous ceiling - can't loop forever
        while counts.get(title, 0) < floor and attempts < max_attempts:
            record = _build_targeted_profile(next_id, title)
            next_id += 1
            attempts += 1
            extra_records.append(record)
            counts[record["programme_label"]] = counts.get(record["programme_label"], 0) + 1

    random.setstate(rng_state)
    np.random.set_state(np_state)

    if not extra_records:
        return df
    extra_df = pd.DataFrame(extra_records)
    return pd.concat([df, extra_df], ignore_index=True)


if __name__ == "__main__":
    df = create_synthetic_dataset(1500)
    df.to_csv("synthetic_student_profiles.csv", index=False)
    print(f"Generated {len(df)} synthetic student profiles. Sample distribution:")
    print(df["programme_label"].value_counts())
