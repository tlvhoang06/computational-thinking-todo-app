from typing import Optional

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    uid: str
    email: str
    role: str = Field(default="user")


class UserRoleUpdate(BaseModel):
    role: str = Field(pattern="^(user|admin)$")


class TodoCreate(BaseModel):
    title: str = Field(min_length=1)
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: str = Field(default="normal", pattern="^(low|normal|high)$")


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = Field(default=None, pattern="^(low|normal|high)$")
    done: Optional[bool] = None


class TodoResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    due_date: Optional[str]
    priority: str
    done: bool
    created_at: str
    updated_at: str
    owner_uid: str
