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

import hashlib
import json
import logging
import os
import subprocess
import sys
import threading
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import numpy as np
import joblib
import pandas as pd
import shap
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from firebase_admin import firestore as fb_firestore
from pydantic import BaseModel, field_validator

from analytics import build_overview
from analytics import day_of as _utc_day
from model_store import ensure_model
from firebase_setup import admin_emails, delete_auth_user, get_db, init_firebase, verify_id_token
from kuccps import (
    COMPULSORY_SUBJECTS,
    FEATURE_COLUMN,
    GRADE_POINTS,
    ML_FEATURE_SUBJECTS,
    UNDECIDED_ASPIRATION,
    aggregate_points,
    cluster_weighted_points,
    eligibility_status,
    university_cutoff_summary,
    cutoff_tier,
    extract_ml_feature_points,
    find_grade_for_subject,
    grade_to_points,
    meets_minimum_requirements,
    points_to_grade,
    unmet_requirements,
    raw_cluster_points,
)
from programmes_catalog import CATALOG_BY_ID as _STATIC_CATALOG_BY_ID
from programmes_catalog import PROGRAMMES
from synthetic_data_generator import ASPIRATION_MAP, FALLBACK_ORDER, TRAIT_COLUMN_INFO, build_cluster_score_features, build_trait_features
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


# Browsers only run the web admin portal from these addresses (the phone app is not
# a browser, so it is unaffected). Set CORS_ORIGINS="https://admin.example.com,..."
# in backend/.env when the portal is hosted somewhere else.
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "http://localhost:5000,http://127.0.0.1:5000").split(",")
    if origin.strip()
]

app = FastAPI(
    title="UniGuide REST API",
    description="Machine Learning Decision Support Backend for Kenyan Form-Four Leavers",
    version="1.0.0",
    lifespan=_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,  # requests carry a bearer token in a header, never cookies
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def _validation_exception_handler(request, exc: RequestValidationError):
    """FastAPI's default 422 body is a list of structured error objects -
    useful for API debugging, but every other error response in this app
    (HTTPException everywhere else) is a plain {"detail": "<message>"}
    string, which is what the Flutter side's ApiService._errorFor expects
    and what IR-06 asks for ("standardized, user-friendly error responses").
    Reformats Pydantic's validation errors (including the StudentProfile
    Payload grade validators above) into that same shape instead of adding
    a special case on the client for this one endpoint family."""
    messages = []
    for error in exc.errors():
        msg = error.get("msg", "Invalid input")
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        messages.append(msg)
    return JSONResponse(status_code=422, content={"detail": "; ".join(messages) or "Invalid request data."})


# ---------------------------------------------------------------------------
# Live catalogue cache
# ---------------------------------------------------------------------------
# CATALOG_BY_ID/CATALOG_BY_TITLE used to just be the static, process-startup
# dicts from programmes_catalog.py - meaning an admin's PUT
# /api/admin/programmes/{id} edit updated Firestore (and so the student
# browse catalogue via /api/programmes) but get_recommendations() kept using
# the original hardcoded values forever, since it read these same static
# dicts directly. These are now live, mutable dicts refreshed from Firestore
# (falling back to the static catalog for anything Firestore doesn't have)
# so an admin's edit reaches the actual recommendation engine too. Kept
# under the same names so every existing call site - get_recommendations,
# select_recommended_indices, _persist_recommendation, the test suite's
# main.CATALOG_BY_TITLE references - needs no changes.
CATALOG_BY_ID: Dict[str, dict] = {}
CATALOG_BY_TITLE: Dict[str, dict] = {}


def _load_live_catalog() -> None:
    db = get_db()
    merged: Dict[str, dict] = dict(_STATIC_CATALOG_BY_ID)
    if db is not None:
        try:
            docs = {d.id: d.to_dict() for d in db.collection("programmes").stream()}
            missing = [pid for pid in merged if pid not in docs]
            if missing:
                # Firestore only has a partial set (e.g. an admin edit lazily
                # created just the one programme they touched) - backfill the
                # rest from the static catalog instead of silently serving an
                # incomplete collection to anything reading Firestore directly.
                batch = db.batch()
                for pid in missing:
                    batch.set(db.collection("programmes").document(pid), merged[pid])
                batch.commit()
            merged.update(docs)
        except Exception:
            logger.exception("Failed reading live programmes from Firestore; using static catalog.")
    CATALOG_BY_ID.clear()
    CATALOG_BY_ID.update(merged)
    CATALOG_BY_TITLE.clear()
    CATALOG_BY_TITLE.update({p["title"]: p for p in CATALOG_BY_ID.values()})


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------
MODEL_PATH = os.path.join(os.path.dirname(__file__), "rf_model_pipeline.pkl")
_pipeline = None
_explainer = None


def _load_model() -> None:
    global _pipeline, _explainer
    ensure_model(MODEL_PATH, os.environ.get("MODEL_URL"), os.environ.get("MODEL_SHA256"), os.environ.get("MODEL_TOKEN"))
    if not os.path.isfile(MODEL_PATH):
        logger.warning(
            "rf_model_pipeline.pkl not found at %s. Run `python train_random_forest.py` "
            "in backend/ before calling /api/recommend.", MODEL_PATH,
        )
        return
    # joblib.load reads both the older plain-pickle file and the compressed one
    # that train_random_forest.py now writes, so an existing model keeps working.
    _pipeline = joblib.load(MODEL_PATH)
    _explainer = shap.TreeExplainer(_pipeline.named_steps["classifier"])
    logger.info("Random Forest pipeline and SHAP explainer loaded (%d classes).", len(_pipeline.classes_))


def model_version() -> str:
    """Identifies the model that produced a result. Training writes a version into
    model_metrics.json; a model trained before that existed falls back to the date
    its file was last written, so every result still says which model made it."""
    try:
        with open(METRICS_PATH, encoding="utf-8") as f:
            recorded = json.load(f).get("model_version")
        if recorded:
            return str(recorded)
    except (OSError, ValueError):
        pass
    try:
        return "rf-" + datetime.fromtimestamp(os.path.getmtime(MODEL_PATH), timezone.utc).strftime("%Y%m%d")
    except OSError:
        return "unknown"


# ---------------------------------------------------------------------------
# Model retrain/rollback (admin-triggered)
# ---------------------------------------------------------------------------
TRAIN_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "train_random_forest.py")
MODEL_BACKUPS_DIR = os.path.join(os.path.dirname(__file__), "model_backups")
METRICS_PATH = os.path.join(os.path.dirname(__file__), "model_metrics.json")

