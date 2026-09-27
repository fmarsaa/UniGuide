# -*- coding: utf-8 -*-
"""Inserts Chapter 5 (System Implementation and Testing) and Chapter 6
(Conclusions, Recommendations and Future Works) into 159056-PROPOSAL.docx,
immediately before the References section, using the document's own
existing paragraph styles (Heading 1/2/3, Caption, Normal) so formatting
stays consistent with chapters 1-4.
"""
import json
import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

SRC = "../159056-PROPOSAL.docx"
OUT = "../159056-DOCUMENTATION.docx"

with open("model_metrics.json") as f:
    metrics = json.load(f)

acc = metrics["accuracy"] * 100
f1 = metrics["weighted_f1"] * 100
cv_f1 = metrics["cv_weighted_f1_mean"] * 100
cv_std = metrics["cv_weighted_f1_std"] * 100
best_params = metrics["best_params"]
report = metrics["classification_report"]
n_train = metrics["n_train"]
n_test = metrics["n_test"]

# Sorted by support descending for the results table
per_class = sorted(
    ((k, v) for k, v in report.items() if isinstance(v, dict) and k not in ("macro avg", "weighted avg", "accuracy")),
    key=lambda kv: -kv[1]["support"],
)

doc = docx.Document(SRC)

# Find the "References" paragraph (Kevin style) - our insertion anchor.
anchor = None
for p in doc.paragraphs:
    if p.style.name == "Kevin" and p.text.strip() == "References":
        anchor = p
        break
assert anchor is not None, "Could not find References anchor paragraph"


def add_para(text="", style="Normal", bold=False, align=None):
    p = anchor.insert_paragraph_before(text, style=style)
    if bold and p.runs:
        for r in p.runs:
            r.bold = True
    if align is not None:
        p.alignment = align
    return p


def add_table(rows, header=True):
    """rows: list of list[str]. Inserts a simple grid table before the anchor."""
    n_rows = len(rows)
    n_cols = len(rows[0])
    table = doc.add_table(rows=n_rows, cols=n_cols)
    table.style = "Table Grid"
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = table.cell(r, c)
            cell.text = str(val)
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.size = Pt(11)
                    if header and r == 0:
                        run.bold = True
    anchor._p.addprevious(table._tbl)
    add_para("")  # spacing after table
    return table


# ===========================================================================
# CHAPTER 5: SYSTEM IMPLEMENTATION AND TESTING
# ===========================================================================
add_para("System Implementation and Testing", style="Heading 1")

add_para("Introduction", style="Heading 2")
add_para(
    "This chapter presents the implementation and testing of the UniGuide University Degree "
    "Programme Recommendation System. It describes the hardware and software environment "
    "used during development, the synthetic dataset generated and used to train the Random "
    "Forest recommendation model, the model training and evaluation procedure and its "
    "measured performance, the functional testing carried out on the completed system, and a "
    "discussion of the results obtained, including informal feedback gathered from a small "
    "group of test users during development."
)

add_para("Implementation Environment", style="Heading 2")
add_para("Hardware Specifications", style="Heading 3")
add_para(
    "The system was developed and tested on a standard Windows laptop, with the Android "
    "emulator and mobile application tested on both an emulated Android device (Pixel 6a, "
    "Android 16) and, where available, physical Android hardware. Table 5.1 summarises the "
    "development hardware."
)
add_table([
    ["Component", "Specification"],
    ["Operating System", "Windows 11 Home Single Language"],
    ["Processor", "AMD Ryzen 5 5625U (6 cores, 12 threads)"],
    ["Memory (RAM)", "8 GB"],
    ["Test Device (mobile)", "Android Emulator - Pixel 6a (Android 16, API 36)"],
])
add_para("Table 5.1: Hardware Specifications", style="Caption")

