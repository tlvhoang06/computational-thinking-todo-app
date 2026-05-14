import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..auth import UTC, verify_firebase_token
from ..firebase import db
from ..schemas import TodoCreate, TodoResponse, TodoUpdate

router = APIRouter(prefix="/todos", tags=["todos"])


def todo_doc_to_response(todo_id: str, data: dict) -> TodoResponse:
    return TodoResponse(
        id=todo_id,
        title=data.get("title", ""),
        description=data.get("description"),
        due_date=data.get("due_date"),
        priority=data.get("priority", "normal"),
        done=data.get("done", False),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
        owner_uid=data.get("owner_uid", ""),
    )


def get_todo_or_404(todo_id: str):
    doc_ref = db.collection("todos").document(todo_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return doc_ref, doc.to_dict()


@router.get("", response_model=List[TodoResponse])
def list_todos(
    q: Optional[str] = None,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    priority: Optional[str] = None,
    user=Depends(verify_firebase_token),
):
    role = user.get("role", "user")
    query = db.collection("todos")
    if role != "admin":
        query = query.where("owner_uid", "==", user["uid"])

    if priority:
        query = query.where("priority", "==", priority)
    if status_filter:
        if status_filter == "done":
            query = query.where("done", "==", True)
        elif status_filter == "todo":
            query = query.where("done", "==", False)

    todos = []
    for doc in query.stream():
        data = doc.to_dict()
        searchable_text = f"{data.get('title', '')} {data.get('description', '') or ''}".lower()
        if q and q.lower() not in searchable_text:
            continue
        todos.append(todo_doc_to_response(doc.id, data))

    todos.sort(key=lambda item: item.due_date or "")
    return todos


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoCreate, user=Depends(verify_firebase_token)):
    now = datetime.datetime.now(UTC).isoformat()
    payload = {
        "title": todo.title,
        "description": todo.description,
        "due_date": todo.due_date,
        "priority": todo.priority,
        "done": False,
        "owner_uid": user["uid"],
        "created_at": now,
        "updated_at": now,
    }
    doc_ref = db.collection("todos").document()
    doc_ref.set(payload)
    return todo_doc_to_response(doc_ref.id, payload)


@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: str, todo: TodoUpdate, user=Depends(verify_firebase_token)):
    doc_ref, data = get_todo_or_404(todo_id)
    role = user.get("role", "user")
    if data.get("owner_uid") != user["uid"] and role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    updates = {}
    if todo.title is not None:
        updates["title"] = todo.title
    if todo.description is not None:
        updates["description"] = todo.description
    if todo.due_date is not None:
        updates["due_date"] = todo.due_date
    if todo.priority is not None:
        updates["priority"] = todo.priority
    if todo.done is not None:
        updates["done"] = todo.done
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    updates["updated_at"] = datetime.datetime.now(UTC).isoformat()
    doc_ref.update(updates)
    data.update(updates)
    return todo_doc_to_response(todo_id, data)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: str, user=Depends(verify_firebase_token)):
    doc_ref, data = get_todo_or_404(todo_id)
    role = user.get("role", "user")
    if data.get("owner_uid") != user["uid"] and role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    doc_ref.delete()
    return None