# In-memory only (single-process FYP scope, not Firestore-backed) - a
# retrain genuinely in progress is always tied to this one running server
# process anyway, so there's nothing meaningful to persist across restarts.
_training_status: Dict[str, Optional[str]] = {
    "running": False, "startedAt": None, "finishedAt": None, "lastError": None,
}


def _run_retrain_subprocess(actor: str) -> None:
    """Runs train_random_forest.py as a genuinely separate OS process (not
    a thread in this one) - this machine's available RAM is tight enough
    that a second full-parallelism model fit sharing memory with the
    already-running live server risked an out-of-memory failure (observed
    directly during development). TRAIN_N_JOBS=2 caps the child's own
    parallelism further for the same reason. If the child process OOMs or
    crashes, this server keeps serving the model it already has loaded -
    it never shares the crash."""
    db = get_db()
    try:
        env = {**os.environ, "TRAIN_N_JOBS": "2"}
        result = subprocess.run(
            [sys.executable, TRAIN_SCRIPT_PATH],
            cwd=os.path.dirname(__file__),
            env=env,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 min ceiling - well above the ~1-5 min this normally takes
        )
        if result.returncode != 0:
            raise RuntimeError(f"train_random_forest.py exited {result.returncode}: {result.stderr[-2000:]}")
        _load_model()  # hot-reload the freshly-trained pipeline into this process
        _training_status["lastError"] = None
        if db is not None:
            db.collection("audit_logs").document().set({
                "action": "Model Retrained",
                "actor": actor,
                "details": "Retrain completed successfully; new model hot-reloaded.",
                "timestamp": fb_firestore.SERVER_TIMESTAMP,
            })
    except Exception as e:
        logger.exception("Admin-triggered retrain failed.")
        _training_status["lastError"] = str(e)
        if db is not None:
            db.collection("audit_logs").document().set({
                "action": "Model Retrain Failed",
                "actor": actor,
                "details": str(e)[:500],
                "timestamp": fb_firestore.SERVER_TIMESTAMP,
            })
    finally:
        _training_status["running"] = False
        _training_status["finishedAt"] = datetime.now(timezone.utc).isoformat()


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
_load_live_catalog()

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

    # DR-05 (Data Validation & Preprocessing): invalid or incomplete academic
    # records must not be processed for a recommendation. Before this,
    # grade_to_points() silently defaulted any unrecognized grade string to
    # "C+" rather than rejecting it - a malformed or tampered grade would
    # quietly generate a real recommendation off a value the student never
    # actually entered, with no indication anything was wrong. Validating
    # here, at the request boundary, means a bad request is refused outright
    # (FastAPI returns 422) instead of silently substituted and processed.
    @field_validator("kcseMeanGrade")
    @classmethod
    def _validate_mean_grade(cls, v: str) -> str:
        if v.strip().upper() not in GRADE_POINTS:
            raise ValueError(f"'{v}' is not a real KCSE grade (A, A-, B+, ... down to E).")
        return v

    @field_validator("grades")
    @classmethod
    def _validate_grades(cls, v: Dict[str, str]) -> Dict[str, str]:
        invalid = [f"{subject}={grade!r}" for subject, grade in v.items() if grade.strip().upper() not in GRADE_POINTS]
        if invalid:
            raise ValueError(f"These aren't real KCSE grades: {', '.join(invalid)}.")
        missing = [s for s in COMPULSORY_SUBJECTS if s not in v]
        if missing:
            raise ValueError(
                f"Missing grade(s) for compulsory subject(s): {', '.join(missing)}. "
                f"All {len(COMPULSORY_SUBJECTS)} compulsory subjects must be provided: {', '.join(COMPULSORY_SUBJECTS)}."
            )
        return v


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



class UniversityCutoffPayload(BaseModel):
    """One university's cutoff points for a programme (latest and previous year).
    KUCCPS cluster points run from 0 to 48, so anything outside that is a typo."""
    latestCutoff: float
    previousCutoff: float

    @field_validator("latestCutoff", "previousCutoff")
    @classmethod
    def _within_cluster_point_scale(cls, v: float) -> float:
        if not (0 < v <= 48):
            raise ValueError("Cutoff points must be between 0 and 48 (the KUCCPS cluster points scale).")
        return v

class AdminInvitePayload(BaseModel):
    email: str


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


def rate_limited_user(decoded: dict = Depends(require_auth)) -> dict:
    check_rate_limit(decoded["uid"])
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
# Abuse protection: request size, request rate, repeated submissions
# ---------------------------------------------------------------------------
MAX_BODY_BYTES = 64 * 1024  # a full profile is a few KB; anything this large is not one
RATE_LIMIT_REQUESTS = int(os.environ.get("RATE_LIMIT_REQUESTS", "30"))
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))
DUPLICATE_WINDOW_SECONDS = 10

_recent_requests: Dict[str, deque] = defaultdict(deque)
_last_submission: Dict[str, tuple] = {}


@app.middleware("http")
async def _reject_oversized_bodies(request: Request, call_next):
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > MAX_BODY_BYTES:
        return JSONResponse(status_code=413, content={"detail": "That request is too large."})
    return await call_next(request)


