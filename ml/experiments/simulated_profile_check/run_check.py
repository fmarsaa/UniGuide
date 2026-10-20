"""System check with 35 SIMULATED student profiles (T01-T35).

These profiles were written by Claude with realistic KCSE grades. They are NOT real students and this is
NOT a user study. What it checks: the recommender answers every profile with three programmes, never marks a
programme as within reach when a required subject grade is missing, and returns programmes that fit what the
profile describes. The "expected" programmes were written down before the run and are one person's judgement,
not ground truth.

    python ml/experiments/simulated_profile_check/run_check.py
"""
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "backend"))
os.chdir(os.path.join(HERE, "..", "..", "..", "backend"))

import main  # noqa: E402
from kuccps import GRADE_POINTS, meets_minimum_requirements, points_to_grade  # noqa: E402

SUBJ = {"M": "Mathematics", "E": "English", "K": "Kiswahili", "C": "Chemistry", "B": "Biology", "P": "Physics",
        "H": "History", "G": "Geography", "S": "Business Studies"}


def g(text):
    return {SUBJ[k]: v for k, v in (item.split(":") for item in text.split(","))}


# id, grades, interests, skills, strengths, career (None = not sure yet), expected programme keywords
P = [
    ("T01", "M:A-,E:B+,K:B+,C:A-,B:A-,P:B+", ["Healthcare & Clinical Medicine"], ["Clinical Diagnostics & Health Care"], ["Empathy & Human Care"], "Medical Doctor (Physician/Surgeon)", ["Medicine and", "Nursing", "Pharmacy", "Dental"]),
    ("T02", "M:B+,E:B,K:B,C:B-,P:B,G:B", ["Software Development & Coding"], ["Python & Software Programming"], ["Logical & Analytical Reasoning"], "Software Engineer / AI Architect", ["Software Engineering", "Informatics", "Information Technology", "Data Science"]),
    ("T03", "M:C+,E:B+,K:B+,C:C+,H:B+,G:B", ["Corporate Law & Constitutional Advocacy"], ["Critical Thinking & Persuasive Debate"], ["Leadership & Strategic Direction"], "Advocate of the High Court / Corporate Lawyer", ["Laws", "Political Science", "Criminology"]),
    ("T04", "M:B,E:B,K:B-,C:C+,S:A-,G:B", ["Financial Markets & Investment Banking"], ["Financial Modeling & Accounting"], ["Attention to Precision"], "Financial Analyst / Investment Banker", ["Commerce", "Economics", "Actuarial"]),
    ("T05", "M:B+,E:B-,K:C+,C:B-,P:B+,G:B", ["Civil Infrastructure & Structural Engineering"], ["CAD Modeling & Spatial Engineering"], ["Creative Problem Solving"], "Civil Infrastructure Engineer", ["Civil Engineering", "Architecture", "Quantity Surveying", "Mechanical"]),
    ("T06", "M:C,E:C+,K:B-,C:C-,H:B-,G:B", ["Teaching & Curriculum Development"], ["Pedagogy & Classroom Management"], ["Team Collaboration"], None, ["Education (Arts)", "Social Work", "Sociology", "Counseling"]),
    ("T07", "M:A-,E:B+,K:B,C:A,B:A,P:B+", ["Pharmaceutical Sciences"], ["Chemical Analysis & Process Optimization"], ["Attention to Precision"], "Pharmacist", ["Pharmacy", "Medicine and", "Biochemistry", "Nursing"]),
    ("T08", "M:B-,E:B+,K:B+,C:B,B:B+,G:B", ["Patient Care & Nursing"], ["Clinical Diagnostics & Health Care"], ["Empathy & Human Care"], "Registered Nursing Specialist", ["Nursing", "Physiotherapy", "Medical Laboratory", "Community Health", "Public Health"]),
    ("T09", "M:C+,E:C+,K:C+,C:C,B:C+,G:C+", ["Environmental Conservation & Sustainability"], ["Environmental Monitoring & Impact Assessment"], ["Perseverance & Discipline"], None, ["Environmental Science", "Forestry", "Agriculture", "Community Health"]),
    ("T10", "M:B-,E:B-,K:B,C:B-,B:B+,G:B", ["Agribusiness & Food Sustainability"], ["Agricultural & Environmental Science"], ["Perseverance & Discipline"], "Agricultural Officer / Agronomist", ["Agriculture", "Food Science", "Forestry", "Environmental"]),
    ("T11", "M:A,E:B+,K:B,C:B+,P:A-,G:B+", ["Mathematical Research & Data Science"], ["Statistical Modeling & Programming (R/Python)"], ["Logical & Analytical Reasoning"], "Data Scientist", ["Data Science", "Mathematics", "Statistics", "Actuarial", "Informatics"]),
    ("T12", "M:C+,E:B-,K:B-,C:C+,P:C+,S:B", ["Business Systems & Enterprise Technology"], ["Problem Solving & Analytical Logic"], ["Team Collaboration"], "Business Systems Analyst / IT Project Manager", ["Information Technology", "Informatics", "Business Management"]),
    ("T13", "M:A-,E:B,K:B,C:B,P:A-,G:B", ["Electrical & Electronic Systems"], ["Problem Solving & Analytical Logic"], ["Logical & Analytical Reasoning"], "Electrical Power Engineer", ["Electrical", "Mechanical", "Biomedical", "Civil"]),
    ("T14", "M:B+,E:B-,K:B-,C:B-,P:B+,S:C+", ["Mechanical Systems & Manufacturing"], ["CAD Modeling & Spatial Engineering"], ["Creative Problem Solving"], "Mechanical Engineer", ["Mechanical", "Electrical", "Civil", "Chemical Engineering"]),
    ("T15", "M:B-,E:B,K:B,C:C+,P:B-,G:B+", ["Architecture & Building Design"], ["CAD Modeling & Spatial Engineering"], ["Creative Problem Solving"], "Architect", ["Architecture", "Quantity Surveying", "Civil", "Urban", "Real Estate"]),
    ("T16", "M:C-,E:B+,K:A-,C:C-,H:B,G:B+", ["Journalism & Media Production"], ["News Writing & Media Research"], ["Creative Problem Solving"], "Journalist / Media Professional", ["Journalism", "Political Science", "Sociology", "Education (Arts)"]),
    ("T17", "M:C+,E:B,K:B+,C:C,G:B+,S:B-", ["Tourism & Destination Management"], ["Destination Marketing & Itinerary Planning"], ["Team Collaboration"], "Tourism Officer / Destination Manager", ["Tourism", "Hospitality", "Business Management", "International Business"]),
    ("T18", "M:C,E:B-,K:B,C:C-,G:B,S:B", ["Hospitality & Guest Services"], ["Guest Relations & Hospitality Service Standards"], ["Team Collaboration"], "Hotel & Hospitality Manager", ["Hospitality", "Tourism", "Business Management"]),
    ("T19", "M:C+,E:B+,K:B,C:C,S:B+,H:B-", ["Human Resource & Organizational Development"], ["Recruitment & Employee Relations"], ["Leadership & Strategic Direction"], "Human Resource Manager", ["Human Resource", "Business Management", "Social Work", "Counseling"]),
    ("T20", "M:B-,E:B,K:B,C:C+,S:A-,G:B", ["International Trade & Global Business"], ["Cross-Cultural Trade & Market Entry Strategy"], ["Leadership & Strategic Direction"], "International Trade Manager", ["International Business", "Business Management", "Economics", "Procurement", "Commerce"]),
    ("T21", "M:B-,E:B-,K:B,C:C+,S:B+,G:B-", ["Procurement & Supply Chain Management"], ["Supply Chain Analysis & Contract Negotiation"], ["Attention to Precision"], "Procurement & Supply Chain Manager", ["Procurement", "Business Management", "International Business", "Commerce"]),
    ("T22", "M:B+,E:B+,K:B,C:B-,S:B+,G:B", ["Economic Policy & Market Analysis"], ["Mathematical & Quantitative Analysis"], ["Logical & Analytical Reasoning"], "Economist / Policy Analyst", ["Economics", "Statistics", "Commerce", "Actuarial", "Political Science"]),
    ("T23", "M:A-,E:B,K:B,C:B,P:B,S:B", ["Actuarial Modeling & Risk Analysis"], ["Mathematical & Quantitative Analysis"], ["Logical & Analytical Reasoning"], "Actuary / Risk Strategist", ["Actuarial", "Statistics", "Mathematics", "Economics", "Data Science"]),
    ("T24", "M:C,E:B,K:B+,C:C-,H:B,G:A-", ["Social Research & Community Development"], ["Social Research Methods & Community Engagement"], ["Empathy & Human Care"], "Social Worker", ["Social Work", "Sociology", "Counseling", "Community Health"]),
    ("T25", "M:C+,E:B+,K:B+,C:C,H:B+,G:B", ["Counseling & Mental Health Support"], ["Active Listening & Psychological Assessment"], ["Empathy & Human Care"], "Counseling Psychologist", ["Counseling", "Social Work", "Sociology"]),
    ("T26", "M:C+,E:B-,K:B-,C:C+,B:B-,G:B-", ["Public Health & Epidemiology"], ["Epidemiological Surveillance & Health Education"], ["Empathy & Human Care"], None, ["Public Health", "Community Health", "Nursing", "Environmental Science"]),
    ("T27", "M:C+,E:C+,K:B-,C:B,B:B+,P:C+", ["Clinical Laboratory & Diagnostic Sciences"], ["Microbial Culturing & Laboratory Research"], ["Attention to Precision"], "Medical Laboratory Technologist", ["Medical Laboratory", "Microbiology", "Biochemistry"]),
    ("T28", "M:B-,E:B-,K:B,C:A-,B:B,P:B", ["Chemical & Materials Sciences"], ["Chemical Analysis & Process Optimization"], ["Attention to Precision"], "Chemist / Analytical Scientist", ["Chemistry", "Industrial Chemistry", "Biochemistry", "Chemical Engineering", "Food Science"]),
    ("T29", "M:B+,E:B-,K:C+,C:B-,P:A-,G:C+", ["Physics & Applied Sciences Research"], ["Mathematical & Quantitative Analysis"], ["Logical & Analytical Reasoning"], "Physicist / Research Scientist", ["Physics", "Mathematics", "Electrical", "Biomedical"]),
    ("T30", "M:B-,E:B-,K:B,C:B-,B:B,P:C+", ["Teaching & Curriculum Development"], ["Pedagogy & Classroom Management"], ["Perseverance & Discipline"], "Science Teacher / Educator", ["Education (Science)", "Mathematics", "Chemistry", "Physics"]),
    ("T31", "M:C,E:C,K:C+,C:C-,G:C,H:C+", ["General Business Administration & Strategy"], ["Team Collaboration & Leadership"], ["Team Collaboration"], None, ["Business Management", "Social Work", "Sociology", "Education (Arts)", "Tourism", "Hospitality"]),
    ("T32", "M:A-,E:A-,K:A-,C:A-,B:A-,P:A-", ["Mathematical Research & Data Science", "Healthcare & Clinical Medicine"], ["Problem Solving & Analytical Logic"], ["Logical & Analytical Reasoning"], None, ["Medicine and", "Data Science", "Actuarial", "Laws", "Pharmacy", "Mathematics", "Software Engineering", "Informatics"]),
    ("T33", "M:D+,E:C-,K:C-,C:D,G:C-,H:C", ["Tourism & Destination Management"], ["Guest Relations & Hospitality Service Standards"], ["Team Collaboration"], None, []),
    ("T34", "M:A,E:D+,K:C,C:A-,B:A-,P:A", ["Healthcare & Clinical Medicine"], ["Clinical Diagnostics & Health Care"], ["Empathy & Human Care"], "Medical Doctor (Physician/Surgeon)", ["Biochemistry", "Physics", "Mathematics", "Chemistry", "Pharmacy"]),
    ("T35", "M:B,E:B,K:B,C:B+,B:B+,P:B", ["Healthcare & Clinical Medicine", "Patient Care & Nursing"], ["Clinical Diagnostics & Health Care"], ["Empathy & Human Care"], "Mechanical Engineer", ["Mechanical", "Nursing", "Biomedical", "Physiotherapy", "Medical Laboratory"]),
]

