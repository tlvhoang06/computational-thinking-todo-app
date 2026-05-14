import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    firebase_project_id: str | None
    google_application_credentials: str | None
    cors_origins: list[str]


def load_settings() -> Settings:
    cors_origins = [
        origin.strip()
        for origin in os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501").split(",")
        if origin.strip()
    ]
    return Settings(
        firebase_project_id=os.getenv("FIREBASE_PROJECT_ID"),
        google_application_credentials=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        cors_origins=cors_origins,
    )


settings = load_settings()