def check_rate_limit(key: str, now: Optional[float] = None) -> None:
    """Allows RATE_LIMIT_REQUESTS per signed-in user per window; raises 429 beyond that.
    Kept in this process's memory, which is enough for a single-server deployment."""
    now = time.monotonic() if now is None else now
    window = _recent_requests[key]
    while window and now - window[0] > RATE_LIMIT_WINDOW_SECONDS:
        window.popleft()
    if len(window) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(status_code=429, detail="You are doing that too quickly. Please wait a minute and try again.")
    window.append(now)


def _is_duplicate_submission(uid: str, payload: StudentProfilePayload, now: Optional[float] = None) -> bool:
    """True when this exact profile was already saved moments ago (a double tap or a
    retry after a dropped connection), so the history gets one record, not two."""
    now = time.monotonic() if now is None else now
    fingerprint = hashlib.sha256(payload.model_dump_json().encode()).hexdigest()
    previous = _last_submission.get(uid)
    _last_submission[uid] = (fingerprint, now)
    return previous is not None and previous[0] == fingerprint and now - previous[1] < DUPLICATE_WINDOW_SECONDS


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
    row["aspiration"] = payload.aspirations[0] if payload.aspirations else UNDECIDED_ASPIRATION
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
            # BUG (found during NFR-03 performance investigation, Section
            # 5.7): one-hot encoding turns a single categorical column
            # (e.g. "aspiration") into one dummy feature PER POSSIBLE
            # VALUE, and SHAP attributes a value to every one of them, not
            # just the one the student actually selected. This branch used
            # to label ALL of them as "Aspiration: <value>" and claim "Your
            # stated aspiration of <value>..." unconditionally - so an
            # explanation could (and, confirmed by direct testing, did)
            # name an aspiration the student never chose as the reason for
            # a recommendation. Fixed to check the real stated value
            # (row[col], the raw pre-one-hot-encoding string) and only
            # claim it was selected when it actually was, mirroring the
            # TRAIT_COLUMN_INFO branch above.
            selected = row.get(col) == value
            if selected and value == UNDECIDED_ASPIRATION:
                feature_name = "Career choice: not sure yet"
                desc = "You have not picked a career yet, so your grades, interests and skills decide this result."
            elif selected:
                feature_name = f"{word}: {value}"
                desc = f"Your stated {word.lower()} of '{value}' relates to this programme's profile."
            else:
                feature_name = f"Not {word.lower()}: {value}"
                desc = f"Your stated {word.lower()} is not '{value}'."
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
            "rawName": str(feature_names[idx]),
            "featureName": feature_name,
            "category": category,
            "shapValue": round(value, 4),
            "description": desc,
        })
    return explanations


def build_plain_reasons(shap_list, row: dict, programme: dict, grades: Dict[str, str], mean_grade: str, max_reasons: int = 3):
    """Turns the factors that actually pushed a result UP (positive SHAP values)
    into plain sentences a student can read. Nothing is invented: every sentence
    comes from a real top factor, and a subject the student did not sit is never
    described as if they had a grade in it."""
    reasons = []
    requirements = programme.get("minimumSubjectRequirements") or {}
    for entry in shap_list:
        if entry.get("shapValue", 0) <= 0:
            continue
        prefix, _, rest = str(entry.get("rawName", "")).partition("__")
        sentence = None
        if prefix == "num":
            if rest in TRAIT_COLUMN_INFO:
                if not row.get(rest):
                    continue
                _category, word, label = TRAIT_COLUMN_INFO[rest]
                if word == "Interest":
                    sentence = f"You said you are interested in {label}."
                elif word == "Skill":
                    sentence = f"You listed {label} as one of your skills."
                else:
                    sentence = f"{label} is one of the strengths you picked."
            elif rest == "mean_points":
                sentence = f"Your overall KCSE mean grade ({mean_grade}) supports this match."
            elif rest in NUMERIC_LABELS:
                subject = NUMERIC_LABELS[rest]
                grade = find_grade_for_subject(grades, subject)
                if grade is None:
                    continue  # not sat - no claim about a grade they do not have
                needed = requirements.get(subject)
                if needed and grade_to_points(grade) >= grade_to_points(needed):
                    sentence = f"Your {subject} grade ({grade}) meets the {needed} this programme asks for."
                else:
                    sentence = f"Your {subject} grade ({grade}) supports this match."
        else:
            for col in CATEGORY_INFO:
                if rest.startswith(f"{col}_"):
                    value = rest[len(col) + 1:]
                    if row.get(col) != value:
                        break  # a one-hot dummy for an option the student did not choose
                    if value == UNDECIDED_ASPIRATION:
                        sentence = "You have not picked a career yet, so this match is based on your grades, interests and skills."
                    else:
                        sentence = f"You picked {value} as a career you have in mind."
        if sentence and sentence not in reasons:
            reasons.append(sentence)
        if len(reasons) >= max_reasons:
            break
    return reasons or ["This programme fits the overall pattern of your grades and answers."]


def build_primary_reason(shap_list, title: str, confidence: float) -> str:
    # Deliberately no percentage in the text: students are not shown the
    # model's confidence figure (it is a probability spread over 53 programmes,
    # easy to misread as a "fit score"). `title`/`confidence` stay in the
    # signature so existing callers are unchanged.
    if shap_list:
        lead = shap_list[0]["featureName"]
        return f"Primarily driven by {lead}."
    return "Recommended based on your submitted profile."


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
            "modelVersion": results[0].get("modelVersion") if results else None,
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
        "model_version": model_version() if _pipeline is not None else None,
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
    # Serves the same live cache get_recommendations() now uses (see "Live
    # catalogue cache" above) - preserves the original catalog ordering.
    # Deactivated programmes are hidden from students entirely (not just
    # excluded from recommendations) - an admin "Admins" view that needs to
    # see inactive ones too uses GET /api/admin/programmes instead.
    return [
        CATALOG_BY_ID.get(p["id"], p) for p in PROGRAMMES
        if CATALOG_BY_ID.get(p["id"], p).get("status") != "inactive"
    ]


