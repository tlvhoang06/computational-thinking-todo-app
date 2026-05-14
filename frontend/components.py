import urllib.parse

import streamlit as st

from api_client import backend_delete, backend_get, backend_post, backend_put, get_user_list, update_user_role
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
from firebase_auth import firebase_google_login, firebase_signin, firebase_signup
from session import refresh_user_profile, reset_auth_state


HTTP_ERROR_MESSAGES = {
    400: "The request is not valid. Please check your input.",
    401: "Your session has expired. Please sign in again.",
    403: "You do not have permission to do that.",
    404: "The requested item was not found.",
    422: "Some fields are invalid. Please check and try again.",
    500: "The server had a problem. Please try again later.",
}


def rerun_app():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


def show_response_error(response):
    message = HTTP_ERROR_MESSAGES.get(response.status_code, "Something went wrong. Please try again.")
    try:
        data = response.json()
    except ValueError:
        data = {}

    detail = data.get("detail") if isinstance(data, dict) else None
    if isinstance(detail, str):
        message = detail
    elif isinstance(detail, list):
        first_error = detail[0] if detail else {}
        field = " -> ".join(str(part) for part in first_error.get("loc", []) if part != "body")
        reason = first_error.get("msg", "Invalid value")
        message = f"{field}: {reason}" if field else reason

    st.error(message)


def handle_google_redirect():
    if st.session_state.auth["id_token"] or not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET):
        return

    query_params = st.query_params
    code_value = query_params.get("code")
    if not code_value:
        return

    if isinstance(code_value, list):
        code_value = code_value[0]

    result = firebase_google_login(code_value)
    try:
        st.query_params.clear()
    except AttributeError:
        st.experimental_set_query_params()
    if "idToken" in result:
        st.session_state.auth["id_token"] = result["idToken"]
        st.success("Google sign-in successful")
        refresh_user_profile()
        rerun_app()
    else:
        st.error(result.get("error_message", "Google sign-in failed. Please try again."))


