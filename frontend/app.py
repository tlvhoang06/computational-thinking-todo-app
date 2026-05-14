import time

import streamlit as st

from components import (
    admin_panel,
    apply_theme,
    flush_toast,
    handle_google_redirect,
    login_ui,
    sidebar_user_info,
    todo_form,
    todo_list_view,
)
from session import ensure_auth_state, refresh_user_profile

st.set_page_config(page_title="Todo App", layout="wide")


def main():
    ensure_auth_state()
    st.session_state["_runtime_now"] = time.time()
    apply_theme()
    flush_toast()
    st.title("Todo Application")
    handle_google_redirect()

    if not st.session_state.auth["id_token"]:
        login_ui()
        return

    if not refresh_user_profile():
        st.error("Session expired. Please log in again.")
        return

    sidebar_user_info()
    
    # Show warning for guest mode
    if st.session_state.auth.get("is_guest"):
        st.warning("👤 You are in Guest Mode - your data will not be saved!", icon="⚠️")
    
    if st.session_state.auth.get("role") == "admin":
        admin_panel()

    todo_form()
    todo_list_view()


if __name__ == "__main__":
    main()
