import streamlit as st

from api_client import backend_get

PROFILE_CACHE_SECONDS = 20


def ensure_auth_state():
    if "auth" not in st.session_state:
        st.session_state.auth = {
            "id_token": None,
            "email": None,
            "role": None,
            "uid": None,
        }
    if "profile_last_sync" not in st.session_state:
        st.session_state.profile_last_sync = 0.0


def reset_auth_state():
    st.session_state.auth = {"id_token": None, "email": None, "role": None, "uid": None}
    st.session_state.profile_last_sync = 0.0


def refresh_user_profile(force: bool = False):
    if not force:
        now = st.session_state.get("_runtime_now")
        if now is not None and now - st.session_state.profile_last_sync < PROFILE_CACHE_SECONDS:
            return bool(st.session_state.auth.get("uid"))

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
        now = st.session_state.get("_runtime_now")
        if now is not None:
            st.session_state.profile_last_sync = now
        return True

    reset_auth_state()
    return False
