"""
UniGuide - Synthetic Student Profile Dataset Generator
Author: Fatuma Omar Marsa (159056)
Supervised by: Deperias Webula Kerre
Strathmore University - School of Computing and Engineering Sciences

Implements the synthetic data generation pipeline described in Chapter 3:
- Realistic Kenyan form-four leaver distributions
- KCSE subject grades (A to E mapped to points 12 to 1)
- Interests, skills, strengths, and career aspirations
- KUCCPS cluster prerequisite validation
"""

import random
import pandas as pd
import numpy as np

PROGRAMMES = [
    "BSc. Informatics and Computer Science",
    "BSc. Software Engineering",
    "BSc. Data Science and Analytics",
    "BSc. Civil Engineering",
    "Bachelor of Medicine and Bachelor of Surgery (MBChB)",
    "Bachelor of Laws (LL.B)",
    "BSc. Electrical and Electronic Engineering",
    "Bachelor of Business Information Technology (BBIT)",
    "BSc. Financial Engineering",
    "BSc. Nursing",
]

INTERESTS_POOL = [
    "Software Development", "Artificial Intelligence", "Data Science", "Cybersecurity",
    "Civil Infrastructure", "Healthcare & Clinical Care", "Corporate Law", "Financial Markets",
    "Robotics & Automation", "Renewable Energy", "Bioinformatics", "Telecommunications"
]

SKILLS_POOL = [
    "Python Coding", "Mathematical Analysis", "Problem Solving", "Critical Thinking",
    "Scientific Research", "Communication", "System Architecture", "CAD Modeling",
    "Statistical Analysis", "Teamwork", "Public Speaking"
]

STRENGTHS_POOL = [
    "Perseverance", "Logical Reasoning", "Attention to Detail", "Creativity",
    "Leadership", "Empathy", "Spatial Reasoning", "Decision Making"
]

ASPIRATIONS_POOL = [
    "Software Engineer", "AI Specialist", "Data Scientist", "Medical Doctor",
    "Civil Engineer", "Corporate Lawyer", "Financial Analyst", "Cybersecurity Architect",
    "Biomedical Researcher", "Renewable Energy Engineer"
]

GRADE_POINTS = {
    'A': 12, 'A-': 11, 'B+': 10, 'B': 9, 'B-': 8,
    'C+': 7, 'C': 6, 'C-': 5, 'D+': 4, 'D': 3, 'D-': 2, 'E': 1
}

def generate_student_profile(profile_id: int) -> dict:
    # Sample mean grade with distribution centered around B-/B/B+
    mean_points = int(np.clip(np.random.normal(8.5, 2.0), 4, 12))
    
    # Generate core KCSE subjects
    math_pts = int(np.clip(mean_points + np.random.choice([-1, 0, 1, 2]), 1, 12))
    eng_pts = int(np.clip(mean_points + np.random.choice([-1, 0, 1]), 1, 12))
    phys_pts = int(np.clip(mean_points + np.random.choice([-2, -1, 0, 1]), 1, 12))
    chem_pts = int(np.clip(mean_points + np.random.choice([-2, -1, 0, 1]), 1, 12))
    bio_pts = int(np.clip(mean_points + np.random.choice([-2, -1, 0, 1]), 1, 12))
    comp_pts = int(np.clip(mean_points + np.random.choice([0, 1, 2]), 1, 12))

    # Pick 2-3 interests, skills, strengths, aspirations
    interests = random.sample(INTERESTS_POOL, k=random.randint(2, 3))
    skills = random.sample(SKILLS_POOL, k=random.randint(2, 3))
    strengths = random.sample(STRENGTHS_POOL, k=random.randint(2, 3))
    aspirations = random.sample(ASPIRATIONS_POOL, k=1)

    # Determine ground-truth programme label based on multi-criteria heuristic rule
    if "Medical Doctor" in aspirations or "Healthcare & Clinical Care" in interests:
        if bio_pts >= 10 and chem_pts >= 10 and math_pts >= 8:
            label = "Bachelor of Medicine and Bachelor of Surgery (MBChB)"
        else:
            label = "BSc. Nursing"
    elif "Civil Engineer" in aspirations or "Civil Infrastructure" in interests:
        label = "BSc. Civil Engineering"
    elif "Corporate Lawyer" in aspirations or "Corporate Law" in interests:
        label = "Bachelor of Laws (LL.B)"
    elif "Data Scientist" in aspirations or "Data Science" in interests:
        label = "BSc. Data Science and Analytics"
    elif "AI Specialist" in aspirations or "Artificial Intelligence" in interests:
        label = "BSc. Informatics and Computer Science"
    elif "Software Engineer" in aspirations or "Software Development" in interests:
        label = "BSc. Software Engineering"
    elif "Financial Analyst" in aspirations or "Financial Markets" in interests:
        label = "BSc. Financial Engineering"
    else:
        label = "Bachelor of Business Information Technology (BBIT)"

    return {
        "student_id": f"std_{profile_id:04d}",
        "math_score": math_pts,
        "eng_score": eng_pts,
        "phys_score": phys_pts,
        "chem_score": chem_pts,
        "bio_score": bio_pts,
        "comp_score": comp_pts,
        "mean_points": mean_points,
        "primary_interest": interests[0],
        "primary_skill": skills[0],
        "primary_strength": strengths[0],
        "aspiration": aspirations[0],
        "programme_label": label
    }

def create_synthetic_dataset(n_samples: int = 1500) -> pd.DataFrame:
    records = [generate_student_profile(i) for i in range(1, n_samples + 1)]
    return pd.DataFrame(records)

if __name__ == "__main__":
    df = create_synthetic_dataset(1500)
    df.to_csv("synthetic_student_profiles.csv", index=False)
    print(f"Generated {len(df)} synthetic student profiles. Sample distribution:")
    print(df['programme_label'].value_counts())
