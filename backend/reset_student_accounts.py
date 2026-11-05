"""Deletes student sign-in accounts (Firebase Authentication) so their emails can sign up again.

Run it yourself - it is deliberately a manual, opt-in tool:

    python reset_student_accounts.py          # dry run: only lists what WOULD be deleted
    python reset_student_accounts.py --yes    # actually deletes it

What it removes: every Firebase Auth account that is not an administrator, together with
that account's `students/{uid}` Firestore record if one exists (a student who signed in
again after reset_student_data.py gets a fresh record, which would otherwise be left behind).
What it keeps: administrator accounts (anyone listed in ADMIN_EMAILS or in the `admins`
collection), the programme catalogue, admin records, audit logs and freshness history.

This cannot be undone: the deleted accounts' emails and passwords are gone, and those
people have to sign up again.
"""
import sys

from dotenv import load_dotenv

load_dotenv()
from firebase_admin import auth as fb_auth  # noqa: E402

from firebase_setup import admin_emails, get_db, init_firebase  # noqa: E402


def main(confirmed: bool) -> None:
    if not init_firebase():
        print("Firebase is not configured (see backend/README.md). Nothing was done.")
        return
    db = get_db()
    admin_uids = {d.id for d in db.collection("admins").stream()}
    admin_mail = admin_emails()

    kept, targets = [], []
    for user in fb_auth.list_users().iterate_all():
        email = (user.email or "").lower()
        if user.uid in admin_uids or email in admin_mail:
            kept.append(user)
        else:
            targets.append(user)

    for user in kept:
        print(f"keeping administrator: {user.email}")
    if not targets:
        print("No student accounts to delete.")
        return

    for user in targets:
        student_ref = db.collection("students").document(user.uid)
        has_record = student_ref.get().exists
        note = " + its student record" if has_record else ""
        print(f"{'DELETING' if confirmed else 'would delete'}: {user.email or user.uid}{note}")
        if confirmed:
            if has_record:
                db.recursive_delete(student_ref)
            fb_auth.delete_user(user.uid)

    print(f"\n{len(targets)} student account(s), {len(kept)} administrator(s) kept.")
    print("Done." if confirmed else "Dry run only - nothing was deleted. Re-run with --yes to delete.")


if __name__ == "__main__":
    main("--yes" in sys.argv)