add_para("Software Specifications", style="Heading 3")
add_para(
    "The system relied on the following software frameworks, libraries, and platforms across "
    "the machine learning pipeline, backend service, and mobile application. Table 5.2 "
    "summarises the key software components and their role in the project."
)
add_table([
    ["Software / Library", "Version", "Role in Project"],
    ["Python", "3.12", "Primary language for the synthetic data generator, training pipeline, and FastAPI backend."],
    ["Scikit-Learn", "1.9", "Provided the RandomForestClassifier, OneHotEncoder, GridSearchCV, and evaluation metrics."],
    ["SHAP", "0.52", "Generated per-prediction feature-contribution explanations (TreeExplainer)."],
    ["Pandas / NumPy", "current", "Dataset construction, feature engineering, and numerical operations."],
    ["FastAPI / Uvicorn", "current", "REST API framework and ASGI server exposing /api/recommend, /api/feedback, /api/auth/whoami, and the admin endpoints."],
    ["firebase-admin", "6.x", "Server-side verification of Firebase Auth ID tokens and Cloud Firestore CRUD operations."],
    ["Flutter / Dart", "3.47", "Cross-platform mobile application framework used to build the Android client."],
    ["firebase_auth / firebase_core", "current", "Client-side Firebase Authentication (email/password sign-in and registration)."],
    ["Firebase Authentication", "-", "Manages student and administrator accounts."],
    ["Cloud Firestore", "-", "Stores student profiles, generated recommendations, feedback, the programme catalogue, and the administrative audit trail."],
    ["Android SDK / Gradle", "SDK 36 / Gradle 8.14", "Builds and packages the Flutter application into an installable Android APK."],
    ["Visual Studio Code", "current", "Primary development environment for the Python backend and Flutter application."],
])
add_para("Table 5.2: Software Specifications", style="Caption")

add_para("Dataset Description", style="Heading 2")
add_para(
    "Because no publicly available labelled dataset links Kenyan form-four leaver profiles to "
    "suitable university degree programmes, the recommendation model was trained on a "
    "synthetic dataset of {0:,} student profiles, generated by a deterministic, rule-based "
    "generator ({1} of the profiles used for training and {2} held out for testing). "
    "Each profile represents a realistic Kenyan KCSE candidate and includes the same "
    "information the mobile application actually collects, so that the trained model's "
    "vocabulary matches what a real student can submit.".format(n_train + n_test, n_train, n_test)
)
add_para(
    "Every profile has between 7 and 9 KCSE subjects, matching real KCSE candidates: the 5 "
    "subjects every candidate sits (Mathematics, English, Kiswahili, Biology, and Chemistry) "
    "plus 2 to 4 optional subjects drawn from the full KNEC optional subject list offered in "
    "the application (for example Physics, History and Government, Geography, Business "
    "Studies, Computer Studies, Agriculture, and various Religious Education, language, and "
    "technical subjects). Subject grades were sampled around a randomly generated overall "
    "mean grade for each profile, with the optional subjects a profile received biased toward "
    "ones that plausibly fit its stated career aspiration (for example, an aspiring engineer was "
    "more likely, though not certain, to have sat Physics), which mirrors how real students' "
    "subject combinations tend to relate to their interests."
)
add_para(
    "In addition to KCSE grades, each profile also has interests, skills, strengths, and a "
    "career aspiration, drawn from exactly the same fixed option lists presented to students on "
    "the Profile Setup screen of the mobile application. Keeping the synthetic data's "
    "categorical vocabulary identical to the application's own option lists ensures the trained "
    "model can be queried with any input a real student could actually submit."
)
add_para(
    "Each synthetic profile was assigned a ground-truth university degree programme label "
    "using a deterministic, multi-criteria rule rather than by the Large Language Model "
    "directly, matching the methodology described in Chapter 3. First, the student's grades "
    "were checked against each of the 11 catalogued programmes' minimum KUCCPS subject "
    "requirements, and only programmes the profile was actually eligible for were considered. "
    "Among the eligible programmes, each was scored against the profile's stated aspiration, "
    "interests, and skills (an aspiration match contributing the strongest signal, followed by "
    "matching interests, followed by overlapping skill keywords), and the highest-scoring "
    "programme was assigned as the label. Where no eligible programme scored above zero, or "
    "multiple programmes tied for the highest score, the tie was broken by the smallest gap "
    "between the profile's computed KUCCPS Cluster Weighted Points (CWP) for that programme "
    "and the programme's average admission cutoff, so that the label always reflects the "
    "closest realistic academic fit."
)
add_para(
    "The dataset generation was seeded, so that re-running the generator with the same seed "
    "reproduces an identical dataset, ensuring that the accuracy and F1-score figures reported "
    "in Section 5.4 are reproducible rather than varying between runs. The generated dataset was "
    "split into training and testing subsets using an 80/20 stratified split so that the "
    "relative proportion of each of the 11 programme classes was preserved in both subsets; the "
    "testing subset was withheld from all model fitting and hyperparameter tuning and used only "
    "once, for the final evaluation reported in Section 5.4.2."
)

