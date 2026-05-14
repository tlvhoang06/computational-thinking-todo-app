# Todo App with Streamlit, FastAPI, and Firebase

This repository contains a Todo application built with:

- Streamlit for the frontend user interface
- FastAPI for the backend REST API
- Firebase Authentication for email/password login and optional Google login
- Cloud Firestore for user and Todo storage

## Project Structure

- `backend/main.py` - FastAPI entrypoint
- `backend/app/config.py` - backend environment configuration
- `backend/app/firebase.py` - Firebase Admin SDK initialization
- `backend/app/auth.py` - Firebase ID token verification and user profile bootstrap
- `backend/app/schemas.py` - Pydantic request/response models
- `backend/app/routes/` - API route modules
- `frontend/app.py` - Streamlit entrypoint
- `frontend/config.py` - frontend environment configuration
- `frontend/firebase_auth.py` - Firebase Authentication REST API calls
- `frontend/api_client.py` - FastAPI client helpers
- `frontend/session.py` - Streamlit auth session state
- `frontend/components.py` - Streamlit UI components
- `procedure.ipynb` - English notebook explaining the build process and data flow

## Setup

1. Create a Firebase project.
2. Enable Email/Password in Firebase Authentication.
3. Enable Google sign-in if you want to demo the advanced login feature.
4. Create a Cloud Firestore database.
5. Create a Firebase service account JSON for the backend.
6. Copy `.env.example` to `.env` and fill in your local values.

Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

Run the backend:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Install frontend dependencies:

```bash
pip install -r frontend/requirements.txt
```

Run the frontend:

```bash
streamlit run frontend/app.py
```

Open `http://localhost:8501`.

## Submission Notes

- Submit `.env.example`, not `.env`.
- Do not submit the Firebase service account JSON file.
- The Firebase Web API key is not an admin private key, but it is still cleaner to keep it in environment variables.
- A deployed app link is useful because the grader can test the app without receiving your private Firebase credentials.

## Implemented Features

- Email/password registration and login
- Optional Google login
- Create, read, update, delete Todo items
- Only show a normal user's own Todo items
- Search by title/description
- Filter by status and priority
- Basic role-based access with `user` and `admin`
