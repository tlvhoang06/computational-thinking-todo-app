import datetime
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from firebase_admin import auth
from firebase_admin.exceptions import FirebaseError

from .firebase import db

UTC = datetime.timezone.utc


def get_user_doc(uid: str) -> dict:
    user_ref = db.collection("users").document(uid)
    doc = user_ref.get()
    if doc.exists:
        return {"uid": uid, **doc.to_dict()}

    now = datetime.datetime.now(UTC).isoformat()
    user_data = {"role": "user", "email_verified": False, "created_at": now}
    user_ref.set(user_data)
    return {"uid": uid, **user_data}


def verify_firebase_token(authorization: Optional[str] = Header(default=None)) -> dict:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")

    token = authorization.split(" ", 1)[1]
    try:
        decoded_token = auth.verify_id_token(token)
    except FirebaseError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Your session is invalid or expired.")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    uid = decoded_token.get("uid")
    if not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user_doc = get_user_doc(uid)
    user_doc["email"] = decoded_token.get("email", "")
    if user_doc["email"]:
        db.collection("users").document(uid).set({"email": user_doc["email"]}, merge=True)
    return user_doc


def require_admin(user=Depends(verify_firebase_token)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You need admin permission for this action.")
    return user