@app.get("/api/admin/programmes")
def list_all_programmes_for_admin(decoded: dict = Depends(require_admin)):
    """Same data as /api/programmes but WITHOUT hiding inactive programmes
    - the admin Catalog tab needs to show deactivated ones (greyed out,
    with a Reactivate action) rather than have them vanish entirely."""
    return [CATALOG_BY_ID.get(p["id"], p) for p in PROGRAMMES]


def select_recommended_indices(
    proba: np.ndarray, classes: np.ndarray, grades: Dict[str, str], mean_grade: str
) -> tuple:
    """Picks the three programmes to show: the best fit among the genuinely eligible
    programmes first, then the best two the student can reach, falling
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
    active_mask = [CATALOG_BY_TITLE.get(c, {}).get("status") != "inactive" for c in classes]
    eligible_mask = [
        active_mask[i] and meets_minimum_requirements(grades, CATALOG_BY_TITLE[c]["minimumSubjectRequirements"], mean_grade)
        for i, c in enumerate(classes)
    ]
    eligible_idx = [i for i in range(n_classes) if eligible_mask[i]]

    # Within the eligible programmes, prefer ones the student can realistically
    # get into: compare their points with EACH university's own latest cutoff
    # (cutoffs differ by university), then rank by model probability inside each
    # tier. A programme the model barely considers (probability under the
    # 1-in-53 chance level) never jumps ahead of one it does, whatever its tier.
    agg = aggregate_points(grades, mean_grade)

    def rank_key(i):
        programme = CATALOG_BY_TITLE[classes[i]]
        cwp = cluster_weighted_points(raw_cluster_points(grades, programme["clusterSubjects"], mean_grade), agg)
        summary = university_cutoff_summary(cwp, programme.get("offeringUniversities"), programme.get("averageCutoff"))
        tier = cutoff_tier(summary) + (3 if proba[i] < 0.02 else 0)
        return (tier, -proba[i])

    # The model's best fit is always shown first, even when it is a stretch (the app says so in
    # plain words). The other two places go to the best programmes the student can reach. Ranking
    # purely by reachability pushed good fits out of the three shown: on out-of-fold profiles the
    # labelled programme was shown 73% of the time, against 92% with this rule (Experiment 9).
    top_idx = []
    if eligible_idx:
        best_fit = max(eligible_idx, key=lambda i: proba[i])
        top_idx = [best_fit] + [i for i in sorted(eligible_idx, key=rank_key) if i != best_fit][:2]

    if len(top_idx) < 3:
        for title in FALLBACK_ORDER:
            if title not in classes or CATALOG_BY_TITLE.get(title, {}).get("status") == "inactive":
                continue
            idx = int(np.where(classes == title)[0][0])
            if idx not in top_idx:
                top_idx.append(idx)
            if len(top_idx) == 3:
                break
    return top_idx, eligible_mask


@app.post("/api/recommend")
def get_recommendations(payload: StudentProfilePayload, decoded: dict = Depends(rate_limited_user), preview: bool = False):
    # preview=true is the "what if" simulator: it returns exactly what a real request would, but saves nothing,
    # so trying out different grades never fills the student's history or the admin analytics.
    if _pipeline is None or _explainer is None:
        raise HTTPException(
            status_code=503,
            detail="Recommendations are temporarily unavailable. Please try again later.",
        )

    uid = decoded["uid"]
    row_df, grades, mean_grade = profile_to_feature_row(payload)

    proba = _pipeline.predict_proba(row_df)[0]
    classes = _pipeline.classes_
    n_classes = len(classes)

    top_idx, eligible_mask = select_recommended_indices(proba, classes, grades, mean_grade)

    X_trans = _pipeline.named_steps["preprocessor"].transform(row_df)
    feature_names = _pipeline.named_steps["preprocessor"].get_feature_names_out()
    # approximate=True uses SHAP's Saabas algorithm instead of exact Shapley
    # values - a real performance defect was found during NFR-03 evaluation
    # (Chapter 5.4.2/5.7): exact TreeSHAP over 350 trees x 53 output classes
    # took ~37.6 seconds per request, which exceeds the Flutter client's own
    # 15-second request timeout (ApiService.getRecommendations) and would
    # fail every real request. The approximation is ~2000x faster (measured
    # ~19ms). It trades the exact efficiency-axiom guarantee (contributions
    # summing precisely to the prediction) for speed. CAVEAT: it is NOT
    # known to rank features identically to exact SHAP - in a direct
    # comparison on one profile the two methods' top-4 features differed
    # (exact SHAP's top features were dominated by "off" one-hot aspiration
    # dummies). Fidelity of the approximate explanations was only checked
    # against exact SHAP on a small sample - see Chapter 5.7.
    raw_shap = _explainer.shap_values(X_trans, check_additivity=False, approximate=True)
    row_values = row_df.iloc[0].to_dict()

    agg = aggregate_points(grades, mean_grade)
    version = model_version()

    results = []
    for rank, class_idx in enumerate(top_idx, start=1):
        title = classes[class_idx]
        programme = CATALOG_BY_TITLE.get(title)
        if programme is None:
            continue

        confidence = float(proba[class_idx])
        raw_cluster = raw_cluster_points(grades, programme["clusterSubjects"], mean_grade)
        cwp = cluster_weighted_points(raw_cluster, agg)
        uni_summary = university_cutoff_summary(cwp, programme.get("offeringUniversities"), programme.get("averageCutoff"))
        cutoff_diff = uni_summary["gap"] if uni_summary else round(cwp - programme["averageCutoff"], 1)

        class_shap = _extract_class_shap(raw_shap, class_idx, n_classes)[0]
        shap_list = top_shap_explanations(class_shap, feature_names, row_values)
        primary_reason = build_primary_reason(shap_list, title, confidence)
        plain_reasons = build_plain_reasons(shap_list, row_values, programme, grades, mean_grade)

        meets_requirements = eligible_mask[class_idx]

        results.append({
            "rank": rank,
            "confidenceScore": round(confidence, 3),
            "studentClusterScore": cwp,
            "cutoffDiff": cutoff_diff,
            "universityCutoffs": uni_summary,
            "eligibilityStatus": eligibility_status(cwp, programme["averageCutoff"], meets_requirements, uni_summary),
            "meetsMinimumRequirements": meets_requirements,
            "primaryReason": primary_reason,
            "plainReasons": plain_reasons,
            "programme": programme,
            "shapExplanations": shap_list,
            "modelVersion": version,
        })

    if not preview and not _is_duplicate_submission(uid, payload):
        _persist_recommendation(uid, decoded.get("email"), payload, results)
    return results


def programmes_missed_for_career(grades: Dict[str, str], careers: List[str]) -> list:
    """For each career the student named, the programmes that lead to it which the student cannot
    be admitted to yet, with the grades that are missing. Programmes the student does qualify for
    are left out, so an empty list means nothing is being held back."""
    notes = []
    for career in careers:
        for title in ASPIRATION_MAP.get(career, []):
            programme = CATALOG_BY_TITLE.get(title)
            if programme is None or programme.get("status") == "inactive":
                continue
            reasons = unmet_requirements(grades, programme.get("minimumSubjectRequirements") or {})
            if reasons:
                notes.append({"career": career, "programme": title, "reasons": reasons})
    return notes


@app.post("/api/career-note")
def career_note(payload: StudentProfilePayload, decoded: dict = Depends(rate_limited_user)):
    """Tells a student why a programme for the career they named is not among their results,
    in terms of the exact subject grades. Nothing is saved."""
    return programmes_missed_for_career(payload.grades or {}, payload.aspirations or [])


SHORTLIST_LIMIT = 30


def _shortlist_collection(db, uid: str):
    return db.collection("students").document(uid).collection("shortlist")


@app.get("/api/shortlist")
def get_shortlist(decoded: dict = Depends(require_auth)):
    """The student's saved programmes, oldest save first, as full programme
    records (deactivated programmes are left out)."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="This service is temporarily unavailable. Please try again later.")
    saved = []
    for doc in _shortlist_collection(db, decoded["uid"]).stream():
        saved_at = (doc.to_dict() or {}).get("savedAt")
        saved.append((saved_at.isoformat() if hasattr(saved_at, "isoformat") else str(saved_at), doc.id))
    saved.sort()
    result = []
    for _when, programme_id in saved:
        programme = CATALOG_BY_ID.get(programme_id)
        if programme is not None and programme.get("status") != "inactive":
            result.append(programme)
    return result


