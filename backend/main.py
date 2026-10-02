"""
UniGuide - FastAPI REST Backend Service
Author: Fatuma Omar Marsa (159056)
Supervised by: Deperias Webula Kerre
Strathmore University - School of Computing and Engineering Sciences

Connects the Flutter Mobile Application with:
1. Scikit-Learn Random Forest Classifier (real inference against
   rf_model_pipeline.pkl - produced by train_random_forest.py)
2. SHAP Explainability Subsystem (real per-prediction feature contributions)
3. KUCCPS Cluster Weight Calculations (kuccps.py)
4. Firebase Authentication & Cloud Firestore (firebase_setup.py)

Every endpoint that claims to persist data or verify identity genuinely does
so; if Firebase Admin isn't configured (FIREBASE_SERVICE_ACCOUNT_PATH), those
endpoints return a clear 503 instead of silently pretending to succeed.
"""

import logging
import os
import pickle
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import shap
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import firestore as fb_firestore
from pydantic import BaseModel

from firebase_setup import admin_emails, get_db, init_firebase, verify_id_token
from kuccps import (
    FEATURE_COLUMN,
    ML_FEATURE_SUBJECTS,
    aggregate_points,
    cluster_weighted_points,
    eligibility_status,
    extract_ml_feature_points,
    grade_to_points,
    meets_minimum_requirements,
    points_to_grade,
    raw_cluster_points,
)
from programmes_catalog import CATALOG_BY_ID, CATALOG_BY_TITLE, PROGRAMMES
from synthetic_data_generator import FALLBACK_ORDER, TRAIT_COLUMN_INFO, build_cluster_score_features, build_trait_features
from catalogue_freshness import check_catalogue_freshness

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uniguide")


@asynccontextmanager
async def _lifespan(app: FastAPI):
    # _start_scheduler/_stop_scheduler are defined further down this module
    # (alongside the scheduler they manage) - resolved by name at call time,
    # not here, so the definition order below is fine.
    _start_scheduler()
    yield
    _stop_scheduler()