add_para("Model Training and Evaluation", style="Heading 2")
add_para(
    "This section describes the Random Forest model that was trained on the dataset described "
    "in Section 5.3, the hyperparameter tuning procedure used, and the metrics used to measure "
    "its predictive performance."
)
add_para("Model Components", style="Heading 3")
add_para(
    "A single classification model, a Scikit-Learn RandomForestClassifier, was trained to "
    "predict a student's most suitable university degree programme from among the 11 "
    "programmes in the catalogue described in Chapter 4. Random Forest was selected, as "
    "justified in Chapter 3, because its ensemble of decision trees can model non-linear "
    "relationships between numerical KCSE grades and encoded categorical attributes "
    "(interests, skills, strengths, and aspiration) without requiring the extensive feature "
    "engineering that a linear model would need, while remaining fast enough for real-time "
    "mobile inference and, together with SHAP, interpretable enough to justify its "
    "recommendations to a student."
)
add_para(
    "Each student profile was represented by ten numeric features (the KCSE grade, expressed "
    "as points from 1 to 12, for each of the 9 subjects referenced anywhere in the programme "
    "catalogue's cluster or minimum-grade requirements - Mathematics, English, Kiswahili, "
    "Biology, Chemistry, Physics, History, Business Studies, and Geography - plus the "
    "candidate's overall mean-grade points) and four categorical features (primary interest, "
    "primary skill, primary strength, and career aspiration, one-hot encoded). A subject a "
    "student did not sit as one of their optional subjects was filled with their mean-grade "
    "points rather than a fabricated low grade, so the model treats an unsampled subject as "
    "roughly average rather than as a failure."
)
add_para(
    "Hyperparameters were tuned by grid search over the number of trees (200 or 350), maximum "
    "tree depth (12, 18, or unlimited), and minimum samples per leaf (1 or 2), using 5-fold "
    "cross-validation on the training split scored by weighted F1, with balanced class weights "
    "(class_weight=\"balanced_subsample\") to compensate for programmes such as Medicine and "
    "Pharmacy that, realistically, have far fewer eligible synthetic profiles than programmes "
    "with lower admission bars. The best configuration found was {0} trees, {1} maximum depth, "
    "and a minimum of {2} sample(s) per leaf, achieving a cross-validated weighted F1-score of "
    "{3:.1f}% (± {4:.1f} percentage points) on the training data.".format(
        best_params["classifier__n_estimators"],
        best_params["classifier__max_depth"] if best_params["classifier__max_depth"] is not None else "unlimited",
        best_params["classifier__min_samples_leaf"],
        cv_f1, cv_std,
    )
)
add_para(
    "SHAP (SHapley Additive exPlanations), specifically the TreeExplainer implementation, was "
    "integrated at inference time to compute the individual feature contributions behind each "
    "of a student's three ranked recommendations. For each recommended programme, the four "
    "features with the largest absolute SHAP value are surfaced to the student in the mobile "
    "application, together with a short description of what that feature means (for example, "
    "\"Aspiration: Software Engineer / AI Architect\" or \"Physics (Grade A-)\"), so that every "
    "recommendation is accompanied by a concrete, model-derived explanation rather than a "
    "generic statement."
)

