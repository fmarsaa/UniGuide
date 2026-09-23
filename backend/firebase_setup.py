"""
UniGuide - Firebase Admin Bootstrap

Centralizes Firebase Authentication token verification and Cloud Firestore
access for the FastAPI backend (see proposal IR-05: "The backend shall
interface directly with Firebase Firestore to perform CRUD operations").

Firestore/Auth-backed endpoints are only enabled once a service account key
is configured via the FIREBASE_SERVICE_ACCOUNT_PATH environment variable
(see backend/README.md for how to generate one). Without it, the backend
still starts and can run pure ML inference, but returns a clear 503 on any
endpoint that requires authentication or persistence - it never silently
pretends a write succeeded.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger("uniguide")

_db = None
_app = None
_initialized = False


def init_firebase() -> bool:
    """Idempotently initializes the Firebase Admin SDK. Returns True if usable."""
    global _db, _app, _initialized
    if _initialized:
        return _db is not None

    _initialized = True
    cred_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")

    if not cred_path or not os.path.isfile(cred_path):
        logger.warning(
            "FIREBASE_SERVICE_ACCOUNT_PATH is not set or the file does not exist "
            "(looked for: %s). Authentication and Firestore persistence are disabled "
            "until this is configured - see backend/README.md.",
            cred_path,
        )
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        cred = credentials.Certificate(cred_path)
        _app = firebase_admin.initialize_app(cred)
        _db = firestore.client()
        logger.info("Firebase Admin initialized. Firestore persistence and auth verification enabled.")
        return True
    except Exception:
        logger.exception("Failed to initialize Firebase Admin SDK.")
        _db = None
        return False


def is_configured() -> bool:
    return _db is not None


def get_db():
    return _db


def verify_id_token(id_token: str) -> dict:
    """Raises on an invalid/expired token. Caller must ensure is_configured() first."""
    from firebase_admin import auth as fb_auth

    return fb_auth.verify_id_token(id_token)


def admin_emails() -> set:
    raw = os.environ.get("ADMIN_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}
