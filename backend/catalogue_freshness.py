"""
UniGuide - Catalogue Freshness Check
Author: Fatuma Omar Marsa (159056)
Supervised by: Deperias Webula Kerre
Strathmore University - School of Computing and Engineering Sciences

Runs both on an admin's manual request and automatically on a weekly
schedule (see main.py's _start_scheduler/_scheduled_freshness_check) -
re-fetches KUCCPS's own published degree programme cutoff document and
cross-references it, structurally (not by guessing from text layout - see
ml/experiments/catalogue_verification/ for why that matters), against the
current programme catalog. Flags any offering-university entry whose real
KUCCPS listing shows no placements in either of the last two years on
record - the strongest available signal that a university may have
stopped offering that programme.

This does NOT auto-edit the catalog. Every flag is surfaced to an admin for
manual review and decision, consistent with how every other catalog write
already goes through a human via PUT /api/admin/programmes/{id} - this
module only ever proposes; it never writes to `programmes_catalog.py` or
Firestore's `programmes` collection itself.

SECURITY NOTE ON TLS VERIFICATION: KUCCPS's own server
(statics.kuccps.net) serves an incomplete certificate chain that fails
standard verification - confirmed during manual testing, this is a
misconfiguration on their end (a missing intermediate certificate), not a
client-side settings issue. This fetch therefore disables certificate
verification for this ONE specific, hard-coded, government-published URL
only - never for any user-supplied or dynamic URL, and never for a request
carrying credentials or user data. The document fetched is public,
non-sensitive data (university admission cutoff points). This is a
deliberate, disclosed trade-off scoped to a single known endpoint, not a
general practice - do not copy this pattern for other requests without the
same reasoning applying.
"""

import io
import re
import warnings
from typing import Dict, List, TypedDict

import pdfplumber
import requests
import urllib3

from programmes_catalog import PROGRAMMES

KUCCPS_DEGREE_PROGRAMMES_URL = "https://statics.kuccps.net/uploads/globalFiles/DEGREE_PROGRAMMES_2025.pdf"

# Institution names appear inconsistently abbreviated/expanded across
# KUCCPS's own documents and our catalog - canonicalize both sides to the
# same short alias before comparing. See catalogue_verification/README.md's
# "institution codes are not stable identifiers" finding for why matching
# on the numeric KUCCPS code instead is not reliable either.
_ALIAS_MAP = [
    ("JOMO KENYATTA", "JKUAT"),
    ("UNIVERSITY OF NAIROBI", "UON"),
    ("SOUTH EASTERN KENYA", "SEKU"),
    ("MASINDE MULIRO", "MMUST"),
    ("DEDAN KIMATHI", "DEKUT"),
    ("TECHNICAL UNIVERSITY OF KENYA", "TUK"),
    ("TECHNICAL UNIVERSITY OF MOMBASA", "TUM"),
]

_STOP_WORDS = {"BACHELOR", "OF", "IN", "THE", "AND", "A"}


def _clean(s: str) -> str:
    s = s.upper().replace("\n", " ")
    s = re.sub(r"[^A-Z ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _canon_institution(name: str) -> str:
    cleaned = _clean(name)
    for key, alias in _ALIAS_MAP:
        if key in cleaned:
            return alias
    return cleaned


def _programme_words(title: str) -> set:
    return set(_clean(title).split()) - _STOP_WORDS


class FreshnessFlag(TypedDict):
    programmeId: str
    programmeTitle: str
    universityName: str
    issueType: str
    details: str
    matchedProgramme: str
    catalogCutoff: float


def fetch_kuccps_rows() -> List[dict]:
    """Downloads and structurally parses KUCCPS's official degree
    programmes document via pdfplumber's table-grid extraction (see module
    docstring for the TLS trade-off this makes). Raises on failure -
    callers must treat an exception as "the check could not run", never as
    "no discrepancies were found"."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(KUCCPS_DEGREE_PROGRAMMES_URL, verify=False, timeout=90)
    response.raise_for_status()

    rows: List[dict] = []
    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if len(row) >= 6 and row[2] and row[3]:
                        rows.append(
                            {
                                "institution": row[2].strip(),
                                "programme": row[3].strip(),
                                "cutoff_2023": (row[4] or "").strip(),
                                "cutoff_2022": (row[5] or "").strip(),
                            }
                        )
    return rows


def check_catalogue_freshness(rows: List[dict] = None) -> List[FreshnessFlag]:
    """Cross-references every offering university in the current catalog
    against a fresh KUCCPS fetch (or a pre-fetched `rows` list, for
    testing). Flags a pair only when its matched real cutoff is blank in
    BOTH of the last two years shown - a single blank year is a common,
    ordinary sign of that year's low demand (see the Forestry/SEKU case in
    catalogue_verification/README.md), not evidence the programme was
    dropped. Two consecutive blank years is a materially stronger signal,
    chosen deliberately to keep false-positive flags rare."""
    if rows is None:
        rows = fetch_kuccps_rows()

    by_inst: Dict[str, List[dict]] = {}
    for r in rows:
        by_inst.setdefault(_canon_institution(r["institution"]), []).append(r)

    flags: List[FreshnessFlag] = []
    for programme in PROGRAMMES:
        pw = _programme_words(programme["title"])
        for uni in programme["offeringUniversities"]:
            key = _canon_institution(uni["universityName"])
            candidates = by_inst.get(key, [])
            if not candidates:
                # No KUCCPS presence at all for this institution (e.g. a
                # private, self-sponsored university) - not a freshness
                # signal, it was never tracked there in the first place.
                continue

            scored = sorted(
                ((len(pw & _programme_words(c["programme"])), c) for c in candidates),
                key=lambda x: -x[0],
            )
            best_score, best = scored[0]
            if best_score == 0:
                continue  # no plausible title match at all - can't compare safely

            blank_2023 = best["cutoff_2023"] in ("", "-")
            blank_2022 = best["cutoff_2022"] in ("", "-")
            if blank_2023 and blank_2022:
                flags.append(
                    {
                        "programmeId": programme["id"],
                        "programmeTitle": programme["title"],
                        "universityName": uni["universityName"],
                        "issueType": "possibly_discontinued",
                        "details": (
                            f"KUCCPS shows no placements for the matched programme "
                            f"at this institution in either of the last two years on "
                            f"record. Catalog currently lists a cutoff of "
                            f"{uni['latestCutoff']}."
                        ),
                        "matchedProgramme": best["programme"],
                        "catalogCutoff": uni["latestCutoff"],
                    }
                )
    return flags