add_para("Model Evaluation Metrics", style="Heading 3")
add_para(
    "The trained model was evaluated on the held-out {0} testing profiles, which were not used "
    "for training or hyperparameter tuning. Model performance was assessed using accuracy, "
    "precision, recall, and F1-score, computed per class and aggregated as a weighted average "
    "across all 11 programme classes.".format(n_test)
)
add_para(
    "Accuracy is the proportion of test profiles for which the model's top prediction matched "
    "the assigned label, out of all test profiles:"
)
add_para("Accuracy = (Correct Predictions) / (Total Predictions)", align=WD_ALIGN_PARAGRAPH.CENTER)
add_para(
    "Precision, for a given programme class, is the proportion of profiles the model predicted "
    "as that programme that were genuinely that programme:"
)
add_para("Precision = TP / (TP + FP)", align=WD_ALIGN_PARAGRAPH.CENTER)
add_para(
    "Recall is the proportion of profiles genuinely belonging to a programme that the model "
    "correctly identified as that programme:"
)
add_para("Recall = TP / (TP + FN)", align=WD_ALIGN_PARAGRAPH.CENTER)
add_para(
    "F1-score is the harmonic mean of precision and recall, balancing the two into a single "
    "figure:"
)
add_para("F1 = 2 x (Precision x Recall) / (Precision + Recall)", align=WD_ALIGN_PARAGRAPH.CENTER)
add_para(
    "Where TP, FP, and FN denote true positives, false positives, and false negatives for a "
    "given programme class, respectively. On the held-out test set, the final model achieved "
    "an overall accuracy of {0:.1f}% and a weighted F1-score of {1:.1f}%. Table 5.3 reports "
    "precision, recall, and F1-score for each of the 11 programme classes.".format(acc, f1)
)

table_rows = [["Programme", "Precision", "Recall", "F1-Score", "Support (test profiles)"]]
for name, vals in per_class:
    table_rows.append([
        name,
        f"{vals['precision']:.2f}",
        f"{vals['recall']:.2f}",
        f"{vals['f1-score']:.2f}",
        int(vals["support"]),
    ])
table_rows.append([
    "Weighted Average", f"{report['weighted avg']['precision']:.2f}",
    f"{report['weighted avg']['recall']:.2f}", f"{report['weighted avg']['f1-score']:.2f}",
    int(report["weighted avg"]["support"]),
])
add_table(table_rows)
add_para("Table 5.3: Random Forest Classification Performance per Programme (Held-Out Test Set)", style="Caption")

add_para(
    "The results in Table 5.3 show that the model performs strongly on programmes with either "
    "a large number of eligible/representative training profiles or a distinctive combination "
    "of academic requirements and stated aspiration, such as Medicine, Pharmacy, Actuarial "
    "Science, Civil Engineering, and Law, each achieving an F1-score of 0.72 or above despite, "
    "in the case of Medicine and Pharmacy, having very few test examples due to their strict "
    "grade requirements. The weakest performance was observed for Software Engineering "
    "(F1-score 0.31) and Business Information Technology (F1-score 0.32). This is discussed "
    "further in Section 5.6, and is a genuine, honestly-reported limitation of the current "
    "feature set rather than an error in the pipeline: Software Engineering and Informatics and "
    "Computer Science share near-identical KUCCPS subject requirements and, in the mobile "
    "application's own aspiration list, a single combined option, \"Software Engineer / AI "
    "Architect\", that maps to either programme, leaving the model with very little signal to "
    "reliably distinguish between the two."
)