USER = {"uid": "simulated-check", "email": "sim@example.com", "email_verified": True}


def mean_grade(grades):
    avg = statistics.mean(GRADE_POINTS[v] for v in grades.values())
    return points_to_grade(round(avg))


def main_run():
    rows, times = [], []
    for pid, gtext, interests, skills, strengths, career, expect in P:
        grades = g(gtext)
        payload = main.StudentProfilePayload(
            kcseMeanGrade=mean_grade(grades), grades=grades, interests=interests, skills=skills,
            strengths=strengths, aspirations=[career] if career else [])
        t = time.perf_counter()
        results = main.get_recommendations(payload, USER, preview=True)
        times.append((time.perf_counter() - t) * 1000)
        titles = [r["programme"]["title"] for r in results]
        within = sum(1 for r in results if r["meetsMinimumRequirements"])
        violations = sum(1 for r in results if r["meetsMinimumRequirements"] and not meets_minimum_requirements(grades, r["programme"].get("minimumSubjectRequirements") or {}))
        top1_hit = bool(expect) and any(k in titles[0] for k in expect)
        top3_hit = bool(expect) and any(k in t for t in titles for k in expect)
        rows.append(dict(id=pid, mean=payload.kcseMeanGrade, career=career or "not sure yet", titles=titles, within=within,
                         violations=violations, top1=top1_hit, top3=top3_hit, expected=bool(expect)))
    return rows, times