@app.post("/api/shortlist/{programme_id}")
def add_to_shortlist(programme_id: str, decoded: dict = Depends(require_auth)):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="This service is temporarily unavailable. Please try again later.")
    programme = CATALOG_BY_ID.get(programme_id)
    if programme is None or programme.get("status") == "inactive":
        raise HTTPException(status_code=404, detail="That programme could not be found.")
    collection = _shortlist_collection(db, decoded["uid"])
    ref = collection.document(programme_id)
    if not ref.get().exists:
        if sum(1 for _ in collection.stream()) >= SHORTLIST_LIMIT:
            raise HTTPException(status_code=409, detail=f"You can save up to {SHORTLIST_LIMIT} programmes. Remove one to add another.")
        ref.set({"savedAt": fb_firestore.SERVER_TIMESTAMP})
    return {"saved": True, "programmeId": programme_id}


@app.delete("/api/shortlist/{programme_id}")
def remove_from_shortlist(programme_id: str, decoded: dict = Depends(require_auth)):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="This service is temporarily unavailable. Please try again later.")
    _shortlist_collection(db, decoded["uid"]).document(programme_id).delete()
    return {"saved": False, "programmeId": programme_id}


@app.post("/api/feedback")
def submit_feedback(feedback: FeedbackPayload, decoded: dict = Depends(require_auth)):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="This service is temporarily unavailable. Please try again later.")
    uid = decoded["uid"]
    doc_ref = db.collection("students").document(uid).collection("feedback").document()
    doc_ref.set({
        "recommendationId": feedback.recommendation_id,
        "rating": feedback.rating,
        "comments": feedback.comments,
        "submittedAt": fb_firestore.SERVER_TIMESTAMP,
    })
    return {"status": "success", "feedback_id": doc_ref.id}


STUDENT_SUBCOLLECTIONS = ("recommendations", "shortlist", "feedback")


class DeleteAccountPayload(BaseModel):
    confirm: str = ""


def delete_student_data(db, uid: str) -> None:
    """Removes everything stored about one student: their recommendations, saved
    programmes, feedback and profile."""
    student_ref = db.collection("students").document(uid)
    for name in STUDENT_SUBCOLLECTIONS:
        collection = student_ref.collection(name)
        for snap in list(collection.stream()):
            collection.document(snap.id).delete()
    student_ref.delete()


@app.delete("/api/me")
def delete_my_account(body: DeleteAccountPayload, decoded: dict = Depends(rate_limited_user)):
    """The student deletes their own account and all data stored about them.
    The body must say {"confirm": "DELETE"} so a stray request cannot do it."""
    if body.confirm != "DELETE":
        raise HTTPException(status_code=400, detail='To delete your account, confirm by sending "DELETE".')
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="This service is temporarily unavailable. Please try again later.")
    uid = decoded["uid"]
    if (decoded.get("email") or "").lower() in admin_emails() or db.collection("admins").document(uid).get().exists:
        raise HTTPException(status_code=403, detail="Administrator accounts are removed by another administrator, not here.")
    delete_student_data(db, uid)
    delete_auth_user(uid)
    # The log keeps only that a deletion happened, never who the student was.
    db.collection("audit_logs").document().set({
        "action": "Student Account Deleted",
        "actor": "Student (self-service)",
        "details": "A student deleted their account and stored data.",
        "timestamp": fb_firestore.SERVER_TIMESTAMP,
    })
    return {"deleted": True}


