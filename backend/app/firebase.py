import firebase_admin
from firebase_admin import credentials, firestore

from .config import settings


def initialize_firebase() -> None:
    if not settings.google_application_credentials:
        raise RuntimeError("Set GOOGLE_APPLICATION_CREDENTIALS to the Firebase service account JSON path.")

    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.google_application_credentials)
        firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})


initialize_firebase()
db = firestore.client()
