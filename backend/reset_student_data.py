"""Deletes student-entered data from Firestore (profiles + recommendations + feedback).

Run it yourself - it is deliberately a manual, opt-in tool:

    python reset_student_data.py          # dry run: only lists what WOULD be deleted
    python reset_student_data.py --yes    # actually deletes it

What it removes: every `students/{uid}` document and everything under it
(saved profile, recommendations, feedback), except any uid that is also an
admin. What it keeps: Firebase Auth accounts (people can still sign in - a
blank student record is recreated automatically on their next sign-in), the
programme catalogue, admin records, audit logs and freshness history.
"""
import sys

from dotenv import load_dotenv

load_dotenv()
from firebase_setup import get_db, init_firebase  # noqa: E402


def main(confirmed: bool) -> None:
    init_firebase()
    db = get_db()
    admin_uids = {d.id for d in db.collection("admins").stream()}

    targets = [s for s in db.collection("students").stream() if s.id not in admin_uids]
    if not targets:
        print("No student data to delete.")
        return

    for s in targets:
        email = (s.to_dict() or {}).get("email")
        recs = len(list(s.reference.collection("recommendations").stream()))
        fb = len(list(s.reference.collection("feedback").stream()))
        print(f"{'DELETING' if confirmed else 'would delete'}: {email}  ({recs} recommendations, {fb} feedback)")
        if confirmed:
            db.recursive_delete(s.reference)

    print("Done." if confirmed else "\nDry run only - nothing was deleted. Re-run with --yes to delete.")


if __name__ == "__main__":
    main("--yes" in sys.argv)