app = FastAPI(
    title="UniGuide REST API",
    description="Machine Learning Decision Support Backend for Kenyan Form-Four Leavers",
    version="1.0.0",
    lifespan=_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------
MODEL_PATH = os.path.join(os.path.dirname(__file__), "rf_model_pipeline.pkl")
_pipeline = None
_explainer = None


def _load_model() -> None:
    global _pipeline, _explainer
    if not os.path.isfile(MODEL_PATH):
        logger.warning(
            "rf_model_pipeline.pkl not found at %s. Run `python train_random_forest.py` "
            "in backend/ before calling /api/recommend.", MODEL_PATH,
        )
        return
    with open(MODEL_PATH, "rb") as f:
        _pipeline = pickle.load(f)
    _explainer = shap.TreeExplainer(_pipeline.named_steps["classifier"])
    logger.info("Random Forest pipeline and SHAP explainer loaded (%d classes).", len(_pipeline.classes_))


# ---------------------------------------------------------------------------
# Background scheduler - weekly catalogue freshness check
# ---------------------------------------------------------------------------
# Previously this check only ran when an admin manually clicked "Run Check"
# in the dashboard, so a university quietly dropping a programme could go
# unnoticed for however long it took someone to remember to check. Running
# it automatically, on a light weekly cadence, turns it into a genuinely
# autonomous feature - it still only ever proposes flags for a human to
# review (see _run_catalogue_freshness_check_and_flag's docstring), never
# auto-edits the catalog, so the human-in-the-loop guarantee is unchanged.
_scheduler = BackgroundScheduler(daemon=True)


def _scheduled_freshness_check() -> None:
    try:
        result = _run_catalogue_freshness_check_and_flag(actor="Scheduled Weekly Check")
        logger.info("Scheduled catalogue freshness check completed: %s", result)
    except Exception:
        # A transient KUCCPS/Firestore outage shouldn't crash the scheduler
        # thread or stop future runs - just log it, same as any other
        # best-effort background maintenance job.
        logger.exception("Scheduled catalogue freshness check failed; will retry on the next schedule.")


def _start_scheduler() -> None:
    if get_db() is None:
        logger.info("Firestore not configured - skipping scheduled catalogue freshness check.")
        return
    _scheduler.add_job(
        _scheduled_freshness_check,
        trigger="interval",
        weeks=1,
        id="catalogue_freshness_weekly",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduled catalogue freshness check registered (runs every 7 days).")


def _stop_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)


_load_model()
init_firebase()

NUMERIC_LABELS = {FEATURE_COLUMN[subject]: subject for subject in ML_FEATURE_SUBJECTS}
NUMERIC_LABELS["mean_points"] = "KCSE Mean Points"
CATEGORY_INFO = {
    "aspiration": ("Aspirations", "Aspiration"),
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class StudentProfilePayload(BaseModel):
    uid: Optional[str] = None
    fullName: str = ""
    indexNumber: str = ""
    kcseMeanGrade: str = "C+"
    kcseMeanPoints: Optional[int] = None
    grades: Dict[str, str] = {}
    interests: List[str] = []
    skills: List[str] = []
    strengths: List[str] = []
    aspirations: List[str] = []
    calculatedClusterScore: Optional[float] = None


class FeedbackPayload(BaseModel):
    student_id: Optional[str] = None
    recommendation_id: str
    rating: int
    comments: str = ""
    timestamp: Optional[str] = None


class ProgrammeUpdatePayload(BaseModel):
    averageCutoff: Optional[float] = None
    minMeanGrade: Optional[str] = None
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# Auth dependencies
# ---------------------------------------------------------------------------
def require_auth(authorization: Optional[str] = Header(None)) -> dict:
    if not init_firebase():
        raise HTTPException(
            status_code=503,
            detail="Firebase Admin is not configured on the server. See backend/README.md.",
        )
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token in Authorization header.")
    token = authorization.split(" ", 1)[1].strip()
    try:
        decoded = verify_id_token(token)
    except Exception as exc:  # noqa: BLE001 - surface the real reason to the client
        raise HTTPException(status_code=401, detail=f"Invalid or expired authentication token: {exc}")

    # Defense in depth: the Flutter app already blocks unverified users from
    # reaching any screen that calls the backend, but a client can't be
    # trusted to enforce this itself - the server must check too.
    if not decoded.get("email_verified", False):
        raise HTTPException(
            status_code=403,
            detail="Please verify your email address before continuing. Check your inbox for the verification link.",
        )
    return decoded


def require_admin(decoded: dict = Depends(require_auth)) -> dict:
    db = get_db()
    email = (decoded.get("email") or "").lower()
    is_admin = email in admin_emails()
    if not is_admin and db is not None:
        is_admin = db.collection("admins").document(decoded["uid"]).get().exists
    if not is_admin:
        raise HTTPException(status_code=403, detail="Administrator privileges required.")
    return decoded


# ---------------------------------------------------------------------------
# Feature extraction + SHAP helpers
# ---------------------------------------------------------------------------
def profile_to_feature_row(payload: StudentProfilePayload):
    grades = payload.grades or {}
    mean_grade = payload.kcseMeanGrade or "C+"
    feature_points = extract_ml_feature_points(grades, mean_grade)
    mean_points = payload.kcseMeanPoints or grade_to_points(mean_grade)

    row = {FEATURE_COLUMN[subject]: feature_points[subject] for subject in ML_FEATURE_SUBJECTS}
    row["mean_points"] = mean_points
    row.update(build_trait_features(payload.interests or [], payload.skills or [], payload.strengths or []))
    row.update(build_cluster_score_features(grades, mean_grade))
    row["aspiration"] = payload.aspirations[0] if payload.aspirations else ""
    return pd.DataFrame([row]), grades, mean_grade


def _extract_class_shap(raw_shap, class_idx: int, n_classes: int) -> np.ndarray:
    arr = np.asarray(raw_shap)
    if arr.ndim == 3:
        if arr.shape[-1] == n_classes:
            return arr[:, :, class_idx]
        if arr.shape[0] == n_classes:
            return arr[class_idx]
    return arr


def describe_feature(raw_name: str, row: dict):
    prefix, _, rest = raw_name.partition("__")
    if prefix == "num":
        if rest in TRAIT_COLUMN_INFO:
            category, word, original_label = TRAIT_COLUMN_INFO[rest]
            selected = bool(row.get(rest))
            feature_name = f"{word}: {original_label}" if selected else f"No {word.lower()} in '{original_label}'"
            desc = (
                f"You selected '{original_label}' as a {word.lower()}, relating to this programme."
                if selected
                else f"You did not select '{original_label}' as a {word.lower()}."
            )
            return category, feature_name, desc

        label = NUMERIC_LABELS.get(rest, rest)
        if rest == "mean_points":
            feature_name = f"{label}: {row[rest]}"
            desc = f"An overall KCSE mean of {row[rest]} points is a contributing academic factor."
        else:
            grade = points_to_grade(int(row[rest]))
            feature_name = f"{label} (Grade {grade})"
            desc = f"{label} grade of {grade} is an academic factor behind this recommendation."
        return "Academic", feature_name, desc

    for col, (category, word) in CATEGORY_INFO.items():
        col_prefix = f"{col}_"
        if rest.startswith(col_prefix):
            value = rest[len(col_prefix):]
            feature_name = f"{word}: {value}"
            desc = f"Your stated {word.lower()} of '{value}' relates to this programme's profile."
            return category, feature_name, desc

    return "Other", rest, ""


def top_shap_explanations(class_shap_row: np.ndarray, feature_names, row: dict, top_n: int = 4):
    order = np.argsort(-np.abs(class_shap_row))[:top_n]
    explanations = []
    for idx in order:
        value = float(class_shap_row[idx])
        if abs(value) < 1e-6:
            continue
        category, feature_name, desc = describe_feature(feature_names[idx], row)
        explanations.append({
            "featureName": feature_name,
            "category": category,
            "shapValue": round(value, 4),
            "description": desc,
        })
    return explanations


def build_primary_reason(shap_list, title: str, confidence: float) -> str:
    pct = f"{confidence * 100:.1f}%"
    if shap_list:
        lead = shap_list[0]["featureName"]
        return f"Primarily driven by {lead}, yielding a {pct} Random Forest confidence for {title}."
    return f"Random Forest model confidence of {pct} for {title} based on the submitted profile."


def _persist_recommendation(uid: str, email: Optional[str], payload: StudentProfilePayload, results: list) -> None:
    db = get_db()
    if db is None:
        return
    try:
        student_ref = db.collection("students").document(uid)
        student_ref.set({
            "uid": uid,
            "email": email,
            "fullName": payload.fullName,
            "indexNumber": payload.indexNumber,
            "kcseMeanGrade": payload.kcseMeanGrade,
            "kcseMeanPoints": payload.kcseMeanPoints,
            "grades": payload.grades,
            "interests": payload.interests,
            "skills": payload.skills,
            "strengths": payload.strengths,
            "aspirations": payload.aspirations,
            "role": "student",
            "updatedAt": fb_firestore.SERVER_TIMESTAMP,
        }, merge=True)
        student_ref.collection("recommendations").add({
            "recommendations": results,
            "createdAt": fb_firestore.SERVER_TIMESTAMP,
        })
    except Exception:
        logger.exception("Failed to persist recommendation for uid=%s", uid)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
def _load_model_metrics() -> Optional[dict]:
    metrics_path = os.path.join(os.path.dirname(__file__), "model_metrics.json")
    if not os.path.isfile(metrics_path):
        return None
    try:
        import json

        with open(metrics_path) as f:
            data = json.load(f)
        return {"accuracy": data.get("accuracy"), "weighted_f1": data.get("weighted_f1")}
    except Exception:
        logger.exception("Failed to read model_metrics.json")
        return None


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "system": "UniGuide Mobile ML Backend",
        "model": "Random Forest Classifier (Scikit-Learn)",
        "model_loaded": _pipeline is not None,
        "model_metrics": _load_model_metrics(),
        "explainability": "SHAP (SHapley Additive exPlanations)",
        "firestore_configured": init_firebase(),
        "author": "Fatuma Omar Marsa (159056), Strathmore University",
    }


@app.post("/api/auth/whoami")
def whoami(decoded: dict = Depends(require_auth)):
    db = get_db()
    uid = decoded["uid"]
    email = (decoded.get("email") or "").lower()
    role = "student"
    profile = None

    admin_doc = db.collection("admins").document(uid).get()
    if admin_doc.exists or email in admin_emails():
        role = "administrator"
        if not admin_doc.exists and email in admin_emails():
            db.collection("admins").document(uid).set({
                "uid": uid, "email": email, "role": "admin",
                "createdAt": fb_firestore.SERVER_TIMESTAMP,
            }, merge=True)
    else:
        student_ref = db.collection("students").document(uid)
        student_doc = student_ref.get()
        if not student_doc.exists:
            student_ref.set({
                "uid": uid, "email": email, "role": "student",
                "fullName": decoded.get("name", ""),
                "createdAt": fb_firestore.SERVER_TIMESTAMP,
            }, merge=True)
        else:
            profile = student_doc.to_dict()

    return {"uid": uid, "email": email, "role": role, "profile": profile}


@app.get("/api/programmes")
def list_programmes():
    db = get_db()
    if db is not None:
        try:
            docs = {d.id: d.to_dict() for d in db.collection("programmes").stream()}
            missing = [p for p in PROGRAMMES if p["id"] not in docs]
            if missing:
                # Firestore only has a partial set (e.g. an admin edit lazily
                # created just the one programme they touched) - backfill the
                # rest from the static catalog instead of silently serving an
                # incomplete list.
                batch = db.batch()
                for programme in missing:
                    batch.set(db.collection("programmes").document(programme["id"]), programme)
                batch.commit()
                for programme in missing:
                    docs[programme["id"]] = programme
            # Preserve catalog ordering; fall back to the static entry for any
            # id Firestore still doesn't have (belt-and-braces).
            return [docs.get(p["id"], p) for p in PROGRAMMES]
        except Exception:
            logger.exception("Failed reading programmes from Firestore; serving static catalog instead.")
    return PROGRAMMES


def select_recommended_indices(
    proba: np.ndarray, classes: np.ndarray, grades: Dict[str, str], mean_grade: str
) -> tuple:
    """Ranks genuinely eligible programmes by predicted probability, falling
    back to FALLBACK_ORDER when fewer than 3 are eligible. Returns
    (top_idx, eligible_mask). Factored out of get_recommendations so it's
    unit-testable (backend/tests/test_recommend_eligibility.py) without
    going through the HTTP layer, Firebase Auth, or Firestore persistence.

    The training labels this model learned from were only ever assigned
    among programmes a synthetic profile actually met the real KUCCPS
    minimum subject-grade requirements for (see
    synthetic_data_generator.assign_programme_label) - ranking by raw
    probability alone, with no gate, would recommend programmes a real
    student cannot be admitted to at all, mislabeled only as "high risk"
    by eligibility_status() rather than "does not qualify". Filter to
    genuinely eligible programmes first, exactly mirroring how the
    training data was generated. A student who doesn't meet the minimum
    requirements for ANY trained programme still needs a useful answer,
    not an empty one - fill remaining slots from the same low-barrier
    fallback the training generator itself falls back to. Every result is
    still explicitly marked (by the caller, via eligible_mask) with
    whether it was a genuine eligible match or a fallback suggestion, so
    the app can be honest about the difference.
    """
    n_classes = len(classes)
    eligible_mask = [
        meets_minimum_requirements(grades, CATALOG_BY_TITLE[c]["minimumSubjectRequirements"], mean_grade)
        for c in classes
    ]
    eligible_idx = [i for i in range(n_classes) if eligible_mask[i]]
    top_idx = sorted(eligible_idx, key=lambda i: -proba[i])[:3]

    if len(top_idx) < 3:
        for title in FALLBACK_ORDER:
            if title not in classes:
                continue
            idx = int(np.where(classes == title)[0][0])
            if idx not in top_idx:
                top_idx.append(idx)
            if len(top_idx) == 3:
                break
    return top_idx, eligible_mask


@app.post("/api/recommend")
def get_recommendations(payload: StudentProfilePayload, decoded: dict = Depends(require_auth)):
    if _pipeline is None or _explainer is None:
        raise HTTPException(
            status_code=503,
            detail="Model not trained yet. Run `python train_random_forest.py` in backend/ first.",
        )

    uid = decoded["uid"]
    row_df, grades, mean_grade = profile_to_feature_row(payload)

    proba = _pipeline.predict_proba(row_df)[0]
    classes = _pipeline.classes_
    n_classes = len(classes)

    top_idx, eligible_mask = select_recommended_indices(proba, classes, grades, mean_grade)

    X_trans = _pipeline.named_steps["preprocessor"].transform(row_df)
    feature_names = _pipeline.named_steps["preprocessor"].get_feature_names_out()
    raw_shap = _explainer.shap_values(X_trans, check_additivity=False)
    row_values = row_df.iloc[0].to_dict()

    agg = aggregate_points(grades, mean_grade)

    results = []
    for rank, class_idx in enumerate(top_idx, start=1):
        title = classes[class_idx]
        programme = CATALOG_BY_TITLE.get(title)
        if programme is None:
            continue

        confidence = float(proba[class_idx])
        raw_cluster = raw_cluster_points(grades, programme["clusterSubjects"], mean_grade)
        cwp = cluster_weighted_points(raw_cluster, agg)
        cutoff_diff = round(cwp - programme["averageCutoff"], 1)

        class_shap = _extract_class_shap(raw_shap, class_idx, n_classes)[0]
        shap_list = top_shap_explanations(class_shap, feature_names, row_values)
        primary_reason = build_primary_reason(shap_list, title, confidence)

        meets_requirements = eligible_mask[class_idx]

        results.append({
            "rank": rank,
            "confidenceScore": round(confidence, 3),
            "studentClusterScore": cwp,
            "cutoffDiff": cutoff_diff,
            "eligibilityStatus": eligibility_status(cwp, programme["averageCutoff"], meets_requirements),
            "meetsMinimumRequirements": meets_requirements,
            "primaryReason": primary_reason,
            "programme": programme,
            "shapExplanations": shap_list,
        })

    _persist_recommendation(uid, decoded.get("email"), payload, results)
    return results


@app.post("/api/feedback")
def submit_feedback(feedback: FeedbackPayload, decoded: dict = Depends(require_auth)):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Firestore is not configured on the server.")
    uid = decoded["uid"]
    doc_ref = db.collection("students").document(uid).collection("feedback").document()
    doc_ref.set({
        "recommendationId": feedback.recommendation_id,
        "rating": feedback.rating,
        "comments": feedback.comments,
        "submittedAt": fb_firestore.SERVER_TIMESTAMP,
    })
    return {"status": "success", "feedback_id": doc_ref.id}


@app.put("/api/admin/programmes/{programme_id}")
def update_programme(programme_id: str, body: ProgrammeUpdatePayload, decoded: dict = Depends(require_admin)):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Firestore is not configured on the server.")
    if programme_id not in CATALOG_BY_ID:
        raise HTTPException(status_code=404, detail="Unknown programme id.")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update were provided.")

    doc_ref = db.collection("programmes").document(programme_id)
    if not doc_ref.get().exists:
        doc_ref.set(CATALOG_BY_ID[programme_id])
    doc_ref.update(updates)

    change_summary = ", ".join(f"{field}={value!r}" for field, value in updates.items())
    db.collection("audit_logs").document().set({
        "action": "Programme Information Updated",
        "actor": decoded.get("email") or decoded["uid"],
        "details": f"Updated {programme_id}: {change_summary}",
        "timestamp": fb_firestore.SERVER_TIMESTAMP,
    })

    return doc_ref.get().to_dict()


@app.get("/api/admin/audit-logs")
def list_audit_logs(decoded: dict = Depends(require_admin)):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Firestore is not configured on the server.")
    query = db.collection("audit_logs").order_by("timestamp", direction=fb_firestore.Query.DESCENDING).limit(25)
    logs = []
    for doc in query.stream():
        entry = doc.to_dict()
        entry["id"] = doc.id
        timestamp = entry.get("timestamp")
        entry["timestamp"] = timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
        logs.append(entry)
    return logs


@app.get("/api/admin/feedback")
def list_feedback(decoded: dict = Depends(require_admin)):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Firestore is not configured on the server.")

    # collection_group() over every students/{uid}/feedback subcollection.
    # Sorted in Python rather than via Firestore order_by() so this doesn't
    # depend on a manually-created composite index existing.
    entries = []
    for doc in db.collection_group("feedback").stream():
        entry = doc.to_dict()
        entry["id"] = doc.id
        submitted_at = entry.get("submittedAt")
        entry["submittedAt"] = submitted_at.isoformat() if hasattr(submitted_at, "isoformat") else str(submitted_at)

        student_ref = doc.reference.parent.parent
        entry["studentUid"] = student_ref.id if student_ref is not None else None
        student_doc = student_ref.get() if student_ref is not None else None
        entry["studentEmail"] = student_doc.get("email") if student_doc is not None and student_doc.exists else None

        entries.append(entry)

    entries.sort(key=lambda e: e.get("submittedAt") or "", reverse=True)
    return entries[:50]


def _run_catalogue_freshness_check_and_flag(actor: str) -> dict:
    """Re-fetches KUCCPS's own cutoff document and flags any
    offering-university entry that may no longer be real. Never edits the
    catalog itself; only proposes flags for a human to review via the
    dismiss endpoint below or the existing PUT /api/admin/programmes/{id}.
    Shared by the admin-triggered endpoint and the weekly scheduled job
    (see _start_scheduler below) so the two never disagree on behaviour -
    the schedule only decides *when* this runs, never what it's allowed to
    do; both paths only ever write proposal flags, same as before."""
    db = get_db()
    if db is None:
        raise RuntimeError("Firestore is not configured on the server.")

    flags = check_catalogue_freshness()

    existing_open = {
        (doc.get("programmeId"), doc.get("universityName"))
        for doc in db.collection("catalogue_flags").where("status", "==", "open").stream()
    }

    new_count = 0
    for flag in flags:
        key = (flag["programmeId"], flag["universityName"])
        if key in existing_open:
            continue  # already flagged and still unresolved - don't duplicate
        db.collection("catalogue_flags").document().set(
            {**flag, "status": "open", "detectedAt": fb_firestore.SERVER_TIMESTAMP}
        )
        new_count += 1

    db.collection("audit_logs").document().set(
        {
            "action": "Catalogue Freshness Check Run",
            "actor": actor,
            "details": f"Checked {len(PROGRAMMES)} programmes against KUCCPS; {len(flags)} potential issues found, {new_count} newly flagged.",
            "timestamp": fb_firestore.SERVER_TIMESTAMP,
        }
    )

    return {"checked_programmes": len(PROGRAMMES), "total_flags_found": len(flags), "newly_flagged": new_count}


@app.post("/api/admin/catalogue-freshness/check")
def run_catalogue_freshness_check(decoded: dict = Depends(require_admin)):
    """Admin-triggered, on-demand version of the same check the scheduler
    runs weekly (see _start_scheduler) - kept for an admin who wants an
    immediate result rather than waiting for the next scheduled run."""
    try:
        return _run_catalogue_freshness_check_and_flag(actor=decoded.get("email") or decoded["uid"])
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not complete the freshness check: {e}")


@app.get("/api/admin/catalogue-freshness/flags")
def list_catalogue_freshness_flags(decoded: dict = Depends(require_admin)):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Firestore is not configured on the server.")
    query = db.collection("catalogue_flags").where("status", "==", "open").order_by(
        "detectedAt", direction=fb_firestore.Query.DESCENDING
    )
    flags = []
    for doc in query.stream():
        entry = doc.to_dict()
        entry["id"] = doc.id
        detected_at = entry.get("detectedAt")
        entry["detectedAt"] = detected_at.isoformat() if hasattr(detected_at, "isoformat") else str(detected_at)
        flags.append(entry)
    return flags


@app.post("/api/admin/catalogue-freshness/flags/{flag_id}/dismiss")
def dismiss_catalogue_freshness_flag(flag_id: str, decoded: dict = Depends(require_admin)):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Firestore is not configured on the server.")
    doc_ref = db.collection("catalogue_flags").document(flag_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="Unknown flag id.")

    doc_ref.update(
        {
            "status": "dismissed",
            "dismissedBy": decoded.get("email") or decoded["uid"],
            "dismissedAt": fb_firestore.SERVER_TIMESTAMP,
        }
    )
    db.collection("audit_logs").document().set(
        {
            "action": "Catalogue Freshness Flag Dismissed",
            "actor": decoded.get("email") or decoded["uid"],
            "details": f"Dismissed flag {flag_id}",
            "timestamp": fb_firestore.SERVER_TIMESTAMP,
        }
    )
    return {"status": "dismissed"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