@app.put("/api/admin/programmes/{programme_id}")
def update_programme(programme_id: str, body: ProgrammeUpdatePayload, decoded: dict = Depends(require_admin)):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="This service is temporarily unavailable. Please try again later.")
    if programme_id not in CATALOG_BY_ID:
        raise HTTPException(status_code=404, detail="Unknown programme id.")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update were provided.")

    doc_ref = db.collection("programmes").document(programme_id)
    if not doc_ref.get().exists:
        doc_ref.set(CATALOG_BY_ID[programme_id])
    doc_ref.update(updates)
    _load_live_catalog()  # so get_recommendations() reflects this edit immediately, not just /api/programmes

    change_summary = ", ".join(f"{field}={value!r}" for field, value in updates.items())
    db.collection("audit_logs").document().set({
        "action": "Programme Information Updated",
        "actor": decoded.get("email") or decoded["uid"],
        "details": f"Updated {programme_id}: {change_summary}",
        "timestamp": fb_firestore.SERVER_TIMESTAMP,
    })

    return doc_ref.get().to_dict()


@app.put("/api/admin/programmes/{programme_id}/universities/{kuccps_code}")
def update_university_cutoff(
    programme_id: str, kuccps_code: str, body: UniversityCutoffPayload, decoded: dict = Depends(require_admin)
):
    """Edits one university's cutoff for a programme. This is the figure students
    are actually compared with (each university has its own cutoff), so an edit
    here reaches the very next recommendation. Recorded in the audit log."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="This service is temporarily unavailable. Please try again later.")
    programme = CATALOG_BY_ID.get(programme_id)
    if programme is None:
        raise HTTPException(status_code=404, detail="Unknown programme id.")

    offerings = [dict(u) for u in programme["offeringUniversities"]]
    target = next((u for u in offerings if str(u["kuccpsCode"]) == kuccps_code), None)
    if target is None:
        raise HTTPException(status_code=404, detail="That university is not listed for this programme.")

    before = (target["latestCutoff"], target["previousCutoff"])
    target["latestCutoff"] = round(body.latestCutoff, 3)
    target["previousCutoff"] = round(body.previousCutoff, 3)

    doc_ref = db.collection("programmes").document(programme_id)
    if not doc_ref.get().exists:
        doc_ref.set(CATALOG_BY_ID[programme_id])
    doc_ref.update({"offeringUniversities": offerings})
    _load_live_catalog()

    db.collection("audit_logs").document().set({
        "action": "University Cutoff Updated",
        "actor": decoded.get("email") or decoded["uid"],
        "details": (
            f"{programme['title']} at {target['universityName']} ({kuccps_code}): "
            f"latest {before[0]} -> {target['latestCutoff']}, previous {before[1]} -> {target['previousCutoff']}"
        ),
        "timestamp": fb_firestore.SERVER_TIMESTAMP,
    })
    return CATALOG_BY_ID[programme_id]


def _set_programme_status(programme_id: str, status: Optional[str], decoded: dict, action: str) -> dict:
    """Shared by deactivate/reactivate below - status=None means active
    (the field is simply absent/cleared), "inactive" means hidden from
    students and never selected by get_recommendations(). A soft toggle,
    never a hard delete, so it's reversible and doesn't orphan any
    historical recommendation record that already references this id."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="This service is temporarily unavailable. Please try again later.")
    if programme_id not in CATALOG_BY_ID:
        raise HTTPException(status_code=404, detail="Unknown programme id.")

    doc_ref = db.collection("programmes").document(programme_id)
    if not doc_ref.get().exists:
        doc_ref.set(CATALOG_BY_ID[programme_id])
    if status is None:
        doc_ref.update({"status": fb_firestore.DELETE_FIELD})
    else:
        doc_ref.update({"status": status})
    _load_live_catalog()

    db.collection("audit_logs").document().set({
        "action": action,
        "actor": decoded.get("email") or decoded["uid"],
        "details": f"{action}: {programme_id} ({CATALOG_BY_ID[programme_id]['title']})",
        "timestamp": fb_firestore.SERVER_TIMESTAMP,
    })
    return CATALOG_BY_ID[programme_id]


@app.post("/api/admin/programmes/{programme_id}/deactivate")
def deactivate_programme(programme_id: str, decoded: dict = Depends(require_admin)):
    return _set_programme_status(programme_id, "inactive", decoded, "Programme Deactivated")


@app.post("/api/admin/programmes/{programme_id}/reactivate")
def reactivate_programme(programme_id: str, decoded: dict = Depends(require_admin)):
    return _set_programme_status(programme_id, None, decoded, "Programme Reactivated")


@app.get("/api/admin/audit-logs")
def list_audit_logs(decoded: dict = Depends(require_admin)):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="This service is temporarily unavailable. Please try again later.")
    query = db.collection("audit_logs").order_by("timestamp", direction=fb_firestore.Query.DESCENDING).limit(25)
    logs = []
    for doc in query.stream():
        entry = doc.to_dict()
        entry["id"] = doc.id
        timestamp = entry.get("timestamp")
        entry["timestamp"] = timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
        logs.append(entry)
    return logs