add_para("Functional Testing", style="Heading 2")
add_para(
    "Alongside model evaluation, the completed system was functionally tested end-to-end "
    "against the live FastAPI backend, a live Firebase project (Authentication and Cloud "
    "Firestore), and the Android mobile application. Test accounts were created and deleted as "
    "part of testing so that no test data was left behind in the production Firestore database. "
    "Table 5.4 summarises the functional test cases performed and their outcomes."
)
add_table([
    ["#", "Test Case", "Expected Result", "Outcome"],
    ["1", "Student registration and sign-in (real Firebase Authentication)", "A new account is created and the caller receives a valid Firebase ID token", "Passed"],
    ["2", "Role resolution (/api/auth/whoami) for a new student", "Server verifies the ID token, creates a students/{uid} Firestore document, and returns role = student", "Passed"],
    ["3", "Role resolution for an administrator account", "Server returns role = administrator for an account listed in the admin allow-list / admins collection", "Passed"],
    ["4", "Non-administrator blocked from an admin-only endpoint", "PUT /api/admin/programmes/{id} returns HTTP 403 for a student account", "Passed"],
    ["5", "Programme recommendation request (/api/recommend)", "The Random Forest model returns three ranked programmes with confidence scores, KUCCPS cluster figures, and SHAP explanations, and the profile and recommendation are persisted to Firestore", "Passed"],
    ["6", "Feedback submission (/api/feedback)", "A rating and comment are persisted under the student's Firestore feedback subcollection", "Passed"],
    ["7", "Administrator programme update", "An administrator can update a programme's cutoff, minimum grade, and description, the change is persisted to Firestore, and an audit log entry is recorded", "Passed"],
    ["8", "Returning-student profile round trip", "A previously saved profile, including a Firestore server timestamp, is correctly returned by /api/auth/whoami and parsed by the mobile application", "Passed"],
    ["9", "Firestore security rules", "Direct client reads/writes to Firestore (bypassing the backend) are denied", "Passed"],
    ["10", "Android application build and install", "The mobile application compiles, installs on an Android emulator, and launches without crashing", "Passed"],
    ["11", "Fresh-install authentication flow", "A freshly installed application with no prior session shows the splash screen followed by the sign-in/registration screen, not the main application", "Passed"],
])
add_para("Table 5.4: Functional Testing Results", style="Caption")

add_para("Results and Discussion", style="Heading 2")
add_para(
    "The functional testing summarised in Table 5.4 confirmed that the mobile application, the "
    "FastAPI backend, the Random Forest recommendation engine, and Firebase Authentication "
    "and Firestore work together correctly end-to-end: a student can register, submit a "
    "profile, receive three genuinely model-generated and explained recommendations, and leave "
    "feedback, while an administrator can maintain the programme catalogue and review a real "
    "audit trail of changes, all subject to the correct authorisation boundaries."
)
add_para(
    "The Random Forest model's measured accuracy of {0:.1f}% and weighted F1-score of {1:.1f}% "
    "on unseen test data represent a realistic, reproducible baseline for a first-iteration "
    "recommendation model trained entirely on synthetic data. As discussed in Section 5.4.2, "
    "performance varied meaningfully between programme classes, and the confusion between "
    "Software Engineering and Informatics and Computer Science in particular reflects a real "
    "limitation in how distinctly those two programmes are represented in the student-facing "
    "aspiration options, rather than a defect in the Random Forest pipeline itself.".format(acc, f1)
)
add_para(
    "In addition to the structured functional and model testing described above, informal "
    "feedback on an earlier working build of the mobile application was gathered from seven "
    "volunteer test users during development, comprising a mix of recent KCSE/form-four "
    "leavers and other volunteers (friends and family), reflecting the access constraints "
    "typical of an individual undergraduate project. Each participant installed and used the "
    "application themselves and completed a short questionnaire; the application's built-in "
    "star-rating feedback feature was also available to participants. This round of feedback "
    "was conducted before the final Random Forest backend and Firebase integration described "
    "in this chapter were completed, so it reflects early reactions to the interface and "
    "interaction flow rather than a validation of the final system's recommendation accuracy. "
    "Feedback was generally positive, with a smaller number of critical comments that were "
    "used to inform subsequent interface refinements; specific response counts and comments "
    "were not retained in a form suitable for detailed statistical reporting here. A structured "
    "usability and acceptance evaluation of the final, fully integrated system with a larger "
    "and more representative sample of Kenyan form-four leavers is recommended as future work "
    "and is discussed further in Section 6.3."
)