def short(t):
    return t.replace("Bachelor of Science in ", "BSc ").replace("Bachelor of Arts in ", "BA ").replace("Bachelor of Engineering in ", "BEng ").replace("Bachelor of ", "B. ")


if __name__ == "__main__":
    rows, times = main_run()
    print("| ID | Mean | Career picked | Top three shown | Within reach | Expected fit (top 1 / top 3) |")
    print("|---|---|---|---|---|---|")
    for r in rows:
        fit = "n/a (none expected)" if not r["expected"] else f"{'yes' if r['top1'] else 'no'} / {'yes' if r['top3'] else 'no'}"
        print(f"| {r['id']} | {r['mean']} | {r['career'][:28]} | {'; '.join(short(t) for t in r['titles'])} | {r['within']}/3 | {fit} |")
    judged = [r for r in rows if r["expected"]]
    print()
    print(f"profiles run: {len(rows)}; all answered with three programmes: {all(len(r['titles']) == 3 for r in rows)}")
    print(f"programmes wrongly marked within reach: {sum(r['violations'] for r in rows)}")
    print(f"expected fit in top 1: {sum(r['top1'] for r in judged)}/{len(judged)}; in top 3: {sum(r['top3'] for r in judged)}/{len(judged)}")
    print(f"profiles with at least one programme within reach: {sum(1 for r in rows if r['within'] > 0)}/{len(rows)}")
    times.sort()
    print(f"response time: median {statistics.median(times):.0f} ms, slowest {times[-1]:.0f} ms")
