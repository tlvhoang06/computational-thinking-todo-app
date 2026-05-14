from typing import List

from fastapi import APIRouter, Depends

from ..auth import require_admin, verify_firebase_token
from ..firebase import db
from ..schemas import UserInfo, UserRoleUpdate

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserInfo)
def get_me(user=Depends(verify_firebase_token)):
    return UserInfo(uid=user["uid"], email=user.get("email", ""), role=user.get("role", "user"))


@router.get("/users", response_model=List[UserInfo])
def list_users(user=Depends(require_admin)):
    users = []
    for doc in db.collection("users").stream():
        data = doc.to_dict()
        users.append(
            UserInfo(
                uid=doc.id,
                email=data.get("email", ""),
                role=data.get("role", "user"),
            )
        )
    users.sort(key=lambda item: (item.role != "admin", item.email or item.uid))
    return users


@router.post("/users/{target_uid}/role", response_model=UserInfo)
def set_user_role(target_uid: str, update: UserRoleUpdate, user=Depends(require_admin)):
    role = update.role

    user_ref = db.collection("users").document(target_uid)
    user_ref.set({"role": role}, merge=True)
    updated = user_ref.get().to_dict() or {}
    return UserInfo(uid=target_uid, email=updated.get("email", ""), role=role)
