"""
UniGuide - Synthetic Student Profile Dataset Generator
Author: Fatuma Omar Marsa (159056)
Supervised by: Deperias Webula Kerre
Strathmore University - School of Computing and Engineering Sciences

Implements the synthetic data generation pipeline described in Chapter 3:
- Realistic Kenyan form-four leaver KCSE grade distributions across the six
  subjects actually captured by the Flutter profile setup screen (Mathematics,
  English, Kiswahili and Chemistry are compulsory; Biology, Physics and the
  rest are optional subjects a student may or may not have sat).
- Interests, strengths, and career aspirations drawn from the exact
  option lists presented to students in the mobile app, so the trained model's
  vocabulary matches what the app can ever submit.
- Programme labels are assigned using the multi-criteria rule described in the
  proposal: first gate on KUCCPS minimum subject requirements and on the
  student's Cluster Weighted Points (CWP) reaching the programme's average
  cutoff, then match the student's stated interests/strengths/aspirations
  against each reachable programme, and finally break ties by the smallest
  margin of CWP above that cutoff. Profiles that reach no programme's cutoff
  are discarded. The seeded,
  programme-biased random generator in this module (no LLM is involved in
  generating the training data) is only responsible for producing profiles;
  this deterministic rule assigns the ground-truth label used to train the
  Random Forest classifier.
"""

import os
for v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(v, "1")

