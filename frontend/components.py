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


def apply_theme():
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=JetBrains+Mono:wght@500&display=swap');

            :root {
                --bg-a: #f4efe6;
                --bg-b: #d7e7dd;
                --ink: #102a43;
                --muted: #486581;
                --surface: rgba(255, 255, 255, 0.78);
                --line: rgba(16, 42, 67, 0.15);
                --accent: #d64545;
                --accent-2: #1f8a70;
            }

            .stApp {
                font-family: "Manrope", sans-serif;
                background:
                    radial-gradient(circle at 15% 20%, rgba(214, 69, 69, 0.20), transparent 32%),
                    radial-gradient(circle at 80% 0%, rgba(31, 138, 112, 0.22), transparent 32%),
                    linear-gradient(145deg, var(--bg-a), var(--bg-b));
            }

            .stApp, label, [data-testid="stWidgetLabel"] p, .stRadio p {
                color: var(--ink) !important;
            }

            h1, h2, h3 {
                color: var(--ink) !important;
                letter-spacing: 0 !important;
            }

            .stCaption, .stMarkdown p {
                color: var(--muted);
            }

            section[data-testid="stSidebar"] {
                background: rgba(255, 255, 255, 0.65);
                border-left: 1px solid var(--line);
                backdrop-filter: blur(8px);
            }
            [data-testid="stFormSubmitButton"] > button {
                background-color: var(--accent) !important; 
                color: white !important; 
                border: none !important;
                transition: opacity 0.2s ease !important; 
            }

            [data-testid="stFormSubmitButton"] > button:hover {
                background-color: var(--accent) !important; 
                opacity: 0.85 !important; 
            }

            div[data-testid="InputInstructions"] {
                display: none !important;
            }
            /* 1. Sửa tất cả các nút phụ (Logout, Delete, Reopen...) */
            button[kind="secondary"] {
                background-color: white !important; /* Đổi nền thành trắng */
                color: var(--ink) !important; /* Chữ xanh đen */
                border: 1px solid var(--line) !important;
                transition: opacity 0.2s ease !important;
            }

            button[kind="secondary"]:hover {
                opacity: 0.65 !important; /* Chỉ mờ đi một chút khi hover */
            }

            /* 2. Sửa các nút chính (Complete Task màu đỏ, Sign in...) */
            button[kind="primary"], button[kind="primaryFormSubmit"] {
                background-color: var(--accent) !important;
                color: white !important;
                border: none !important;
                transition: opacity 0.2s ease !important;
            }

            button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover {
                background-color: var(--accent) !important; /* Giữ nguyên màu đỏ */
                opacity: 0.85 !important; /* Mờ đi một chút khi hover */
            }

            /* 3. Sửa luôn các ô nhập liệu (Title, Description) đang bị nền đen */
            .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
                background-color: white !important;
                color: var(--ink) !important;
                -webkit-text-fill-color: var(--ink) !important; /* Ép màu chữ hiển thị rõ khi gõ */
                border: 1px solid var(--line) !important;
            }
            [data-testid="stVerticalBlockBorderWrapper"] {
                border-radius: 8px;
                border: 1px solid var(--line);
                background: var(--surface);
                box-shadow: 0 18px 40px rgba(16, 42, 67, 0.08);
                padding: 0.35rem 0.75rem;
                animation: fadeUp 360ms ease-out;
            }

            div[data-testid="stForm"] {
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 1.25rem;
                background: rgba(255, 255, 255, 0.82);
                box-shadow: 0 20px 42px rgba(16, 42, 67, 0.09);
            }

            .stButton > button, .stDownloadButton > button {
                border-radius: 8px;
                border: 1px solid rgba(16, 42, 67, 0.18);
                font-weight: 700;
                /* --- ĐÃ SỬA: Ép màu chữ cho nút bấm --- */
                color: var(--ink) !important; 
                transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
            }

            .stButton > button:hover, .stDownloadButton > button:hover {
                transform: translateY(-1px);
                box-shadow: 0 8px 16px rgba(16, 42, 67, 0.16);
                border-color: rgba(16, 42, 67, 0.28);
            }

            [data-testid="stToast"] {
                border-radius: 8px;
                border: 1px solid var(--line);
            }

            @keyframes fadeUp {
                from { opacity: 0; transform: translateY(8px); }
                to { opacity: 1; transform: translateY(0); }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

def push_toast(message: str, level: str = "info"):
    st.session_state["ui_toast"] = {"message": message, "level": level}


def flush_toast():
    payload = st.session_state.pop("ui_toast", None)
    if not payload:
        return
    icon = {"success": "✅", "error": "❌", "warning": "⚠️"}.get(payload.get("level"), "ℹ️")
    st.toast(payload.get("message", ""), icon=icon)


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
        push_toast("Google login successful.", "success")
        refresh_user_profile()
        rerun_app()
    else:
        st.error(result.get("error_message", "Google sign-in failed. Please try again."))


def login_ui():
    st.markdown("<style>section[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)

    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.subheader("Welcome to your workspace")
        st.caption("Sign in to continue with your todo board.")
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
                if auth_mode == "Register":
                    push_toast("Register successful. Your account is ready.", "success")
                else:
                    push_toast(f"Login successful: {email}", "success")
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
        with st.expander("How to sign in as admin"):
            st.write(
                "1. Login with any account.\n"
                "2. Use an existing admin account to open Admin Controls.\n"
                "3. Promote your account role from user to admin.\n"
                "4. Logout and login again to refresh admin privileges."
            )


def logout():
    reset_auth_state()
    push_toast("Logged out successfully.", "info")
    rerun_app()


def sidebar_user_info():
    st.sidebar.markdown("---")
    st.sidebar.subheader("Current user")
    st.sidebar.write(f"**Email:** {st.session_state.auth.get('email')} ")
    st.sidebar.write(f"**Role:** {st.session_state.auth.get('role')} ")
    st.sidebar.write(f"**UID:** {st.session_state.auth.get('uid')} ")
    if st.session_state.auth.get("role") == "admin":
        st.sidebar.success("Admin mode enabled")
    if st.sidebar.button("Logout"):
        logout()


def todo_form():
    st.sidebar.header("Create a Todo")
    title = st.sidebar.text_input("Title", key="todo_title")
    description = st.sidebar.text_area("Description", key="todo_description")
    due_date = st.sidebar.date_input("Due date", key="todo_due_date")
    priority = st.sidebar.selectbox("Priority", ["low", "normal", "high"], key="todo_priority")

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
    priority_filter = filter_col3.selectbox("Priority", ["all", "low", "normal", "high"])

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
        
        # Make description stand out with styling
        description_text = todo.get("description") or "No description"
        st.markdown(
            f"""
            <div style='background: rgba(255,255,255,0.5); padding: 12px; border-radius: 6px; 
                        border-left: 4px solid var(--accent); margin: 12px 0;'>
                <b>📝 Description:</b><br>{description_text}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Initialize edit mode in session state
        edit_key = f"editing_{todo['id']}"
        if edit_key not in st.session_state:
            st.session_state[edit_key] = False

        # Action buttons row - now with Edit button
        action_cols = st.columns([1.2, 1.2, 1.2, 1.4])
        toggle_text = "Complete Task" if not todo["done"] else "Reopen Task"
        toggle_type = "primary" if not todo["done"] else "secondary"
        if action_cols[0].button(toggle_text, key=f"toggle_{todo['id']}", type=toggle_type, use_container_width=True):
            update = backend_put(f"/todos/{todo['id']}", {"done": not todo["done"]})
            if update.status_code == 200:
                push_toast("Task status updated.", "success")
                rerun_app()
            else:
                show_response_error(update)

        if action_cols[1].button("Edit", key=f"edit_{todo['id']}", type="secondary", use_container_width=True):
            st.session_state[edit_key] = not st.session_state[edit_key]
            rerun_app()

        if action_cols[2].button("Delete", key=f"delete_{todo['id']}", type="secondary", use_container_width=True):
            delete = backend_delete(f"/todos/{todo['id']}")
            if delete.status_code == 204:
                push_toast("Task deleted.", "warning")
                rerun_app()
            else:
                show_response_error(delete)

        # Show edit form if in edit mode
        if st.session_state.get(edit_key, False):
            st.markdown("---")
            with st.form(f"edit_form_{todo['id']}"):
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
                    ["low", "normal", "high"],
                    index=["low", "normal", "high"].index(todo.get("priority", "normal")),
                    key=f"priority_{todo['id']}",
                )
                col1, col2 = st.columns(2)
                if col1.form_submit_button("Save changes", use_container_width=True):
                    save_todo_changes(todo["id"], edit_title, edit_description, edit_due_date, edit_priority)
                    st.session_state[edit_key] = False
                    rerun_app()
                if col2.form_submit_button("Cancel", use_container_width=True):
                    st.session_state[edit_key] = False
                    rerun_app()


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
        push_toast("Task updated.", "success")
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