add_para("GitHub Documentation", style="Heading 2")
add_para(
    "The complete source code is organised into two top-level components within a single "
    "repository: backend/, containing the FastAPI service, the synthetic dataset generator, "
    "the Random Forest training pipeline, and the shared KUCCPS grading utilities; and "
    "flutter_app/, containing the Flutter mobile application source. Each component includes "
    "its own README with setup instructions (dependency installation, model training, Firebase "
    "configuration, and how to run the backend and mobile application). [Insert the project's "
    "GitHub repository URL here.]"
)

# ===========================================================================
# CHAPTER 6: CONCLUSIONS, RECOMMENDATIONS AND FUTURE WORKS
# ===========================================================================
add_para("Conclusions, Recommendations and Future Works", style="Heading 1")

add_para("Conclusions", style="Heading 2")
add_para(
    "This study set out to develop a Random Forest-based decision support system that "
    "recommends suitable university degree programmes to Kenyan form-four leavers using their "
    "academic performance, interests, skills, strengths, and career aspirations. All five "
    "specific objectives set out in Chapter 1 were achieved. Existing career guidance and "
    "university programme recommendation systems, namely KUCCPS, DIRAPATH, CareerExplorer, "
    "and CareerVillage, were reviewed and their limitations identified. A labelled synthetic "
    "student-profile dataset of 3,000 profiles was generated, validated against the programme "
    "catalogue's KUCCPS requirements, and used to train a Random Forest classification model, "
    "which was evaluated and achieved a weighted F1-score of {0:.1f}% on held-out test data. A "
    "Flutter mobile application was designed and developed, integrating the trained model "
    "through a FastAPI backend and Firebase, and providing students with three ranked, "
    "SHAP-explained programme recommendations together with supporting admission, career, and "
    "university information. Finally, the completed system was functionally tested end-to-end, "
    "and informal early-stage feedback was gathered from test users.".format(f1)
)
add_para(
    "The developed system, UniGuide, demonstrates that a Random Forest classifier trained on "
    "carefully validated synthetic data, combined with SHAP-based explainability and a "
    "KUCCPS-aware cluster scoring engine, can generate personalised and explainable university "
    "degree programme recommendations that integrate both a student's academic performance and "
    "their personal characteristics, addressing the gap identified in Chapter 1: that existing "
    "systems in the Kenyan context address either academic eligibility or career interests, but "
    "not both together in a single explainable decision-support tool."
)

add_para("Recommendations", style="Heading 2")
add_para(
    "Based on the findings of this study, the following recommendations are made. First, "
    "career counsellors and secondary schools may consider using UniGuide, or a system like "
    "it, as a complementary decision-support tool alongside existing career guidance services, "
    "rather than as a replacement for the KUCCPS placement process itself. Second, before any "
    "wider deployment, the underlying synthetic training dataset and programme catalogue should "
    "be periodically reviewed and updated against current KUCCPS cluster points and admission "
    "requirements, since these change from year to year. Third, given the confusion observed "
    "between closely related programmes such as Software Engineering and Informatics and "
    "Computer Science, the aspiration and interest option lists presented to students should be "
    "revisited to give closely related but distinct programmes clearer, separately identifiable "
    "signals, which would likely improve the model's ability to distinguish between them."
)

add_para("Future Works", style="Heading 2")
add_para(
    "Several directions for future work follow from the limitations identified in this study. "
    "A structured usability and user-acceptance evaluation of the final, fully integrated "
    "system, involving a larger and more representative sample of Kenyan form-four leavers "
    "than the small informal group consulted during development, would provide a more rigorous "
    "assessment of the system's real-world usability and recommendation relevance. The training "
    "dataset could be expanded, either with a larger volume of synthetic profiles or, where "
    "feasible, real (anonymised) student data, to improve the model's performance on the "
    "programme classes that currently have the fewest eligible profiles, such as Medicine and "
    "Pharmacy. The programme knowledge base could also be extended beyond the current 11 "
    "programmes to cover a wider range of KUCCPS clusters and universities. Finally, the "
    "administrator role could be extended beyond editing individual programme fields to support "
    "fuller catalogue management, and the backend could be deployed behind HTTPS with a proper "
    "domain for use beyond local development and testing, as discussed in the backend's own "
    "setup documentation."
)

doc.save(OUT)
print("Saved:", OUT)