def login_ui():
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] {display: none;}
            .block-container {
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            div[data-testid="stForm"] {
                border: 1px solid rgba(49, 51, 63, 0.18);
                border-radius: 8px;
                padding: 1.5rem;
                background: rgba(255, 255, 255, 0.03);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.subheader("Welcome back")
        auth_mode = st.radio("Choose action", ["Login", "Register"], horizontal=True)

        with st.form("auth_form"):
            email = st.text_input("Email", key="email")
            password = st.text_input("Password", type="password", key="password")
            submitted = st.form_submit_button("Sign in" if auth_mode == "Login" else "Create account", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("Email and password are required.")
                return

            result = firebase_signup(email, password) if auth_mode == "Register" else firebase_signin(email, password)
            if "idToken" in result:
                st.session_state.auth["id_token"] = result["idToken"]
                st.success(f"Authenticated as {email}")
                refresh_user_profile()
                rerun_app()
            else:
                st.error(result.get("error_message", "Authentication failed. Please try again."))

        if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
            st.markdown("---")
            auth_url = (
                "https://accounts.google.com/o/oauth2/v2/auth?"
                + urllib.parse.urlencode(
                    {
                        "client_id": GOOGLE_CLIENT_ID,
                        "redirect_uri": GOOGLE_REDIRECT_URI,
                        "response_type": "code",
                        "scope": "openid email profile",
                        "access_type": "offline",
                        "prompt": "select_account",
                    }
                )
            )
            st.link_button("Continue with Google", auth_url, use_container_width=True)


def logout():
    reset_auth_state()
    st.success("Logged out")
    rerun_app()


def sidebar_user_info():
    st.sidebar.markdown("---")
    st.sidebar.subheader("Current user")
    st.sidebar.write(f"**Email:** {st.session_state.auth.get('email')} ")
    st.sidebar.write(f"**Role:** {st.session_state.auth.get('role')} ")
    st.sidebar.write(f"**UID:** {st.session_state.auth.get('uid')} ")
    if st.sidebar.button("Logout"):
        logout()


def todo_form():
    st.sidebar.header("Create a Todo")
    title = st.sidebar.text_input("Title", key="todo_title")
    description = st.sidebar.text_area("Description", key="todo_description")
    due_date = st.sidebar.date_input("Due date", key="todo_due_date")
    priority = st.sidebar.selectbox("Priority", ["normal", "high", "low"], key="todo_priority")

    if st.sidebar.button("Add Todo"):
        if not title.strip():
            st.error("Todo title is required.")
            return
        payload = {
            "title": title.strip(),
            "description": description.strip() or None,
            "due_date": due_date.isoformat() if due_date else None,
            "priority": priority,
        }
        response = backend_post("/todos", payload)
        if response.status_code == 201:
            st.success("Todo created")
            rerun_app()
        else:
            show_response_error(response)


def todo_list_view():
    st.header("Todo Dashboard")
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    search_text = filter_col1.text_input("Search todos")
    status_filter = filter_col2.selectbox("Status", ["all", "todo", "done"])
    priority_filter = filter_col3.selectbox("Priority", ["all", "normal", "high", "low"])

    params = {}
    if search_text:
        params["q"] = search_text
    if status_filter != "all":
        params["status"] = status_filter
    if priority_filter != "all":
        params["priority"] = priority_filter

    response = backend_get("/todos", params=params)
    if response.status_code != 200:
        show_response_error(response)
        return

    todos = response.json()
    if not todos:
        st.info("No todos found.")
        return

    for todo in todos:
        render_todo_card(todo)


def render_todo_card(todo: dict):
    with st.container():
        cols = st.columns([3, 1, 1])
        cols[0].markdown(f"### {todo['title']}")
        cols[1].markdown(f"**{'Done' if todo['done'] else 'Open'}**")
        cols[2].markdown(f"**Priority:** {todo['priority']}  \n**Due:** {todo.get('due_date') or '-'}")
        st.write(todo.get("description") or "")

        with st.expander("Edit todo"):
            edit_title = st.text_input("Title", value=todo["title"], key=f"title_{todo['id']}")
            edit_description = st.text_area(
                "Description",
                value=todo.get("description") or "",
                key=f"description_{todo['id']}",
            )
            edit_due_date = st.text_input(
                "Due date (YYYY-MM-DD)",
                value=todo.get("due_date") or "",
                key=f"due_{todo['id']}",
            )
            edit_priority = st.selectbox(
                "Priority",
                ["normal", "high", "low"],
                index=["normal", "high", "low"].index(todo.get("priority", "normal")),
                key=f"priority_{todo['id']}",
            )
            if st.button("Save changes", key=f"save_{todo['id']}"):
                save_todo_changes(todo["id"], edit_title, edit_description, edit_due_date, edit_priority)

        action_cols = st.columns([1, 1, 4])
        if action_cols[0].button("Mark done" if not todo["done"] else "Mark open", key=f"toggle_{todo['id']}"):
            update = backend_put(f"/todos/{todo['id']}", {"done": not todo["done"]})
            if update.status_code == 200:
                rerun_app()
            else:
                show_response_error(update)

        if action_cols[1].button("Delete", key=f"delete_{todo['id']}"):
            delete = backend_delete(f"/todos/{todo['id']}")
            if delete.status_code == 204:
                rerun_app()
            else:
                show_response_error(delete)


def save_todo_changes(todo_id: str, title: str, description: str, due_date: str, priority: str):
    if not title.strip():
        st.error("Todo title is required.")
        return

    payload = {
        "title": title.strip(),
        "description": description.strip() or None,
        "due_date": due_date.strip() or None,
        "priority": priority,
    }
    update = backend_put(f"/todos/{todo_id}", payload)
    if update.status_code == 200:
        st.success("Todo updated")
        rerun_app()
    else:
        show_response_error(update)


def admin_panel():
    st.markdown("---")
    st.subheader("Admin Controls")
    st.info("Admin users can see all todos and assign admin/user roles.")

    users_response = get_user_list()
    users = users_response.json() if users_response.status_code == 200 else []
    if users_response.status_code != 200:
        show_response_error(users_response)

    with st.expander("Manage roles", expanded=True):
        user_options = {
            f"{user.get('email') or 'No email'} | {user.get('role', 'user')} | {user['uid']}": user["uid"]
            for user in users
        }
        selected_user = st.selectbox("User", list(user_options.keys()), key="admin_user_select") if user_options else None
        target_uid = user_options[selected_user] if selected_user else st.text_input("Target user UID", key="admin_target_uid")
        target_role = st.selectbox("New role", ["user", "admin"], key="admin_target_role")
        if st.button("Update role", key="admin_update_role"):
            if not target_uid:
                st.error("Enter a target UID.")
            else:
                response = update_user_role(target_uid, target_role)
                if response.status_code == 200:
                    st.success(f"Role updated: {target_uid} -> {target_role}")
                    rerun_app()
                else:
                    show_response_error(response)