@app.get("/api/admin/admins")
def list_admins(decoded: dict = Depends(require_admin)):
    """Lists only the Firestore-managed admins (the `admins` collection
    require_admin already checks) - the ADMIN_EMAILS env var is a separate,
    bootstrap allowlist that can't be edited at runtime and deliberately
    isn't shown/removable here, so there's always at least one admin who
    can never be locked out via this UI."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="This service is temporarily unavailable. Please try again later.")
    admins = []
    for doc in db.collection("admins").stream():
        entry = doc.to_dict()
        entry["uid"] = doc.id
        added_at = entry.get("addedAt")
        entry["addedAt"] = added_at.isoformat() if hasattr(added_at, "isoformat") else str(added_at)
        admins.append(entry)
    return admins


@app.post("/api/admin/admins")
def add_admin(body: AdminInvitePayload, decoded: dict = Depends(require_admin)):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="This service is temporarily unavailable. Please try again later.")

    from firebase_admin import auth as fb_auth

    try:
        user = fb_auth.get_user_by_email(body.email.strip().lower())
    except fb_auth.UserNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="No account with that email has signed up yet - they must create an account first.",
        )

    db.collection("admins").document(user.uid).set({
        "email": user.email,
        "addedBy": decoded.get("email") or decoded["uid"],
        "addedAt": fb_firestore.SERVER_TIMESTAMP,
    })
    db.collection("audit_logs").document().set({
        "action": "Administrator Added",
        "actor": decoded.get("email") or decoded["uid"],
        "details": f"Granted admin access to {user.email}",
        "timestamp": fb_firestore.SERVER_TIMESTAMP,
    })
    return {"uid": user.uid, "email": user.email}


@app.delete("/api/admin/admins/{uid}")
def remove_admin(uid: str, decoded: dict = Depends(require_admin)):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="This service is temporarily unavailable. Please try again later.")
    doc_ref = db.collection("admins").document(uid)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="That admin entry doesn't exist (they may only have access via ADMIN_EMAILS).")
    removed_email = doc.to_dict().get("email", uid)
    doc_ref.delete()
    db.collection("audit_logs").document().set({
        "action": "Administrator Removed",
        "actor": decoded.get("email") or decoded["uid"],
        "details": f"Revoked admin access from {removed_email}",
        "timestamp": fb_firestore.SERVER_TIMESTAMP,
    })
    return {"status": "removed"}


@app.post("/api/admin/model/retrain")
def trigger_retrain(decoded: dict = Depends(require_admin)):
    if _training_status["running"]:
        raise HTTPException(status_code=409, detail="A retrain is already in progress.")
    _training_status["running"] = True
    _training_status["startedAt"] = datetime.now(timezone.utc).isoformat()
    _training_status["lastError"] = None
    actor = decoded.get("email") or decoded["uid"]
    threading.Thread(target=_run_retrain_subprocess, args=(actor,), daemon=True).start()
    return {"started": True}


@app.get("/api/admin/model/status")
def model_training_status(decoded: dict = Depends(require_admin)):
    return dict(_training_status)


@app.get("/api/admin/model/backups")
def list_model_backups(decoded: dict = Depends(require_admin)):
    if not os.path.isdir(MODEL_BACKUPS_DIR):
        return []
    backups = []
    for fname in os.listdir(MODEL_BACKUPS_DIR):
        if not fname.startswith("rf_model_pipeline_") or not fname.endswith(".pkl"):
            continue
        timestamp = fname[len("rf_model_pipeline_"):-len(".pkl")]
        entry = {"timestamp": timestamp}
        metrics_path = os.path.join(MODEL_BACKUPS_DIR, f"model_metrics_{timestamp}.json")
        if os.path.isfile(metrics_path):
            try:
                import json
                with open(metrics_path) as f:
                    metrics = json.load(f)
                entry["accuracy"] = metrics.get("accuracy")
                entry["weightedF1"] = metrics.get("weighted_f1")
                entry["nClasses"] = metrics.get("n_classes")
            except Exception:
                pass
        backups.append(entry)
    backups.sort(key=lambda b: b["timestamp"], reverse=True)
    return backups


class ModelRestorePayload(BaseModel):
    timestamp: str


@app.post("/api/admin/model/restore")
def restore_model_backup(body: ModelRestorePayload, decoded: dict = Depends(require_admin)):
    import shutil

    if _training_status["running"]:
        raise HTTPException(status_code=409, detail="A retrain is already in progress.")

    backup_pkl = os.path.join(MODEL_BACKUPS_DIR, f"rf_model_pipeline_{body.timestamp}.pkl")
    backup_metrics = os.path.join(MODEL_BACKUPS_DIR, f"model_metrics_{body.timestamp}.json")
    if not os.path.isfile(backup_pkl):
        raise HTTPException(status_code=404, detail="No backup with that timestamp exists.")

    db = get_db()
    # Back up the CURRENT model before overwriting it, same as every normal
    # retrain already does - a restore is itself reversible, never a
    # one-way trip.
    if os.path.isfile(MODEL_PATH):
        os.makedirs(MODEL_BACKUPS_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy(MODEL_PATH, os.path.join(MODEL_BACKUPS_DIR, f"rf_model_pipeline_{stamp}.pkl"))
        if os.path.isfile(METRICS_PATH):
            shutil.copy(METRICS_PATH, os.path.join(MODEL_BACKUPS_DIR, f"model_metrics_{stamp}.json"))

    shutil.copy(backup_pkl, MODEL_PATH)
    if os.path.isfile(backup_metrics):
        shutil.copy(backup_metrics, METRICS_PATH)
    _load_model()

    if db is not None:
        db.collection("audit_logs").document().set({
            "action": "Model Restored",
            "actor": decoded.get("email") or decoded["uid"],
            "details": f"Restored model backup from {body.timestamp}",
            "timestamp": fb_firestore.SERVER_TIMESTAMP,
        })
    return {"restored": body.timestamp}


@app.get("/api/admin/feedback")
def list_feedback(decoded: dict = Depends(require_admin)):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="This service is temporarily unavailable. Please try again later.")

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


@app.get("/api/admin/analytics/activity")
def activity_analytics(days: int = 30, decoded: dict = Depends(require_admin)):
    """Recommendations, feedback and new students per day for the last `days` days,
    plus all-time totals. Counted in Python after plain scans, so no Firestore
    composite index is needed."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="This service is temporarily unavailable. Please try again later.")
    days = max(7, min(days, 90))
    today = datetime.now(timezone.utc).date()
    buckets = {}
    for offset in range(days - 1, -1, -1):
        day = (today - timedelta(days=offset)).isoformat()
        buckets[day] = {"date": day, "recommendations": 0, "feedback": 0, "newStudents": 0}

    totals = {"students": 0, "recommendations": 0, "feedback": 0, "averageRating": None}
    ratings = []

    for doc in db.collection_group("recommendations").stream():
        totals["recommendations"] += 1
        day = _utc_day((doc.to_dict() or {}).get("createdAt"))
        if day in buckets:
            buckets[day]["recommendations"] += 1
    for doc in db.collection_group("feedback").stream():
        entry = doc.to_dict() or {}
        totals["feedback"] += 1
        if isinstance(entry.get("rating"), (int, float)) and entry["rating"] > 0:
            ratings.append(entry["rating"])
        day = _utc_day(entry.get("submittedAt"))
        if day in buckets:
            buckets[day]["feedback"] += 1
    for doc in db.collection("students").stream():
        totals["students"] += 1
        day = _utc_day((doc.to_dict() or {}).get("createdAt"))
        if day in buckets:
            buckets[day]["newStudents"] += 1

    if ratings:
        totals["averageRating"] = round(sum(ratings) / len(ratings), 2)
    return {"days": list(buckets.values()), "totals": totals}


