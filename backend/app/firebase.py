import firebase_admin
from firebase_admin import auth, credentials, firestore

from .config import settings


def initialize_firebase() -> None:
    if not settings.google_application_credentials:
        raise RuntimeError("Set GOOGLE_APPLICATION_CREDENTIALS to the Firebase service account JSON path.")

    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.google_application_credentials)
        firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})


def ensure_bootstrap_admin() -> None:
    email = (settings.bootstrap_admin_email or "").strip()
    if not email:
        return

    password = settings.bootstrap_admin_password
    user = None
    try:
        user = auth.get_user_by_email(email)
    except auth.UserNotFoundError:
        if not password:
            raise RuntimeError("BOOTSTRAP_ADMIN_PASSWORD is required to create bootstrap admin user.")
        user = auth.create_user(email=email, password=password, email_verified=True)

    db.collection("users").document(user.uid).set(
        {"role": "admin", "email": email, "email_verified": True},
        merge=True,
    )


initialize_firebase()
db = firestore.client()
ensure_bootstrap_admin()
