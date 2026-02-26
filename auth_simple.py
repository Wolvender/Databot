# auth_simple.py - Simplified authentication with working Remember Me
import hashlib
import streamlit as st
from config import USERS

def check_password(username: str, password: str) -> bool:
    """Verify credentials against stored users."""
    if username not in USERS:
        return False
    
    # Hash provided password
    hashed = hashlib.sha256(password.encode()).hexdigest()
    stored_hash = hashlib.sha256(USERS[username].encode()).hexdigest()
    
    return hashed == stored_hash

def initialize_session_state():
    """Initialize all session state variables."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None

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
        
        # Simple remember me - just pre-fill username
        if remember_me:
            st.session_state.remembered_username = username
        
        return True
    return False

def logout_user():
    """Handle user logout."""
    st.session_state.logged_in = False
    st.session_state.username = None

def get_remembered_username() -> str:
    """Get remembered username if exists."""
    return st.session_state.get("remembered_username", "")
