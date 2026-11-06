"""Runs the three demo profiles through the backend's recommendation code with the v4
model and the live programme catalogue, as a preview (nothing is saved), and prints
the programme titles, eligibility and message for each.

    python demo_profiles.py
"""
import contextlib
import io

with contextlib.redirect_stdout(io.StringIO()):
    import main

DEMO_USER = {"uid": "demo-profile-check", "email_verified": True}

PROFILES = [
    ("1. Strong science student", main.StudentProfilePayload(
        kcseMeanGrade="A-",
        grades={"Mathematics": "A", "English": "B+", "Kiswahili": "B", "Chemistry": "A",
                "Biology": "A", "Physics": "A-", "Geography": "B+"},
        interests=["Healthcare & Clinical Medicine", "Clinical Laboratory & Diagnostic Sciences"],
        strengths=["Logical & Analytical Reasoning", "Empathy & Human Care"],
        aspirations=["Medical Doctor (Physician/Surgeon)"],
    )),
    ("2. Undecided student (Not sure yet)", main.StudentProfilePayload(
        kcseMeanGrade="B",
        grades={"Mathematics": "B", "English": "B+", "Kiswahili": "B", "Chemistry": "B-",
                "Biology": "B", "History & Government": "A-", "Business Studies": "B+"},
        interests=["Journalism & Media Production", "Social Research & Community Development"],
        strengths=["Team Collaboration", "Creative Problem Solving"],
        aspirations=[],
    )),
    ("3. C+ mean, meets no programme's subject requirements", main.StudentProfilePayload(
        kcseMeanGrade="C+",
        grades={"Mathematics": "D+", "English": "C-", "Kiswahili": "B", "Chemistry": "D+",
                "Christian Religious Education (CRE)": "A", "Home Science": "B+", "Art & Design": "B-"},
        interests=["Hospitality & Guest Services"],
        strengths=["Creative Problem Solving"],
        aspirations=[],
    )),
]


def main_() -> None:
    print(f"Model: {main.MODEL_FILENAME}, version {main.model_version()}")
    for name, payload in PROFILES:
        response = main.get_recommendations(payload, DEMO_USER, preview=True)
        results = response["recommendations"]
        print(f"\n{name}")
        print(f"  mean grade {payload.kcseMeanGrade}; grades {payload.grades}")
        print(f"  career: {payload.aspirations[0] if payload.aspirations else 'Not sure yet'}")
        print(f"  recommendations: {len(results)}")
        for r in results:
            print(f"    {r['rank']}. {r['programme']['title']} | meets subject requirements: "
                  f"{r['meetsMinimumRequirements']} | {r.get('eligibilityStatus')}")
        print(f"  message: {response.get('message')}")


if __name__ == "__main__":
    main_()
