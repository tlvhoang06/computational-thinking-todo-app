import streamlit as st

from api_client import backend_get


def ensure_auth_state():
    if "auth" not in st.session_state:
        st.session_state.auth = {
            "id_token": None,
            "email": None,
            "role": None,
            "uid": None,
        }


def reset_auth_state():
    st.session_state.auth = {"id_token": None, "email": None, "role": None, "uid": None}


def refresh_user_profile():
    response = backend_get("/me")
    if response.status_code == 200:
        user = response.json()
        st.session_state.auth.update(
            {
                "email": user.get("email"),
                "uid": user.get("uid"),
                "role": user.get("role"),
            }
        )
        return True

    reset_auth_state()
    return False
