"""Brings the live Firestore `programmes` documents' `offeringUniversities` field in
line with backend/programmes_catalog.py after the catalogue corrections.

Touches ONLY that one field, and ONLY on documents where it differs - admin edits to
cutoffs, grades or descriptions are never overwritten. Dry run by default:

    python catalogue_verification/sync_offerings_to_firestore.py          # show what differs
    python catalogue_verification/sync_offerings_to_firestore.py --apply  # write the changes
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(BACKEND, ".env"))
from firebase_setup import get_db, init_firebase  # noqa: E402
from programmes_catalog import PROGRAMMES  # noqa: E402


def main(apply: bool) -> None:
    init_firebase()
    db = get_db()
    changed = 0
    for p in PROGRAMMES:
        ref = db.collection("programmes").document(p["id"])
        snap = ref.get()
        if not snap.exists:
            print(f"skip (no Firestore doc yet, it will be created from the file on first start): {p['id']}")
            continue
        live = snap.to_dict().get("offeringUniversities")
        if live == p["offeringUniversities"]:
            continue
        changed += 1
        print(f"{'UPDATING' if apply else 'would update'}: {p['title']}")
        old = {u["kuccpsCode"]: u for u in (live or [])}
        for u in p["offeringUniversities"]:
            before = old.get(u["kuccpsCode"])
            if before != u:
                print(f"    {u['universityName']}  code {u['kuccpsCode']}  {u['latestCutoff']}/{u['previousCutoff']}")
        if apply:
            ref.update({"offeringUniversities": p["offeringUniversities"]})
    print(f"\n{changed} document(s) {'updated' if apply else 'differ'}.")
    if not apply and changed:
        print("Dry run only - re-run with --apply to write.")


if __name__ == "__main__":
    main("--apply" in sys.argv)
