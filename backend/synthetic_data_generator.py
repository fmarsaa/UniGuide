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
    # --- 53-class catalogue expansion additions --- each label's first
    # word is deliberately drawn from the matching programme's own
    # requiredSkills text in programmes_catalog.py, so _score_programme's
    # existing substring match stays meaningful without any code change.
    "Chemical Analysis & Process Optimization",
    "Microbial Culturing & Laboratory Research",
    "Statistical Modeling & Programming (R/Python)",
    "Pedagogy & Classroom Management",
    "Epidemiological Surveillance & Health Education",
    "Social Research Methods & Community Engagement",
    "Case Management & Counseling Ethics",
    "Active Listening & Psychological Assessment",
    "Destination Marketing & Itinerary Planning",
    "Guest Relations & Hospitality Service Standards",
    "Recruitment & Employee Relations",
    "Cross-Cultural Trade & Market Entry Strategy",
    "Supply Chain Analysis & Contract Negotiation",
    "Land Use Planning & GIS Mapping",
    "GIS Software & Remote Sensing",
    "Property Valuation & Market Analysis",
    "Forest Resource Assessment & Conservation Planning",
    "Environmental Monitoring & Impact Assessment",
    "Medical Device Design & Signal Processing",
    "Patient Assessment & Rehabilitation Technique",
    "Political Analysis & Policy Research",
    "Criminal Justice Analysis & Investigation",
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
    "Healthcare Professional (General)": [],
    "Technology Professional (General)": ["Computer Studies"],
    "Engineering Professional (General)": ["Physics"],
    "Finance & Business Professional (General)": ["Business Studies"],
    "Built Environment Professional (General)": ["Physics", "Building Construction"],
    "Quantitative Analyst / Researcher (General)": ["Physics"],
    "Public Policy & Communications Professional (General)": ["History & Government"],
    "Agricultural & Environmental Professional (General)": ["Agriculture"],
    "Industrial Chemist / Process Chemist": ["Physics"],
    "Microbiologist": ["Agriculture"],
    "Food Scientist / Food Technologist": ["Agriculture", "Home Science"],
    "Statistician / Data Analyst": ["Physics", "Computer Studies"],
    "Science Teacher / Educator": ["Physics"],
    "Arts Teacher / Educator": ["History & Government"],
    "Public Health Officer": ["Agriculture"],
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
    "Medical Laboratory Technologist": [],
    "Physiotherapist": [],
    "Community Health Officer": ["Agriculture"],
    "Data Scientist": ["Computer Studies", "Physics"],
    "Biochemist": [],
    "Physicist / Research Scientist": ["Physics"],
    "Chemist / Analytical Scientist": ["Physics"],
    "Procurement & Supply Chain Manager": ["Business Studies"],
    "Environmental Scientist / Conservationist": ["Agriculture", "Geography"],
    "Forester / Conservation Officer": ["Agriculture", "Geography"],
    "Biomedical Engineer": ["Physics"],
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