import random
import re
from collections import Counter
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from kuccps import (
    COMPULSORY_SUBJECTS,
    FEATURE_COLUMN,
    FULL_OPTIONAL_SUBJECTS,
    GRADE_POINTS,
    ML_FEATURE_SUBJECTS,
    UNDECIDED_ASPIRATION,
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
    # --- 53-class catalogue expansion additions ---
    "Public Health & Epidemiology",
    "Clinical Laboratory & Diagnostic Sciences",
    "Physical Rehabilitation & Therapy",
    "Environmental Conservation & Sustainability",
    "Chemical & Materials Sciences",
    "Physics & Applied Sciences Research",
    "Food Production & Agro-Processing",
    "Social Research & Community Development",
    "Counseling & Mental Health Support",
    "Teaching & Curriculum Development",
    "Tourism & Destination Management",
    "Hospitality & Guest Services",
    "Human Resource & Organizational Development",
    "International Trade & Global Business",
    "Procurement & Supply Chain Management",
    "Urban Planning & Land Use",
    "Geospatial Mapping & Remote Sensing",
    "Political & Governance Studies",
    "Criminal Justice & Security Studies",
    "General Business Administration & Strategy",
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
    # --- Experiment 1 (profile redesign) additions ---
    # Deliberately non-exclusive, cluster-level aspirations. Every one of the
    # 21 trained programmes above had, at most, one dedicated aspiration
    # option pointing to it - for 10 of them that single option mapped to
    # them *exclusively*, which let a synthetic profile's stated aspiration
    # alone (worth +4.0 in _score_programme, vs +2.0/+1.0/+1.0 for the other
    # signals) dominate the label almost like a lookup table. These eight
    # options each map to several thematically-related programmes (see the
    # ASPIRATION_MAP additions below), so every programme now has at least
    # one genuinely shared aspiration alongside its specific one, and stating
    # it never single-handedly gives away which specific programme within
    # the cluster is the right fit - the other signals still have to do that
    # work. See ml/experiments/experiment_1_profile_redesign/programme_profiles.md.
    "Healthcare Professional (General)",
    "Technology Professional (General)",
    "Engineering Professional (General)",
    "Finance & Business Professional (General)",
    "Built Environment Professional (General)",
    "Quantitative Analyst / Researcher (General)",
    "Public Policy & Communications Professional (General)",
    "Agricultural & Environmental Professional (General)",
    # --- 53-class catalogue expansion additions ---
    # One specific aspiration per newly-trained programme (below) plus 4 new
    # shared cluster aspirations, following exactly the same non-exclusive
    # pattern as the Experiment 1 additions above - every one of the 32
    # newly-trained programmes gets its own specific option AND placement in
    # a shared cluster (either one of these 4 new ones or an existing one
    # extended in ASPIRATION_MAP below), so none of them repeats the original
    # single-exclusive-aspiration leakage bug.
    "Industrial Chemist / Process Chemist",
    "Microbiologist",
    "Food Scientist / Food Technologist",
    "Statistician / Data Analyst",
    "Science Teacher / Educator",
    "Arts Teacher / Educator",
    "Public Health Officer",
    "Sociologist / Social Researcher",
    "Social Worker",
    "Counseling Psychologist",
    "Business Manager / Administrator",
    "Tourism Officer / Destination Manager",
    "Hotel & Hospitality Manager",
    "Real Estate / Property Manager",
    "Chemical Process Engineer",
    "Human Resource Manager",
    "International Trade Manager",
    "Urban & Regional Planner",
    "Geospatial Analyst / Land Surveyor",
    "Medical Laboratory Technologist",
    "Physiotherapist",
    "Community Health Officer",
    "Data Scientist",
    "Biochemist",
    "Physicist / Research Scientist",
    "Chemist / Analytical Scientist",
    "Procurement & Supply Chain Manager",
    "Environmental Scientist / Conservationist",
    "Forester / Conservation Officer",
    "Biomedical Engineer",
    "Political Analyst / Public Administrator",
    "Criminologist / Security Analyst",
    "Educator / Teaching Professional (General)",
    "Social & Community Services Professional (General)",
    "Applied & Physical Sciences Researcher (General)",
    "Tourism & Hospitality Professional (General)",
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
STRENGTH_COLUMN: Dict[str, str] = {s: f"str_{_slug(s)}" for s in STRENGTHS_POOL}
TRAIT_FEATURE_COLUMNS: List[str] = list(INTEREST_COLUMN.values()) + list(STRENGTH_COLUMN.values())

TRAIT_COLUMN_INFO: Dict[str, tuple] = {}
for _label, _col in INTEREST_COLUMN.items():
    TRAIT_COLUMN_INFO[_col] = ("Interests", "Interest", _label)
for _label, _col in STRENGTH_COLUMN.items():
    TRAIT_COLUMN_INFO[_col] = ("Strengths", "Strength", _label)


def build_trait_features(interests: List[str], strengths: List[str]) -> Dict[str, int]:
    row = {col: 0 for col in TRAIT_FEATURE_COLUMNS}
    for i in interests:
        if i in INTEREST_COLUMN:
            row[INTEREST_COLUMN[i]] = 1
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
    "Medical Doctor (Physician/Surgeon)": ["Biology"],
    "Pharmacist": ["Biology"],
    "Registered Nursing Specialist": ["Biology"],
    "Software Engineer / AI Architect": ["Physics", "Computer Studies"],
    "Civil Infrastructure Engineer": ["Physics", "Building Construction"],
    "Electrical Power Engineer": ["Physics", "Electricity"],
    "Advocate of the High Court / Corporate Lawyer": ["History & Government", "Christian Religious Education (CRE)"],
    "Actuary / Risk Strategist": ["Physics", "Business Studies"],
    "Financial Analyst / Investment Banker": ["Business Studies", "Geography"],
    "Cybersecurity Architect": ["Physics", "Computer Studies"],
    "Dentist": ["Biology"],
    "Veterinary Doctor": ["Biology", "Agriculture"],
    "Nutritionist / Dietitian": ["Biology", "Home Science"],
    "Mechanical Engineer": ["Physics"],
    "Architect": ["Physics", "Art & Design"],
    "Quantity Surveyor": ["Physics", "Building Construction"],
    "Mathematician / Data Analyst": ["Physics", "Computer Studies"],
    "Economist / Policy Analyst": ["Business Studies", "Geography"],
    "Journalist / Media Professional": ["History & Government"],
    "Agricultural Officer / Agronomist": ["Agriculture", "Biology", "Geography"],
    "Business Systems Analyst / IT Project Manager": ["Computer Studies", "Business Studies"],
    "Healthcare Professional (General)": ["Biology"],
    "Technology Professional (General)": ["Computer Studies"],
    "Engineering Professional (General)": ["Physics"],
    "Finance & Business Professional (General)": ["Business Studies"],
    "Built Environment Professional (General)": ["Physics", "Building Construction"],
    "Quantitative Analyst / Researcher (General)": ["Physics"],
    "Public Policy & Communications Professional (General)": ["History & Government"],
    "Agricultural & Environmental Professional (General)": ["Agriculture", "Biology"],
    "Industrial Chemist / Process Chemist": ["Physics"],
    "Microbiologist": ["Biology", "Agriculture"],
    "Food Scientist / Food Technologist": ["Biology", "Agriculture", "Home Science"],
    "Statistician / Data Analyst": ["Physics", "Computer Studies"],
    "Science Teacher / Educator": ["Physics", "Biology"],
    "Arts Teacher / Educator": ["History & Government"],
    "Public Health Officer": ["Biology", "Agriculture"],
    "Sociologist / Social Researcher": ["History & Government", "Geography"],
    "Social Worker": ["History & Government"],
    "Counseling Psychologist": ["Christian Religious Education (CRE)"],
    "Business Manager / Administrator": ["Business Studies"],
    "Tourism Officer / Destination Manager": ["Geography", "Business Studies"],
    "Hotel & Hospitality Manager": ["Business Studies", "Home Science"],
    "Real Estate / Property Manager": ["Business Studies", "Geography"],
    "Chemical Process Engineer": ["Physics"],
    "Human Resource Manager": ["Business Studies"],
    "International Trade Manager": ["Business Studies", "Geography"],
    "Urban & Regional Planner": ["Geography", "Physics"],
    "Geospatial Analyst / Land Surveyor": ["Geography", "Physics"],
    "Medical Laboratory Technologist": ["Biology"],
    "Physiotherapist": ["Biology"],
    "Community Health Officer": ["Biology", "Agriculture"],
    "Data Scientist": ["Computer Studies", "Physics"],
    "Biochemist": ["Biology"],
    "Physicist / Research Scientist": ["Physics"],
    "Chemist / Analytical Scientist": ["Physics"],
    "Procurement & Supply Chain Manager": ["Business Studies"],
    "Environmental Scientist / Conservationist": ["Agriculture", "Biology", "Geography"],
    "Forester / Conservation Officer": ["Agriculture", "Biology", "Geography"],
    "Biomedical Engineer": ["Physics", "Biology"],
    "Political Analyst / Public Administrator": ["History & Government"],
    "Criminologist / Security Analyst": ["History & Government"],
    "Educator / Teaching Professional (General)": [],
    "Social & Community Services Professional (General)": [],
    "Applied & Physical Sciences Researcher (General)": ["Physics"],
    "Tourism & Hospitality Professional (General)": ["Business Studies"],
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

# --- 53-class catalogue expansion additions ---
_INDCHEM = "Bachelor of Science in Industrial Chemistry"
_MICRO = "Bachelor of Science in Microbiology"
_FOODSCI = "Bachelor of Science in Food Science and Technology"
_STATS = "Bachelor of Science in Statistics"
_EDUSCI = "Bachelor of Education (Science)"
_EDUARTS = "Bachelor of Education (Arts)"
_PUBHEALTH = "Bachelor of Science in Public Health"
_SOCIOLOGY = "Bachelor of Arts in Sociology"
_SOCIALWORK = "Bachelor of Social Work"
_COUNSELING = "Bachelor of Arts in Counseling Psychology"
_BUSMGMT = "Bachelor of Business Management"
_TOURISM = "Bachelor of Tourism Management"
_HOSPITALITY = "Bachelor of Science in Hospitality Management"
_REALESTATE = "Bachelor of Science in Real Estate Management"
_CHEMENG = "Bachelor of Engineering in Chemical Engineering"
_HRM = "Bachelor of Science in Human Resource Management"
_INTLBUS = "Bachelor of Science in International Business Management"
_URP = "Bachelor of Urban and Regional Planning"
_GEOMATICS = "Bachelor of Science in Geomatics and Geospatial Information Systems"
_MEDLAB = "Bachelor of Science in Medical Laboratory Sciences"
_PHYSIO = "Bachelor of Science in Physiotherapy"
_COMMHEALTH = "Bachelor of Science in Community Health and Development"
_DATASCI = "Bachelor of Science in Data Science and Analytics"
_BIOCHEM = "Bachelor of Science in Biochemistry"
_PHYSICS = "Bachelor of Science in Physics"
_CHEMISTRY = "Bachelor of Science in Chemistry"
_PROCUREMENT = "Bachelor of Procurement and Logistics Management"
_ENVSCI = "Bachelor of Science in Environmental Science"
_FORESTRY = "Bachelor of Science in Forestry"
_BIOMEDENG = "Bachelor of Science in Biomedical Engineering"
_POLSCI = "Bachelor of Arts in Political Science and Public Administration"
_CRIMINOLOGY = "Bachelor of Arts in Criminology and Security Studies"

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
    # Cluster-level, deliberately shared aspirations (see ASPIRATIONS_POOL
    # comment above) - each maps to several programmes so no single trained
    # programme is left with only one exclusive aspiration option.
    "Healthcare Professional (General)": [
        _MBCHB, _BPHARM, _NURSING, _DENTAL, _VET, _NUTRITION,
        _PUBHEALTH, _COMMHEALTH, _MEDLAB, _PHYSIO, _BIOMEDENG, _BIOCHEM,
    ],
    "Technology Professional (General)": [_ICS, _SE, _BBIT, _DATASCI],
    "Engineering Professional (General)": [_EEE, _CIVIL, _MECH, _CHEMENG, _BIOMEDENG, _PHYSICS],
    "Finance & Business Professional (General)": [
        _BCOM, _ACTUARIAL, _BBIT, _BUSMGMT, _HRM, _INTLBUS, _PROCUREMENT,
    ],
    "Built Environment Professional (General)": [_ARCH, _QS, _CIVIL, _REALESTATE, _URP, _GEOMATICS],
    "Quantitative Analyst / Researcher (General)": [_MATH, _ACTUARIAL, _ECON, _STATS, _DATASCI],
    "Public Policy & Communications Professional (General)": [_LAW, _ECON, _JMC, _POLSCI],
    "Agricultural & Environmental Professional (General)": [_AGRI, _NUTRITION, _FOODSCI, _ENVSCI, _FORESTRY],
    # --- 53-class catalogue expansion: new shared clusters ---
    "Educator / Teaching Professional (General)": [_EDUSCI, _EDUARTS],
    "Social & Community Services Professional (General)": [
        _SOCIOLOGY, _SOCIALWORK, _COUNSELING, _CRIMINOLOGY, _COMMHEALTH,
    ],
    "Applied & Physical Sciences Researcher (General)": [
        _INDCHEM, _MICRO, _BIOCHEM, _PHYSICS, _CHEMISTRY, _CHEMENG, _MEDLAB,
    ],
    "Tourism & Hospitality Professional (General)": [_TOURISM, _HOSPITALITY],
    # --- 53-class catalogue expansion: new specific (per-programme) aspirations ---
    "Industrial Chemist / Process Chemist": [_INDCHEM],
    "Microbiologist": [_MICRO],
    "Food Scientist / Food Technologist": [_FOODSCI],
    "Statistician / Data Analyst": [_STATS],
    "Science Teacher / Educator": [_EDUSCI],
    "Arts Teacher / Educator": [_EDUARTS],
    "Public Health Officer": [_PUBHEALTH],
    "Sociologist / Social Researcher": [_SOCIOLOGY],
    "Social Worker": [_SOCIALWORK],
    "Counseling Psychologist": [_COUNSELING],
    "Business Manager / Administrator": [_BUSMGMT],
    "Tourism Officer / Destination Manager": [_TOURISM],
    "Hotel & Hospitality Manager": [_HOSPITALITY],
    "Real Estate / Property Manager": [_REALESTATE],
    "Chemical Process Engineer": [_CHEMENG],
    "Human Resource Manager": [_HRM],
    "International Trade Manager": [_INTLBUS],
    "Urban & Regional Planner": [_URP],
    "Geospatial Analyst / Land Surveyor": [_GEOMATICS],
    "Medical Laboratory Technologist": [_MEDLAB],
    "Physiotherapist": [_PHYSIO],
    "Community Health Officer": [_COMMHEALTH],
    "Data Scientist": [_DATASCI],
    "Biochemist": [_BIOCHEM],
    "Physicist / Research Scientist": [_PHYSICS],
    "Chemist / Analytical Scientist": [_CHEMISTRY],
    "Procurement & Supply Chain Manager": [_PROCUREMENT],
    "Environmental Scientist / Conservationist": [_ENVSCI],
    "Forester / Conservation Officer": [_FORESTRY],
    "Biomedical Engineer": [_BIOMEDENG],
    "Political Analyst / Public Administrator": [_POLSCI],
    "Criminologist / Security Analyst": [_CRIMINOLOGY],
}

