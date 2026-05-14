import requests
from requests import RequestException

from config import (
    FIREBASE_AUTH_IDP,
    FIREBASE_AUTH_SIGNIN,
    FIREBASE_AUTH_SIGNUP,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    REQUEST_TIMEOUT,
)

FIREBASE_ERROR_MESSAGES = {
    "EMAIL_EXISTS": "This email is already registered. Please sign in instead.",
    "EMAIL_NOT_FOUND": "No account was found for this email.",
    "INVALID_LOGIN_CREDENTIALS": "Email or password is incorrect.",
    "INVALID_PASSWORD": "Email or password is incorrect.",
    "INVALID_EMAIL": "Please enter a valid email address.",
    "MISSING_PASSWORD": "Please enter your password.",
    "WEAK_PASSWORD": "Password should be at least 6 characters.",
    "TOO_MANY_ATTEMPTS_TRY_LATER": "Too many attempts. Please wait a moment and try again.",
    "USER_DISABLED": "This account has been disabled.",
    "OPERATION_NOT_ALLOWED": "This sign-in method is not enabled.",
}


def friendly_firebase_error(payload) -> str:
    if isinstance(payload, str):
        return FIREBASE_ERROR_MESSAGES.get(payload, payload)

    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, str):
        return FIREBASE_ERROR_MESSAGES.get(error, error)
    if isinstance(error, dict):
        message = error.get("message", "Authentication failed.")
        code = message.split(" : ", 1)[0]
        return FIREBASE_ERROR_MESSAGES.get(code, "Authentication failed. Please check your information and try again.")

    return "Authentication failed. Please try again."


def _post_firebase(url: str, payload: dict):
    try:
        response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        data = response.json()
    except RequestException:
        return {"error_message": "Cannot connect to Firebase right now. Please try again."}
    except ValueError:
        return {"error_message": "Firebase returned an unreadable response."}

    if response.ok:
        return data

    return {"error_message": friendly_firebase_error(data)}


def firebase_signup(email: str, password: str):
    payload = {"email": email, "password": password, "returnSecureToken": True}
    return _post_firebase(FIREBASE_AUTH_SIGNUP, payload)


def firebase_signin(email: str, password: str):
    payload = {"email": email, "password": password, "returnSecureToken": True}
    return _post_firebase(FIREBASE_AUTH_SIGNIN, payload)


def firebase_google_login(code: str):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return {"error_message": "Google OAuth client settings are not configured."}

    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    try:
        token_response = requests.post("https://oauth2.googleapis.com/token", data=token_data, timeout=REQUEST_TIMEOUT)
        token_json = token_response.json()
    except RequestException:
        return {"error_message": "Cannot connect to Google sign-in right now. Please try again."}
    except ValueError:
        return {"error_message": "Google sign-in returned an unreadable response."}

    if token_response.status_code != 200 or "id_token" not in token_json:
        return {"error_message": "Google sign-in failed. Please try again."}

    firebase_payload = {
        "postBody": f"id_token={token_json['id_token']}&providerId=google.com",
        "requestUri": GOOGLE_REDIRECT_URI,
        "returnSecureToken": True,
        "returnIdpCredential": True,
    }
    return _post_firebase(FIREBASE_AUTH_IDP, firebase_payload)