# Generation-bias only (see _build_profile_for_target) - which skills a
# programme's synthetic profiles should be weighted toward. Not used by
# _score_programme, which keeps its existing free-text substring match
# against the real catalog description/requiredSkills; this list only
# decides what a *plausible* student for that programme tends to pick when
# generating a profile, from the exact same SKILLS_POOL the app exposes.
PROGRAMME_SKILLS: Dict[str, List[str]] = {
    _MBCHB: ["Clinical Diagnostics & Health Care", "Scientific Laboratory Research", "Attention to Detail"],
    _BPHARM: ["Clinical Diagnostics & Health Care", "Scientific Laboratory Research", "Attention to Detail"],
    _NURSING: ["Clinical Diagnostics & Health Care", "Team Collaboration & Leadership"],
    _DENTAL: ["Clinical Diagnostics & Health Care", "Attention to Detail"],
    _VET: ["Clinical Diagnostics & Health Care", "Scientific Laboratory Research"],
    _NUTRITION: ["Scientific Laboratory Research", "Attention to Detail"],
    _ICS: ["Python & Software Programming", "Problem Solving & Analytical Logic", "Mathematical & Quantitative Analysis"],
    _SE: ["Python & Software Programming", "Problem Solving & Analytical Logic"],
    _BBIT: ["Python & Software Programming", "Financial Modeling & Accounting", "Team Collaboration & Leadership"],
    _EEE: ["CAD Modeling & Spatial Engineering", "Mathematical & Quantitative Analysis", "Problem Solving & Analytical Logic"],
    _CIVIL: ["CAD Modeling & Spatial Engineering", "Cost Estimation & Construction Economics", "Mathematical & Quantitative Analysis"],
    _MECH: ["CAD Modeling & Spatial Engineering", "Problem Solving & Analytical Logic", "Mathematical & Quantitative Analysis"],
    _ARCH: ["CAD Modeling & Spatial Engineering", "Attention to Detail"],
    _QS: ["Cost Estimation & Construction Economics", "Attention to Detail", "Mathematical & Quantitative Analysis"],
    _LAW: ["Critical Thinking & Persuasive Debate", "Attention to Detail"],
    _ACTUARIAL: ["Mathematical & Quantitative Analysis", "Financial Modeling & Accounting", "Attention to Detail"],
    _BCOM: ["Financial Modeling & Accounting", "Team Collaboration & Leadership"],
    _MATH: ["Mathematical & Quantitative Analysis", "Problem Solving & Analytical Logic"],
    _ECON: ["Mathematical & Quantitative Analysis", "Critical Thinking & Persuasive Debate"],
    _JMC: ["News Writing & Media Research", "Critical Thinking & Persuasive Debate"],
    _AGRI: ["Agricultural & Environmental Science", "Scientific Laboratory Research"],
    # --- 53-class catalogue expansion additions ---
    _INDCHEM: ["Chemical Analysis & Process Optimization", "Scientific Laboratory Research"],
    _MICRO: ["Microbial Culturing & Laboratory Research", "Scientific Laboratory Research"],
    _FOODSCI: ["Scientific Laboratory Research", "Agricultural & Environmental Science"],
    _STATS: ["Statistical Modeling & Programming (R/Python)", "Mathematical & Quantitative Analysis"],
    _EDUSCI: ["Pedagogy & Classroom Management", "Critical Thinking & Persuasive Debate"],
    _EDUARTS: ["Pedagogy & Classroom Management", "News Writing & Media Research"],
    _PUBHEALTH: ["Epidemiological Surveillance & Health Education", "Scientific Laboratory Research"],
    _SOCIOLOGY: ["Social Research Methods & Community Engagement", "Critical Thinking & Persuasive Debate"],
    _SOCIALWORK: ["Case Management & Counseling Ethics", "Social Research Methods & Community Engagement"],
    _COUNSELING: ["Active Listening & Psychological Assessment", "Case Management & Counseling Ethics"],
    _BUSMGMT: ["Financial Modeling & Accounting", "Team Collaboration & Leadership"],
    _TOURISM: ["Destination Marketing & Itinerary Planning", "Team Collaboration & Leadership"],
    _HOSPITALITY: ["Guest Relations & Hospitality Service Standards", "Team Collaboration & Leadership"],
    _REALESTATE: ["Property Valuation & Market Analysis", "Mathematical & Quantitative Analysis"],
    _CHEMENG: ["Chemical Analysis & Process Optimization", "Problem Solving & Analytical Logic"],
    _HRM: ["Recruitment & Employee Relations", "Team Collaboration & Leadership"],
    _INTLBUS: ["Cross-Cultural Trade & Market Entry Strategy", "Financial Modeling & Accounting"],
    _URP: ["Land Use Planning & GIS Mapping", "Critical Thinking & Persuasive Debate"],
    _GEOMATICS: ["GIS Software & Remote Sensing", "Mathematical & Quantitative Analysis"],
    _MEDLAB: ["Scientific Laboratory Research", "Attention to Detail"],
    _PHYSIO: ["Patient Assessment & Rehabilitation Technique", "Clinical Diagnostics & Health Care"],
    _COMMHEALTH: ["Epidemiological Surveillance & Health Education", "Social Research Methods & Community Engagement"],
    _DATASCI: ["Statistical Modeling & Programming (R/Python)", "Python & Software Programming"],
    _BIOCHEM: ["Scientific Laboratory Research", "Chemical Analysis & Process Optimization"],
    _PHYSICS: ["Mathematical & Quantitative Analysis", "Scientific Laboratory Research"],
    _CHEMISTRY: ["Chemical Analysis & Process Optimization", "Scientific Laboratory Research"],
    _PROCUREMENT: ["Supply Chain Analysis & Contract Negotiation", "Financial Modeling & Accounting"],
    _ENVSCI: ["Environmental Monitoring & Impact Assessment", "Agricultural & Environmental Science"],
    _FORESTRY: ["Forest Resource Assessment & Conservation Planning", "Agricultural & Environmental Science"],
    _BIOMEDENG: ["Medical Device Design & Signal Processing", "Mathematical & Quantitative Analysis"],
    _POLSCI: ["Political Analysis & Policy Research", "Critical Thinking & Persuasive Debate"],
    _CRIMINOLOGY: ["Criminal Justice Analysis & Investigation", "Critical Thinking & Persuasive Debate"],
}

