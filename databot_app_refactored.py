# databot_app_refactored.py - Main Streamlit application (modularized)
"""
DataBot - Intelligent Document Extraction & Data Entry
Refactored version with modular architecture
"""

import streamlit as st
import os
from pathlib import Path

# Import all modules
from config import PAGE_TITLE, PAGE_ICON, PAGE_LAYOUT
from auth import initialize_session_state, is_logged_in, get_current_username, login_user, logout_user
from data_processor import DataProcessor
from ui_components import (
    apply_theme,
    render_header,
    render_login_page,
    render_upload_section,
    render_processing_status,
    render_results_table,
    render_empty_results,
    render_download_section,
    render_upgrade_page
)


# ════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ════════════════════════════════════════════════════════════
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout=PAGE_LAYOUT)

# Apply theme
apply_theme()

# ════════════════════════════════════════════════════════════
# INITIALIZATION
# ════════════════════════════════════════════════════════════
initialize_session_state()
processor = DataProcessor()

# ════════════════════════════════════════════════════════════
# AUTHENTICATION FLOW
# ════════════════════════════════════════════════════════════
if not is_logged_in():
    render_header()
    username, password, remember_me = render_login_page()
    
    if username and password:
        if login_user(username, password, remember_me):
            st.success("Signed in successfully")
            st.rerun()
        else:
            st.error("Invalid credentials")
    
    st.stop()

# ════════════════════════════════════════════════════════════
# LOGGED-IN APPLICATION
# ════════════════════════════════════════════════════════════
# Render header and check for logout action
header_action = render_header()
if header_action == "logout":
    logout_user()
    st.rerun()

# Sidebar removed as per user request
# sidebar_action = render_sidebar(get_current_username())

# Main content tabs
tab_upload, tab_results, tab_account = st.tabs(["Upload & Process", "View Results", "Account & Billing"])

# ────────────────────────────────────────────────────────────
# TAB 1: Upload & Process
# ────────────────────────────────────────────────────────────
with tab_upload:
    uploaded_files = render_upload_section(len(st.session_state.processed))
    
    if uploaded_files:
        # Wrapper to enforce rate limits per file
        def rate_limited_process(file_bytes, file_name):
            from rate_limiter import rate_limiter
            user = get_current_username()
            allowed, retry_after = rate_limiter.is_allowed(user)
            
            if not allowed:
                return False, f"⚠️ Rate limit exceeded! Retry in {retry_after}s or Upgrade."
            
            return processor.process_content(file_bytes, file_name)

        processed_count, skipped_count = render_processing_status(
            uploaded_files,
            rate_limited_process
        )

# ────────────────────────────────────────────────────────────
# TAB 2: View Results
# ────────────────────────────────────────────────────────────
with tab_results:
    st.title("Processed Results")
    
    if st.session_state.processed:
        # Render summary table
        df_summary = render_results_table(st.session_state.processed)
        
        # Clear all button
        if st.button("Clear All Processed Data"):
            processor.clear_history()
            st.success("History cleared! Uploader and saved file reset.")
            st.rerun()
        
        # Download section
        render_download_section(df_summary, st.session_state.processed)
        
        # Detailed results removed as per user request
        # render_detailed_results(
        #     st.session_state.processed,
        #     processor.remove_entry
        # )
    else:
        render_empty_results()

# ────────────────────────────────────────────────────────────
# TAB 3: Account & Billing
# ────────────────────────────────────────────────────────────
with tab_account:
    render_upgrade_page(get_current_username())

