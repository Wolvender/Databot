# auth.py - Authentication and session management
"""
Token-based remember-me: a random token is stored client-side (session state /
localStorage) and its *hash* lives in users.json.  No plain password is ever
written to disk.
"""

import streamlit as st


# ──────────────────────────────────────────────────────────────
# Session-state bootstrap
# ──────────────────────────────────────────────────────────────

def initialize_session_state():
    """Initialize every session-state key the app depends on."""
    defaults = {
        "logged_in": False,
        "username": None,
        "remember_token": None,  # raw token for current session
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ──────────────────────────────────────────────────────────────
# Core helpers
# ──────────────────────────────────────────────────────────────

def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)


def get_current_username() -> str:
    return st.session_state.get("username") or "Unknown"


def check_password(username: str, password: str) -> bool:
    """Delegate to UserManager so all hashing lives in one place."""
    from user_manager import user_manager
    return user_manager.verify_password(username, password)


# ──────────────────────────────────────────────────────────────
# Login / Logout
# ──────────────────────────────────────────────────────────────

def login_user(username: str, password: str, remember_me: bool = False) -> bool:
    """
    Authenticate the user.
    If remember_me is True a fresh token is issued, stored (hashed) in
    users.json, and the raw token is kept in session_state so the browser
    can persist it via JavaScript localStorage.
    """
    if not check_password(username, password):
        return False

    st.session_state.logged_in = True
    st.session_state.username = username

    from user_manager import user_manager

    if remember_me:
        raw_token = user_manager.create_remember_token(username)
        st.session_state.remember_token = raw_token
        # Inject the token into localStorage so it survives page reloads
        _write_token_to_localstorage(username, raw_token)
    else:
        # Clear any previously stored token for this browser
        _clear_token_from_localstorage()

    return True


def logout_user():
    """
    Log out and revoke the current remember-me token so it can't be reused.
    """
    from user_manager import user_manager

    username = st.session_state.get("username")
    raw_token = st.session_state.get("remember_token")

    if username and raw_token:
        user_manager.revoke_remember_token(username, raw_token)

    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.remember_token = None

    _clear_token_from_localstorage()


# ──────────────────────────────────────────────────────────────
# Auto-login from localStorage token
# ──────────────────────────────────────────────────────────────

def check_remembered_login():
    """
    Called once at app startup.  Reads the remember-me token injected by
    JavaScript into a hidden Streamlit text input, validates it against
    users.json, and auto-logs the user in if valid.

    Returns True if auto-login succeeded.
    """
    if is_logged_in():
        return True  # already authenticated this session

    # The JS bridge writes into st.session_state["_rm_payload"] as "username:token"
    payload = st.session_state.get("_rm_payload", "")
    if not payload or ":" not in payload:
        return False

    parts = payload.split(":", 1)
    if len(parts) != 2:
        return False

    username, raw_token = parts
    from user_manager import user_manager

    if user_manager.verify_remember_token(username, raw_token):
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.remember_token = raw_token
        return True

    # Token invalid / expired — clear it
    _clear_token_from_localstorage()
    return False


# ──────────────────────────────────────────────────────────────
# localStorage helpers  (JavaScript bridge)
# ──────────────────────────────────────────────────────────────

_LS_KEY = "databot_remember"   # key used in localStorage


def _write_token_to_localstorage(username: str, raw_token: str):
    """
    Inject a tiny JS snippet that:
      1. Saves "username:token" to localStorage under _LS_KEY.
      2. Reads it back and sets a hidden Streamlit query-param so the
         Python side can pick it up on the *next* page load via
         st.query_params or the component bridge below.

    Note: we use st.components.v1.html for the JS injection.
    """
    payload = f"{username}:{raw_token}"
    js = f"""
    <script>
      localStorage.setItem("{_LS_KEY}", "{payload}");
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)


def _clear_token_from_localstorage():
    """Remove the remember-me entry from localStorage."""
    js = f"""
    <script>
      localStorage.removeItem("{_LS_KEY}");
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)


def inject_localstorage_reader():
    """
    Render a hidden component that reads localStorage and feeds the value
    into st.session_state["_rm_payload"].  Call this *once* near the top
    of your main app file, before check_remembered_login().

    The component writes the payload into a hidden URL fragment that
    Streamlit reads back via st.query_params on the next render cycle.
    Because of Streamlit's single-threaded rerun model, the auto-login
    will take effect on the *second* render (after the JS has run).
    """
    import streamlit.components.v1 as components
    components.html(
        f"""
        <script>
          const val = localStorage.getItem("{_LS_KEY}");
          if (val) {{
            // Post the payload to the parent Streamlit window
            window.parent.postMessage({{
              type: "streamlit:setComponentValue",
              value: val
            }}, "*");
          }}
        </script>
        """,
        height=0,
        key="_rm_reader",
    )


# ──────────────────────────────────────────────────────────────
# Legacy shim  (keeps existing call-sites working)
# ──────────────────────────────────────────────────────────────

def get_remembered_credentials() -> tuple[str, str, bool]:
    """
    Backward-compatible shim used by render_login_page() to pre-fill
    the username field.  We no longer store the password anywhere, so
    password is always returned as an empty string.
    """
    username = st.session_state.get("username") or ""
    has_token = bool(st.session_state.get("remember_token"))
    return username, "", has_token


def save_remembered_credentials(username: str, password: str, remember_me: bool):
    """
    Legacy shim — no-op.  Token creation is now handled inside login_user().
    Kept so existing imports don't break.
    """
    pass  # intentionally empty