# Cross-cutting skills/strengths legitimately common across many unrelated
# programmes (per the profile-redesign audit's "shared characteristics"
# tier) - used as the second-choice bucket in biased generation so a
# profile's non-primary picks aren't drawn from the *entire* pool at random,
# but still aren't limited to only that one programme's own associated tags.
SHARED_SKILLS: List[str] = [
    "Attention to Detail",
    "Team Collaboration & Leadership",
    "Problem Solving & Analytical Logic",
]
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
    assert _title in PROGRAMME_SKILLS and PROGRAMME_SKILLS[_title], f"{_title} has no associated skills"
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


# ---------------------------------------------------------------------------
# Experiment 1 profile generation. Replaces the old two-stage approach (a
# uniform-random `_build_profile` for the bulk of the dataset, unaware of
# which programme it would end up labelling, plus a hand-picked 5-class-only
# `_build_targeted_profile` top-up) with ONE mechanism applied to all 21
# trained programmes: pick a target programme first, generate a profile
# whose interests/skills/strengths/aspiration are *weighted toward* that
# programme's own associations (own pool / shared cross-cutting pool / full
# pool, per the three-tier model in the profile-redesign audit) and whose
# grades are floor-enforced to clear its real KUCCPS minimums, then hand the
# result to the exact same assign_programme_label() rule as before.
#
# This does NOT hand-assign labels and does NOT force the outcome: a biased
# profile can still land on a neighbouring class if its random draws
# genuinely point there (e.g. a BDS-targeted draw whose skills/strengths
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

    mean_points = int(np.clip(np.random.normal(8.5, 2.0), 4, 12))
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
    skills = _weighted_sample(
        random.randint(2, 3), PROGRAMME_SKILLS[target_title], SHARED_SKILLS, SKILLS_POOL,
        own_prob=0.55, shared_prob=0.25,
    )
    strengths = _weighted_sample(
        random.randint(2, 3), PROGRAMME_STRENGTHS[target_title], SHARED_STRENGTHS, STRENGTHS_POOL,
        own_prob=0.55, shared_prob=0.25,
    )

    # Real KCSE candidates sit 7-9 subjects: the 5 compulsory ones plus 2-4
    # optional ones, chosen with a bias toward whatever plausibly fits the
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

    label = assign_programme_label(grades, mean_grade, interests, skills, strengths, aspiration)
    feature_points = extract_ml_feature_points(grades, mean_grade)

    record = {"student_id": f"std_{profile_id:05d}"}
    for subject in ML_FEATURE_SUBJECTS:
        record[FEATURE_COLUMN[subject]] = feature_points[subject]
    record["mean_points"] = mean_points
    record.update(build_trait_features(interests, skills, strengths))
    record.update(build_cluster_score_features(grades, mean_grade))
    record["aspiration"] = aspiration
    record["programme_label"] = label
    return record


def _top_up_to_floor(df: pd.DataFrame, floor: int, seed: int) -> pd.DataFrame:
    """Generalizes the old 5-class-only oversample_thin_classes to every
    trained programme: tops up any class that fell short of `floor` after
    the main balanced-target generation pass, using the exact same
    _build_profile_for_target (and therefore the same assign_programme_label
    rule) as every other profile. Own seed so this pass is reproducible
    independent of how many draws the main pass consumed."""
    rng_state = random.getstate()
    np_state = np.random.get_state()
    random.seed(seed)
    np.random.seed(seed)

    counts = df["programme_label"].value_counts().to_dict()
    extra_records = []
    next_id = 900000
    for title in TRAINED_PROGRAMME_TITLES:
        needed = max(0, floor - counts.get(title, 0))
        attempts = 0
        max_attempts = needed * 25 + 200  # generous ceiling - can't loop forever
        while counts.get(title, 0) < floor and attempts < max_attempts:
            record = _build_profile_for_target(next_id, title)
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


def create_synthetic_dataset(n_samples: int = 1500, seed: int = 42) -> pd.DataFrame:
    # Seeded so the training pipeline is reproducible run-to-run - important
    # for a thesis where reported accuracy/F1 numbers should be reproducible.
    random.seed(seed)
    np.random.seed(seed)
    targets = TRAINED_PROGRAMME_TITLES
    records = [
        _build_profile_for_target(i, random.choice(targets))
        for i in range(1, n_samples + 1)
    ]
    df = pd.DataFrame(records)
    return _top_up_to_floor(df, floor=THIN_CLASS_FLOOR, seed=seed + 1000)


if __name__ == "__main__":
    df = create_synthetic_dataset(1500)
    df.to_csv("synthetic_student_profiles.csv", index=False)
    print(f"Generated {len(df)} synthetic student profiles. Sample distribution:")
    print(df["programme_label"].value_counts())
