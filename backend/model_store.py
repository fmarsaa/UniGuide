"""Fetches the trained model on a server that does not have it yet, and checks it.

The trained model is too large for the git repository, so a deployed server starts
with MODEL_URL and MODEL_SHA256 set. The file is downloaded once, its SHA-256 is
compared with the published value, and a file that does not match is deleted and
never loaded. A server that already has the model file does nothing here.
"""

import hashlib
import logging
import os
from typing import Optional

import requests

logger = logging.getLogger("uniguide")


def sha256_of(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_model(path: str, url: Optional[str], expected_sha256: Optional[str], token: Optional[str] = None) -> bool:
    """True when a verified model file is at `path` afterwards."""
    if os.path.isfile(path):
        return True
    if not url:
        return False
    if not expected_sha256:
        logger.error("MODEL_URL is set but MODEL_SHA256 is not; refusing to load an unchecked model.")
        return False
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    partial = path + ".part"
    try:
        with requests.get(url, headers=headers, stream=True, timeout=60) as response:
            response.raise_for_status()
            with open(partial, "wb") as f:
                for block in response.iter_content(chunk_size=1024 * 1024):
                    f.write(block)
    except requests.RequestException:
        logger.exception("Could not download the model from MODEL_URL.")
        _remove(partial)
        return False
    if sha256_of(partial).lower() != expected_sha256.strip().lower():
        logger.error("The downloaded model does not match MODEL_SHA256; it was discarded.")
        _remove(partial)
        return False
    os.replace(partial, path)
    return True


def _remove(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass
