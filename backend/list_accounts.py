"""Lists Firebase Authentication accounts with their role and email-verification status.
Read-only: nothing is created, changed or deleted.

    python list_accounts.py
"""
from dotenv import load_dotenv

load_dotenv()
from firebase_admin import auth as fb_auth  # noqa: E402

from firebase_setup import admin_emails, get_db, init_firebase  # noqa: E402


def main() -> None:
    if not init_firebase():
        print("Firebase is not configured (see backend/README.md). Nothing was read.")
        return
    db = get_db()
    admin_uids = {d.id for d in db.collection("admins").stream()}
    admin_mail = admin_emails()
    users = list(fb_auth.list_users().iterate_all())
    for user in sorted(users, key=lambda u: (u.email or "")):
        email = (user.email or "").lower()
        role = "administrator" if user.uid in admin_uids or email in admin_mail else "student"
        has_profile = db.collection("students").document(user.uid).get().exists
        providers = ",".join(p.provider_id for p in user.provider_data) or "-"
        print(f"{user.email or user.uid}: role={role} email_verified={user.email_verified} "
              f"sign_in={providers} disabled={user.disabled} student_record={has_profile}")
    print(f"\n{len(users)} account(s).")


if __name__ == "__main__":
    main()