# Secondary signal: stated interests nudge scoring toward related programmes.
INTEREST_MAP: Dict[str, List[str]] = {
    "Healthcare & Clinical Medicine": [_MBCHB, _NURSING],
    "Patient Care & Nursing": [_NURSING, _MBCHB],
    "Pharmaceutical Sciences": [_BPHARM],
    "Software Development & Coding": [_SE, _ICS],
    "Artificial Intelligence & Machine Learning": [_ICS],
    "Data Analytics & Statistics": [_ICS, _ACTUARIAL, _MATH, _STATS, _DATASCI],
    "Cybersecurity & Network Defense": [_ICS],
    "Civil Infrastructure & Structural Engineering": [_CIVIL],
    "Electrical & Electronic Systems": [_EEE],
    "Robotics, Mechatronics & Automation": [_EEE, _ICS],
    "Corporate Law & Constitutional Advocacy": [_LAW],
    "Financial Markets & Investment Banking": [_BCOM, _ACTUARIAL],
    "Actuarial Modeling & Risk Analysis": [_ACTUARIAL],
    "Agribusiness & Food Sustainability": [_BCOM, _BBIT, _AGRI, _FOODSCI, _ENVSCI, _FORESTRY],
    "Dental & Oral Health Care": [_DENTAL],
    "Veterinary & Animal Health Care": [_VET],
    "Food Science & Nutrition": [_NUTRITION],
    "Mechanical Systems & Manufacturing": [_MECH],
    "Architecture & Building Design": [_ARCH, _QS],
    "Mathematical Research & Data Science": [_MATH, _STATS, _DATASCI],
    "Economic Policy & Market Analysis": [_ECON],
    "Journalism & Media Production": [_JMC],
    "Business Systems & Enterprise Technology": [_BBIT],
    # --- 53-class catalogue expansion additions ---
    "Public Health & Epidemiology": [_PUBHEALTH, _COMMHEALTH],
    "Clinical Laboratory & Diagnostic Sciences": [_MEDLAB, _MICRO, _BIOCHEM],
    "Physical Rehabilitation & Therapy": [_PHYSIO],
    "Environmental Conservation & Sustainability": [_ENVSCI, _FORESTRY],
    "Chemical & Materials Sciences": [_CHEMISTRY, _INDCHEM, _CHEMENG],
    "Physics & Applied Sciences Research": [_PHYSICS, _BIOMEDENG],
    "Food Production & Agro-Processing": [_FOODSCI],
    "Social Research & Community Development": [_SOCIOLOGY, _SOCIALWORK, _COMMHEALTH],
    "Counseling & Mental Health Support": [_COUNSELING],
    "Teaching & Curriculum Development": [_EDUSCI, _EDUARTS],
    "Tourism & Destination Management": [_TOURISM],
    "Hospitality & Guest Services": [_HOSPITALITY],
    "Human Resource & Organizational Development": [_HRM],
    "International Trade & Global Business": [_INTLBUS],
    "Procurement & Supply Chain Management": [_PROCUREMENT],
    "Urban Planning & Land Use": [_URP, _REALESTATE],
    "Geospatial Mapping & Remote Sensing": [_GEOMATICS],
    "Political & Governance Studies": [_POLSCI],
    "Criminal Justice & Security Studies": [_CRIMINOLOGY],
    "General Business Administration & Strategy": [_BUSMGMT],
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
# Agriculture had no strength association at all before Experiment 1 - every
# trained programme needs at least one for the biased-generation weighting
# below to have something programme-specific to draw from.
STRENGTH_MAP["Perseverance & Discipline"].append(_AGRI)

# --- 53-class catalogue expansion additions ---
# No new STRENGTHS_POOL entries needed - the 7 above already cover these new
# domains well; just extending which programmes draw on each.
STRENGTH_MAP["Attention to Precision"].extend([_INDCHEM, _MICRO, _FOODSCI, _REALESTATE, _GEOMATICS, _MEDLAB, _BIOCHEM, _CHEMISTRY])
STRENGTH_MAP["Logical & Analytical Reasoning"].extend([_STATS, _CHEMENG, _DATASCI, _PHYSICS, _BIOMEDENG, _CRIMINOLOGY])
STRENGTH_MAP["Leadership & Strategic Direction"].extend([_EDUSCI, _EDUARTS, _BUSMGMT, _HRM, _INTLBUS, _PROCUREMENT, _POLSCI])
STRENGTH_MAP["Empathy & Human Care"].extend([_PUBHEALTH, _SOCIOLOGY, _SOCIALWORK, _COUNSELING, _PHYSIO, _COMMHEALTH])
STRENGTH_MAP["Team Collaboration"].extend([_TOURISM, _HOSPITALITY])
STRENGTH_MAP["Creative Problem Solving"].append(_URP)
STRENGTH_MAP["Perseverance & Discipline"].extend([_ENVSCI, _FORESTRY])

# Cross-cutting strengths legitimately common across many unrelated
# programmes (per the profile-redesign audit's "shared characteristics"
# tier) - used as the second-choice bucket in biased generation so a
# profile's non-primary picks aren't drawn from the *entire* pool at random,
# but still aren't limited to only that one programme's own associated tags.
SHARED_STRENGTHS: List[str] = [
    "Team Collaboration",
    "Perseverance & Discipline",
    "Logical & Analytical Reasoning",
]

# Fallback ordering when no eligible programme scores above zero (lowest
# admission bars first). Recomputed for the 53-class expansion by actually
# ranking every trained programme's real minimum-requirement "floor" (max
# grade points among minimumSubjectRequirements) rather than guessing - the
# previous hardcoded list included Nursing, whose real floor is a B, a
# strictly worse safety net than the genuinely low-barrier programmes below
# (floor: plain "C", the lowest that exists anywhere in the catalogue - see
# ml/experiments/experiment_5_full_catalogue_53_classes/README.md).
FALLBACK_ORDER = [
    _BUSMGMT, _PROCUREMENT, _FOODSCI, _NUTRITION, _INTLBUS,
    _SOCIOLOGY, _BBIT, _BCOM, _ICS, _AGRI,
]

# Every one of the 53 real, KUCCPS-verified catalogue programmes now has its
# own aspiration/interest/skill/strength vocabulary (see the 53-class
# catalogue expansion additions above), so the model can recommend any
# catalogue programme, not just a 21-programme subset - see
# ml/experiments/experiment_5_full_catalogue_53_classes/README.md for why
# this matters: a programme that's real, verified, and in the catalogue but
# never trainable could never be recommended no matter how well a student's
# profile matched it.
TRAINED_PROGRAMME_TITLES: List[str] = [
    _MBCHB, _BPHARM, _NURSING, _ICS, _SE, _BBIT, _EEE, _CIVIL, _LAW,
    _ACTUARIAL, _BCOM, _DENTAL, _VET, _NUTRITION, _MECH, _ARCH, _QS,
    _MATH, _ECON, _JMC, _AGRI,
    _INDCHEM, _MICRO, _FOODSCI, _STATS, _EDUSCI, _EDUARTS, _PUBHEALTH,
    _SOCIOLOGY, _SOCIALWORK, _COUNSELING, _BUSMGMT, _TOURISM, _HOSPITALITY,
    _REALESTATE, _CHEMENG, _HRM, _INTLBUS, _URP, _GEOMATICS, _MEDLAB,
    _PHYSIO, _COMMHEALTH, _DATASCI, _BIOCHEM, _PHYSICS, _CHEMISTRY,
    _PROCUREMENT, _ENVSCI, _FORESTRY, _BIOMEDENG, _POLSCI, _CRIMINOLOGY,
]
assert len(TRAINED_PROGRAMME_TITLES) == 53
assert all(t in PROGRAMME_TITLES for t in TRAINED_PROGRAMME_TITLES)

assert set(ASPIRATION_MAP) == set(ASPIRATIONS_POOL)
assert set(INTEREST_MAP) == set(INTERESTS_POOL)
assert set(STRENGTH_MAP) == set(STRENGTHS_POOL)
assert set(ASPIRATION_LIKELY_OPTIONALS) == set(ASPIRATIONS_POOL)
assert all(title in PROGRAMME_TITLES for titles in ASPIRATION_MAP.values() for title in titles)
assert all(title in PROGRAMME_TITLES for titles in INTEREST_MAP.values() for title in titles)
assert all(title in PROGRAMME_TITLES for titles in STRENGTH_MAP.values() for title in titles)
assert all(s in FULL_OPTIONAL_SUBJECTS for subs in ASPIRATION_LIKELY_OPTIONALS.values() for s in subs)


def _invert(mapping: Dict[str, List[str]], titles: List[str]) -> Dict[str, List[str]]:
    """programme title -> every pool label whose mapping entry names it."""
    result: Dict[str, List[str]] = {title: [] for title in titles}
    for label, mapped_titles in mapping.items():
        for title in mapped_titles:
            if title in result:
                result[title].append(label)
    return result


# Programme -> its own associated interests/strengths/aspirations, derived
# directly from the maps above so there's exactly one place to edit an
# association and both scoring (_score_programme) and generation
# (_build_profile_for_target) stay consistent with it automatically.
PROGRAMME_INTERESTS: Dict[str, List[str]] = _invert(INTEREST_MAP, TRAINED_PROGRAMME_TITLES)
PROGRAMME_STRENGTHS: Dict[str, List[str]] = _invert(STRENGTH_MAP, TRAINED_PROGRAMME_TITLES)
PROGRAMME_ASPIRATIONS: Dict[str, List[str]] = _invert(ASPIRATION_MAP, TRAINED_PROGRAMME_TITLES)

# Every trained programme must have at least one of its own associated tag
# in each category, and (for aspirations specifically) at least TWO - one
# specific/original plus one of the Experiment 1 shared cluster additions -
# otherwise biased generation below has nothing programme-specific to draw
# from and/or the exclusivity problem this experiment exists to fix would
# silently persist for that programme.
for _title in TRAINED_PROGRAMME_TITLES:
    assert PROGRAMME_INTERESTS[_title], f"{_title} has no associated interests"
    assert PROGRAMME_STRENGTHS[_title], f"{_title} has no associated strengths"
    assert len(PROGRAMME_ASPIRATIONS[_title]) >= 2, f"{_title} still has fewer than 2 aspiration options"


# Experiment 2 (cluster-weighted-points feature) - proposed during the
# original brainstorm, deliberately deferred until Experiment 1's profile
# redesign was validated so any accuracy change here can't be confused with
# that one. One numeric feature per trained programme: the student's real
# KUCCPS Cluster Weighted Points for that programme's own cluster-subject
# set, minus that programme's real average cutoff. Positive = comfortably
# above cutoff, negative = below - gives the model an explicit, direct
# signal for near-cutoff confusions (e.g. Economics vs Mathematics, whose
# cutoffs sit close together) that raw per-subject grade points don't make
# explicit on their own. Shared by training (here) and serving (main.py's
# profile_to_feature_row) so the two schemas can never disagree - same
# principle as build_trait_features above.
CLUSTER_SCORE_COLUMN: Dict[str, str] = {t: f"clsc_{_slug(t)}" for t in TRAINED_PROGRAMME_TITLES}
CLUSTER_SCORE_FEATURE_COLUMNS: List[str] = list(CLUSTER_SCORE_COLUMN.values())


def build_cluster_score_features(grades: Dict[str, str], mean_grade: str) -> Dict[str, float]:
    agg = aggregate_points(grades, mean_grade)
    row: Dict[str, float] = {}
    for title in TRAINED_PROGRAMME_TITLES:
        programme = CATALOG_BY_TITLE[title]
        raw = raw_cluster_points(grades, programme["clusterSubjects"], mean_grade)
        cwp = cluster_weighted_points(raw, agg)
        row[CLUSTER_SCORE_COLUMN[title]] = cwp - programme["averageCutoff"]
    return row


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


# Global tracking counters for dataset generation statistics. These count every
# labelling call, including profiles that are later discarded; the per-profile
# flags in _LAST_LABEL_FLAGS let the generator report the same figures for the
# rows actually kept in the dataset.
GENERATOR_STATS = {
    "top_score_zero": 0,
    "tie_before_tiebreak": 0,
}
_LAST_LABEL_FLAGS = {"top_score_zero": False, "tie_before_tiebreak": False, "no_cutoff_reached": False}


def _score_programme(title: str, interests: List[str], strengths: List[str],
                      aspiration: str) -> float:
    score = 0.0
    if title in ASPIRATION_MAP.get(aspiration, []):
        score += 4.0
    for interest in interests:
        if title in INTEREST_MAP.get(interest, []):
            score += 2.0
    for strength in strengths:
        if title in STRENGTH_MAP.get(strength, []):
            score += 1.0
    return score


def assign_programme_label(grades: Dict[str, str], mean_grade: str, interests: List[str],
                            strengths: List[str], aspiration: str) -> Optional[str]:
    _LAST_LABEL_FLAGS["top_score_zero"] = False
    _LAST_LABEL_FLAGS["tie_before_tiebreak"] = False
    _LAST_LABEL_FLAGS["no_cutoff_reached"] = False
    if grade_to_points(mean_grade) < GRADE_POINTS["C+"]:
        return "Not eligible for degree study"

    agg = aggregate_points(grades, mean_grade)

    eligible = [
        title for title in TRAINED_PROGRAMME_TITLES
        if meets_minimum_requirements(grades, CATALOG_BY_TITLE[title]["minimumSubjectRequirements"], mean_grade)
    ]
    if not eligible:
        return None

    margins: Dict[str, float] = {}
    for title in eligible:
        programme = CATALOG_BY_TITLE[title]
        raw = raw_cluster_points(grades, programme["clusterSubjects"], mean_grade)
        margins[title] = cluster_weighted_points(raw, agg) - programme["averageCutoff"]

    reachable = [title for title in eligible if margins[title] >= 0]
    if not reachable:
        _LAST_LABEL_FLAGS["no_cutoff_reached"] = True
        return None

    scored = [(title, _score_programme(title, interests, strengths, aspiration)) for title in reachable]
    best_score = max(s for _, s in scored)

    if best_score <= 0:
        GENERATOR_STATS["top_score_zero"] += 1
        _LAST_LABEL_FLAGS["top_score_zero"] = True
        candidates = reachable
    else:
        candidates = [title for title, s in scored if s == best_score]

    if len(candidates) > 1:
        GENERATOR_STATS["tie_before_tiebreak"] += 1
        _LAST_LABEL_FLAGS["tie_before_tiebreak"] = True

    return min(candidates, key=lambda title: margins[title])


_JITTER_SPREADS = {
    "Mathematics": [-1, 0, 1, 2],
    "English": [-1, 0, 1],
    "Kiswahili": [-1, 0, 1],
    "Chemistry": [-2, -1, 0, 1],
}
_DEFAULT_OPTIONAL_SPREAD = [-2, -1, 0, 1]


# ---------------------------------------------------------------------------
# Experiment 1 profile generation. Replaces the old two-stage approach (a
# uniform-random `_build_profile` for the bulk of the dataset, unaware of
# which programme it would end up labelling, plus a hand-picked 5-class-only
# `_build_targeted_profile` top-up) with ONE mechanism applied to all 21
# trained programmes: pick a target programme first, generate a profile
# whose interests/strengths/aspiration are *weighted toward* that
# programme's own associations (own pool / shared cross-cutting pool / full
# pool, per the three-tier model in the profile-redesign audit) and whose
# grades are floor-enforced to clear its real KUCCPS minimums, then hand the
# result to the exact same assign_programme_label() rule as before.
#
# This does NOT hand-assign labels and does NOT force the outcome: a biased
# profile can still land on a neighbouring class if its random draws
# genuinely point there (e.g. a BDS-targeted draw whose strengths
# happen to score higher for Medicine) - that's deliberate. It's exactly the
# realistic, ambiguous middle-ground profile the Top-3 ranking exists to
# help with, not a bug in the generator.
#
# Consequences worth stating plainly in Chapter 5.3: (1) every trained
# programme, not just the 5 hardest-gated ones, is now generated with a
# thematic bias rather than pure chance, so resulting class counts do not
# represent naturally-occurring KUCCPS eligibility frequency anywhere in the
# dataset - they represent a deliberately-balanced training population, which
# is what a defensible classifier needs when 21 classes have wildly different
# real-world base rates; (2) the aspiration-leakage issue documented for the
# 21-class baseline (ml/experiments/baseline_21_classes/README.md) is
# addressed at its source (every programme now has >=2 non-exclusive
# aspiration options - see PROGRAMME_ASPIRATIONS / the ASPIRATIONS_POOL
# additions above) rather than by suppressing the aspiration signal itself.
# ---------------------------------------------------------------------------

THIN_CLASS_FLOOR = 200

# Share of synthetic students who have not picked a career yet (their aspiration is
# the UNDECIDED_ASPIRATION value). Their optional subjects were still chosen from the
# underlying leaning, as a real undecided student's subjects would reflect one.
UNDECIDED_RATE = 0.35


def _weighted_sample(k: int, own_pool: List[str], shared_pool: List[str], full_pool: List[str],
                      own_prob: float, shared_prob: float) -> List[str]:
    """Draws k distinct labels from full_pool, biased toward own_pool (with
    probability own_prob per draw) and shared_pool (with probability
    shared_prob per draw), falling back to a uniform draw from the rest of
    full_pool otherwise - the "individual variation" tier from the
    profile-redesign audit: not every profile for a programme gets the same
    bundle, and not every pick has to come from that programme's own tags."""
    picks: List[str] = []
    attempts = 0
    while len(picks) < k and attempts < k * 15:
        attempts += 1
        r = random.random()
        if r < own_prob and own_pool:
            candidate = random.choice(own_pool)
        elif r < own_prob + shared_prob and shared_pool:
            candidate = random.choice(shared_pool)
        else:
            candidate = random.choice(full_pool)
        if candidate not in picks:
            picks.append(candidate)

    if len(picks) < k:
        remaining = [x for x in full_pool if x not in picks]
        random.shuffle(remaining)
        while len(picks) < k and remaining:
            picks.append(remaining.pop())
    return picks


def _build_profile_for_target(profile_id: int, target_title: str) -> dict:
    """Generates one profile biased toward target_title (see module comment
    above), then labels it with the same assign_programme_label() rule used
    everywhere else - the label can differ from target_title."""
    programme = CATALOG_BY_TITLE[target_title]
    min_reqs = programme["minimumSubjectRequirements"]

    # KUCCPS degree applicants must have at least a C+ mean (7 points).
    # Keep the synthetic training population inside that degree-eligible
    # population rather than assigning degree labels to below-threshold
    # fallback profiles.
    mean_points = int(np.clip(np.random.normal(8.5, 2.0), 7, 12))
    mean_grade = points_to_grade(mean_points)

    def jitter(spread):
        return int(np.clip(mean_points + np.random.choice(spread), 1, 12))

    # Aspiration: mostly one of this programme's own (now non-exclusive)
    # options, sometimes a genuinely unrelated one - a student's stated
    # career goal doesn't always match their eventual best-fit programme.
    if random.random() < 0.75:
        aspiration = random.choice(PROGRAMME_ASPIRATIONS[target_title])
    else:
        aspiration = random.choice(ASPIRATIONS_POOL)

    interests = _weighted_sample(
        random.randint(2, 3), PROGRAMME_INTERESTS[target_title], [], INTERESTS_POOL,
        own_prob=0.70, shared_prob=0.0,
    )
    strengths = _weighted_sample(
        random.randint(2, 3), PROGRAMME_STRENGTHS[target_title], SHARED_STRENGTHS, STRENGTHS_POOL,
        own_prob=0.55, shared_prob=0.25,
    )

    # Real KCSE candidates sit 7-9 subjects: the 4 compulsory ones plus 3-5
    # optional ones (Biology among them), chosen with a bias toward whatever plausibly fits the
    # student's stated aspiration (see _choose_optional_subjects).
    total_subjects = random.choice([7, 7, 8, 8, 9])
    n_optional = total_subjects - len(COMPULSORY_SUBJECTS)
    optional_subjects = _choose_optional_subjects(aspiration, n_optional)

    # Guarantee any gated subject that isn't compulsory was actually sat, so
    # eligibility for the target isn't left to a mean-grade fallback guess.
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

    if random.random() < UNDECIDED_RATE:
        aspiration = UNDECIDED_ASPIRATION

    label = assign_programme_label(grades, mean_grade, interests, strengths, aspiration)
    feature_points = extract_ml_feature_points(grades, mean_grade)

    record = {"student_id": f"std_{profile_id:05d}"}
    for subject in ML_FEATURE_SUBJECTS:
        record[FEATURE_COLUMN[subject]] = feature_points[subject]
    record["mean_points"] = mean_points
    record.update(build_trait_features(interests, strengths))
    record.update(build_cluster_score_features(grades, mean_grade))
    record["aspiration"] = aspiration
    record["programme_label"] = label
    record["_tie_before_tiebreak"] = _LAST_LABEL_FLAGS["tie_before_tiebreak"]
    record["_top_score_zero"] = _LAST_LABEL_FLAGS["top_score_zero"]
    record["_no_cutoff_reached"] = _LAST_LABEL_FLAGS["no_cutoff_reached"]
    return record


def _discard_reason(rec: dict) -> Optional[str]:
    label = rec["programme_label"]
    if label == "Not eligible for degree study":
        return "below C+"
    if label is None:
        return "reaches no programme's cutoff" if rec["_no_cutoff_reached"] else "no eligible programme"
    return None


def generate_dataset(seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    np.random.seed(seed)

    GENERATOR_STATS["top_score_zero"] = 0
    GENERATOR_STATS["tie_before_tiebreak"] = 0

    discards_by_reason = {
        "no eligible programme": 0,
        "below C+": 0,
        "reaches no programme's cutoff": 0,
    }

    pass1_kept = 0
    pass1_attempts = 0
    target_pass1 = 6000
    max_pass1_attempts = 120000

    kept_records = []
    pid = 1

    while len(kept_records) < target_pass1 and pass1_attempts < max_pass1_attempts:
        pass1_attempts += 1
        target_title = random.choice(TRAINED_PROGRAMME_TITLES)
        rec = _build_profile_for_target(pid, target_title)
        reason = _discard_reason(rec)
        if reason:
            discards_by_reason[reason] += 1
        else:
            kept_records.append(rec)
            pid += 1

    pass1_kept = len(kept_records)
    if pass1_kept < target_pass1:
        raise RuntimeError(f"Pass 1 could not reach {target_pass1} (kept: {pass1_kept}, attempts: {pass1_attempts})")

    # Pass 2: top up every programme to at least 200
    counts = Counter(r["programme_label"] for r in kept_records)
    pass2_kept = 0
    floor = 200

    for title in TRAINED_PROGRAMME_TITLES:
        attempts_prog = 0
        max_attempts_prog = 30000
        while counts.get(title, 0) < floor and attempts_prog < max_attempts_prog:
            attempts_prog += 1
            rec = _build_profile_for_target(pid, title)
            reason = _discard_reason(rec)
            if reason:
                discards_by_reason[reason] += 1
            elif rec["programme_label"] == title:
                kept_records.append(rec)
                counts[title] = counts.get(title, 0) + 1
                pass2_kept += 1
                pid += 1

        if counts.get(title, 0) < floor:
            raise RuntimeError(f"Safety limit reached: could not top up {title} to {floor} (current: {counts.get(title, 0)})")

    df = pd.DataFrame(kept_records)

    # Model feature columns for exact duplicate detection
    model_feature_cols = (
        [FEATURE_COLUMN[s] for s in ML_FEATURE_SUBJECTS] +
        ["mean_points"] +
        list(INTEREST_COLUMN.values()) +
        list(STRENGTH_COLUMN.values()) +
        ["aspiration"]
    )

    initial_count = len(df)
    df = df.drop_duplicates(subset=model_feature_cols).reset_index(drop=True)
    duplicates_removed = initial_count - len(df)

    # If any programme falls below 200 after deduplication, top it up again
    post_counts = df["programme_label"].value_counts().to_dict()
    extra_top_ups = 0

    for title in TRAINED_PROGRAMME_TITLES:
        needed = max(0, floor - post_counts.get(title, 0))
        attempts_extra = 0
        max_extra = 30000
        while post_counts.get(title, 0) < floor and attempts_extra < max_extra:
            attempts_extra += 1
            rec = _build_profile_for_target(pid, title)
            reason = _discard_reason(rec)
            if reason:
                discards_by_reason[reason] += 1
            elif rec["programme_label"] == title:
                rec_series = pd.Series({col: rec[col] for col in model_feature_cols})
                # Check for duplicates on model feature columns
                matches = (df[model_feature_cols] == rec_series).all(axis=1)
                if not matches.any():
                    df = pd.concat([df, pd.DataFrame([rec])], ignore_index=True)
                    post_counts[title] = post_counts.get(title, 0) + 1
                    extra_top_ups += 1
                    pid += 1

        if post_counts.get(title, 0) < floor:
            raise RuntimeError(f"Safety limit reached after deduplication: could not top up {title} to {floor}")

    final_row_count = len(df)
    distinct_labels = df["programme_label"].nunique()
    val_counts = df["programme_label"].value_counts()
    smallest_class = val_counts.index[-1], int(val_counts.iloc[-1])
    largest_class = val_counts.index[0], int(val_counts.iloc[0])
    profiles_below_cplus = int((df["mean_points"] < 7).sum())
    missing_values = int(df.isnull().sum().sum())

    # Profiles labelled with a programme whose cutoff they did not meet
    cutoff_not_met = 0
    for idx, row in df.iterrows():
        title = row["programme_label"]
        col_name = CLUSTER_SCORE_COLUMN[title]
        if row[col_name] < 0:
            cutoff_not_met += 1

    kept_ties = int(df["_tie_before_tiebreak"].sum())
    kept_top_zero = int(df["_top_score_zero"].sum())
    df = df.drop(columns=["_tie_before_tiebreak", "_top_score_zero", "_no_cutoff_reached"])
    labels_not_in_catalogue = sorted(set(df["programme_label"]) - set(TRAINED_PROGRAMME_TITLES))

    # Print all required metrics
    print(f"Pass 1 kept: {pass1_kept}")
    print(f"Pass 1 attempts: {pass1_attempts}")
    print(f"Pass 2 kept: {pass2_kept}")
    print(f"Discards by reason - no eligible programme: {discards_by_reason['no eligible programme']}")
    print(f"Discards by reason - below C+: {discards_by_reason['below C+']}")
    no_cutoff_discards = discards_by_reason["reaches no programme's cutoff"]
    print(f"Discards by reason - reaches no programme's cutoff: {no_cutoff_discards}")
    print(f"Duplicates removed: {duplicates_removed}")
    print(f"Extra top-ups after deduplication: {extra_top_ups}")
    print(f"Final row count: {final_row_count}")
    print(f"Number of distinct labels: {distinct_labels}")
    print(f"Labels not in the catalogue: {len(labels_not_in_catalogue)} {labels_not_in_catalogue}")
    print(f"Smallest class: {smallest_class[0]} ({smallest_class[1]})")
    print(f"Largest class: {largest_class[0]} ({largest_class[1]})")
    print("Full value_counts:")
    print(val_counts.to_string())
    print(f"Profiles with mean_points < 7: {profiles_below_cplus}")
    print(f"Missing values: {missing_values}")
    print(f"Profiles with a tie for the top score before tie-breaking (kept rows): {kept_ties}")
    print(f"Profiles whose top score was 0 (kept rows): {kept_top_zero}")
    print(f"Labelling calls with a tie, including discarded profiles: {GENERATOR_STATS['tie_before_tiebreak']}")
    print(f"Labelling calls whose top score was 0, including discarded profiles: {GENERATOR_STATS['top_score_zero']}")
    print(f"Profiles labelled with a programme whose cutoff they did not meet: {cutoff_not_met}")

    skl_cols = [c for c in df.columns if c.startswith("skl_")]
    assert len(skl_cols) == 0, f"Found skl_ columns: {skl_cols}"
    print("Confirmation: no column starts with skl_")
    print(f"Full column list ({len(df.columns)} columns):")
    print(list(df.columns))

    return df


def create_synthetic_dataset(n_samples: int = 6000, seed: int = 42) -> pd.DataFrame:
    return generate_dataset(seed=seed)


if __name__ == "__main__":
    out_dir = os.path.dirname(__file__)
    csv_path = os.path.join(out_dir, "xgboost_training_dataset_v3.csv")
    df = generate_dataset(seed=42)
    df.to_csv(csv_path, index=False)
    print(f"Saved dataset to {csv_path}")
