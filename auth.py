# auth.py - Authentication and session management
import hashlib
import streamlit as st
def check_password(username: str, password: str) -> bool:
    """Verify credentials against stored users."""
    try:
        from user_manager import user_manager
        return user_manager.verify_password(username, password)
    except ImportError:
        # Fallback if user_manager fails for some reason
        return False

def initialize_session_state():
    """Initialize all session state variables."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "remembered_username" not in st.session_state:
        st.session_state.remembered_username = ""

def is_logged_in() -> bool:
    """Check if user is currently logged in."""
    return st.session_state.get("logged_in", False)

def get_current_username() -> str:
    """Get the current logged-in user's username."""
    return st.session_state.get("username", "Unknown")

def login_user(username: str, password: str, remember_me: bool = False) -> bool:
    """Handle user login."""
    if check_password(username, password):
        st.session_state.logged_in = True
        st.session_state.username = username
        
        # Remember username for next login (pre-fill)
        if remember_me:
            st.session_state.remembered_username = username
        else:
            st.session_state.remembered_username = ""
        
        return True
    return False

def logout_user():
    """Handle user logout."""
    st.session_state.logged_in = False
    st.session_state.username = None
    # Don't clear remembered_username on logout

def get_remembered_username() -> str:
    """Get remembered username if exists."""
    return st.session_state.get("remembered_username", "")
