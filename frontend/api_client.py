from typing import Optional

import requests
import streamlit as st

from config import API_BASE_URL, REQUEST_TIMEOUT


def get_headers():
    return {"Authorization": f"Bearer {st.session_state.auth['id_token']}"}


def backend_get(path: str, params: Optional[dict] = None):
    return requests.get(f"{API_BASE_URL}{path}", headers=get_headers(), params=params, timeout=REQUEST_TIMEOUT)


def backend_post(path: str, data: dict):
    return requests.post(f"{API_BASE_URL}{path}", json=data, headers=get_headers(), timeout=REQUEST_TIMEOUT)


def backend_put(path: str, data: dict):
    return requests.put(f"{API_BASE_URL}{path}", json=data, headers=get_headers(), timeout=REQUEST_TIMEOUT)


def backend_delete(path: str):
    return requests.delete(f"{API_BASE_URL}{path}", headers=get_headers(), timeout=REQUEST_TIMEOUT)


def get_user_list():
    return requests.get(f"{API_BASE_URL}/users", headers=get_headers(), timeout=REQUEST_TIMEOUT)


def update_user_role(target_uid: str, role: str):
    return requests.post(
        f"{API_BASE_URL}/users/{target_uid}/role",
        headers=get_headers(),
        json={"role": role},
        timeout=REQUEST_TIMEOUT,
    )