@app.get("/api/admin/analytics/overview")
def analytics_overview(decoded: dict = Depends(require_admin)):
    """Counts for the admin Insights page: users and growth, activity, how far students
    get, who they are (grade bands, decided or not), what they were shown and what they
    saved. Plain scans with the counting done in Python, so no Firestore index is needed;
    only totals leave the server, never a student's name, email or grades."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="This service is temporarily unavailable. Please try again later.")

    def owner(doc) -> str:
        return doc.reference.parent.parent.id

    students = []
    for doc in db.collection("students").stream():
        data = doc.to_dict() or {}
        students.append({
            "uid": doc.id,
            "createdAt": data.get("createdAt"),
            "kcseMeanGrade": data.get("kcseMeanGrade"),
            "aspirations": data.get("aspirations") or [],
        })
    recommendations = []
    for doc in db.collection_group("recommendations").stream():
        data = doc.to_dict() or {}
        recommendations.append({"uid": owner(doc), "createdAt": data.get("createdAt"), "items": data.get("recommendations") or []})
    feedback = [{"uid": owner(doc), "rating": (doc.to_dict() or {}).get("rating")} for doc in db.collection_group("feedback").stream()]
    saved = [{"uid": owner(doc), "programmeId": doc.id} for doc in db.collection_group("shortlist").stream()]
    titles = {pid: programme["title"] for pid, programme in CATALOG_BY_ID.items()}
    return build_overview(students, recommendations, feedback, saved, titles)


@app.get("/api/admin/analytics/programme-popularity")
def programme_popularity(decoded: dict = Depends(require_admin)):
    """Tallies how often each trained programme has appeared in a Top-3
    recommendation, across every student's students/{uid}/recommendations
    subcollection (written by _persist_recommendation). Aggregation is done
    in Python after a plain unfiltered collection_group() scan - no
    where()/order_by() on it - so this needs no composite Firestore index.
    Returns the 5 most and 5 least recommended among the 53 trained
    programmes (zero-count ones included in "least", since "never
    recommended" is itself a meaningful signal for an admin to see)."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="This service is temporarily unavailable. Please try again later.")

    counts: Dict[str, int] = {title: 0 for title in CATALOG_BY_TITLE}
    for doc in db.collection_group("recommendations").stream():
        for item in (doc.to_dict().get("recommendations") or []):
            title = (item.get("programme") or {}).get("title")
            if title in counts:
                counts[title] += 1

    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    most = [{"title": t, "count": c} for t, c in ranked[:5]]
    least = [{"title": t, "count": c} for t, c in ranked[-5:]][::-1]
    return {"mostRecommended": most, "leastRecommended": least}


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
    # Separate from audit_logs so the dashboard can show "last checked: X"
    # and a clean run-by-run history without mixing it into the general
    # admin activity feed - this is what actually proves the weekly
    # scheduler (see _start_scheduler) is running over time, not just that
    # it registered once at startup.
    db.collection("catalogue_freshness_runs").document().set({
        "runAt": fb_firestore.SERVER_TIMESTAMP,
        "actor": actor,
        "checkedProgrammes": len(PROGRAMMES),
        "totalFlagsFound": len(flags),
        "newlyFlagged": new_count,
    })

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
        raise HTTPException(status_code=503, detail="This service is temporarily unavailable. Please try again later.")
    # Filter by status only and sort in Python: combining where("status") with
    # order_by("detectedAt") makes Firestore demand a composite index that has
    # to be created by hand in the Firebase console, and the list failed with a
    # 500 on any project that hadn't. Same approach list_feedback already uses.
    flags = []
    for doc in db.collection("catalogue_flags").where("status", "==", "open").stream():
        entry = doc.to_dict()
        entry["id"] = doc.id
        detected_at = entry.get("detectedAt")
        entry["detectedAt"] = detected_at.isoformat() if hasattr(detected_at, "isoformat") else str(detected_at)
        flags.append(entry)
    flags.sort(key=lambda f: f.get("detectedAt") or "", reverse=True)
    return flags


@app.get("/api/admin/catalogue-freshness/history")
def list_catalogue_freshness_history(decoded: dict = Depends(require_admin)):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="This service is temporarily unavailable. Please try again later.")
    query = db.collection("catalogue_freshness_runs").order_by(
        "runAt", direction=fb_firestore.Query.DESCENDING
    ).limit(10)
    runs = []
    for doc in query.stream():
        entry = doc.to_dict()
        entry["id"] = doc.id
        run_at = entry.get("runAt")
        entry["runAt"] = run_at.isoformat() if hasattr(run_at, "isoformat") else str(run_at)
        runs.append(entry)
    return runs


@app.post("/api/admin/catalogue-freshness/flags/{flag_id}/dismiss")
def dismiss_catalogue_freshness_flag(flag_id: str, decoded: dict = Depends(require_admin)):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="This service is temporarily unavailable. Please try again later.")
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
