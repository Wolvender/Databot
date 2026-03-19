# ui_components.py - Reusable UI components and rendering
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from io import BytesIO
from config import STREAMLIT_THEME, LOGO_SVG, APP_NAME

def apply_theme():
    """Apply premium theme styling to the app using config settings."""
    st.markdown(STREAMLIT_THEME, unsafe_allow_html=True)

def render_header():
    """Render a clean, premium app header with logo, name, and tagline. Returns 'logout' if Sign Out clicked."""
    
    # Top bar with Sign Out button
    col1, col2 = st.columns([1, 6])
    with col1:
        if st.button("Sign Out", type="secondary", use_container_width=True):
            return "logout"
    
    st.markdown(
"""
<div class="main-header">
    <div class="logo">
        <svg width="60" height="60" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="50" cy="50" r="45" stroke="white" stroke-width="6" stroke-dasharray="10 10"/>
            <path d="M30 50 L45 65 L70 35" stroke="white" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        DataBot
    </div>
    <p>Intelligent Document Extraction – Fast, Accurate, Secure</p>
</div>
""", unsafe_allow_html=True)
    return None

def render_login_page() -> tuple[str, str, str, bool]:
    """
    Render premium login/signup page. Returns (action, username, password, remember_me).
    """
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"
        
    from auth import get_remembered_credentials
    rem_user, rem_pass, is_rem = get_remembered_credentials()
        
    # Apply glass-card to the specific stForm container so it doesn't break Streamlit DOM
    st.markdown('<style>[data-testid="stForm"] { background: rgba(30, 30, 30, 0.72); backdrop-filter: blur(18px); padding: 2.2rem; border-radius: 20px; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 10px 38px rgba(0,0,0,0.45); }</style>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.auth_mode == "login":
            st.markdown("<h3 style='text-align:center; color: #6b21a8; margin-bottom: 1.5rem;'>Sign In</h3>", unsafe_allow_html=True)
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username", value=rem_user, placeholder="admin / user", autocomplete="username")
                password = st.text_input("Password", type="password", value=rem_pass, placeholder="•••••••", autocomplete="current-password")
                remember_me = st.checkbox("Remember me on this device", value=is_rem)
                submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
            
            st.markdown("<p style='text-align:center; margin-top: 1rem; opacity: 0.8;'>Need an account?</p>", unsafe_allow_html=True)
            if st.button("Sign Up Now", use_container_width=True):
                st.session_state.auth_mode = "signup"
                st.rerun()
                
            if submitted:
                return "login", username, password, remember_me
        else:
            st.markdown("<h3 style='text-align:center; color: #6b21a8; margin-bottom: 1.5rem;'>Create Account</h3>", unsafe_allow_html=True)
            with st.form("signup_form", clear_on_submit=False):
                username = st.text_input("New Username", placeholder="Choose a username", autocomplete="username")
                password = st.text_input("New Password", type="password", placeholder="•••••••", autocomplete="new-password")
                remember_me = st.checkbox("Remember me on this device", value=True)
                submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)
            
            st.markdown("<p style='text-align:center; margin-top: 1rem; opacity: 0.8;'>Already have an account?</p>", unsafe_allow_html=True)
            if st.button("Sign In Instead", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()
                
            if submitted:
                return "signup", username, password, remember_me
    
    return None, "", "", False

def render_sidebar(username: str):
    """Sidebar removed as per user request."""
    return None

def render_upload_section(processed_count: int):
    """Render file upload section."""
    st.title("Upload & Process")
    st.markdown("Upload invoices, timesheets, receipts or any documents → get structured data ready for Excel/ERP")
    
    st.markdown("""
    **How to upload many files at once:**
    - Click **Browse files** → go to your folder → press **Ctrl+A** (select all) → Open
    - Or drag & drop files directly from your file explorer (hold Ctrl to select many)
    """)
    
    if processed_count > 0:
        col_btn = st.columns([1, 3, 1])[1]
        with col_btn:
            if st.button("🔍 View Results Now", type="primary", use_container_width=True):
                st.session_state.current_tab = "View Results"
                st.rerun()
    
    uploaded_files = st.file_uploader(
        "Upload files (PDF or TXT)",
        accept_multiple_files=True,
        type=["pdf", "txt"],
        key=f"uploader_{st.session_state.uploader_key}"
    )
    
    return uploaded_files

def render_processing_status(uploaded_files, process_callback):
    """
    Render file processing with progress bar.
    process_callback: function(file_bytes, file_name) -> (success, message)
    """
    if not uploaded_files:
        return 0, 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total = len(uploaded_files)
    processed_count = 0
    skipped_count = 0
    
    from file_handler import get_file_hash
    
    for i, file in enumerate(uploaded_files):
        file_name = file.name
        file_bytes = file.read()
        file_hash = get_file_hash(file_bytes)
        
        if file_hash in st.session_state.processed_hashes:
            skipped_count += 1
            status_text.text(f"Skipped (identical content): {file_name}")
        else:
            with st.spinner(f"Processing {file_name}..."):
                success, msg = process_callback(file_bytes, file_name)
                status_text.text(msg)
                if success:
                    processed_count += 1
                else:
                    st.warning(msg)
        
        progress_bar.progress((i + 1) / total)
    
    if processed_count > 0 or skipped_count > 0:
        st.markdown(f"""
            <div class="result-banner">
                ✅ Processing finished!
                New files processed: {processed_count} • Skipped (already done): {skipped_count}
            </div>
        """, unsafe_allow_html=True)
    
    return processed_count, skipped_count

def render_results_table(processed_items: list):
    """Render summary table of processed results."""
    st.subheader(f"Processed Documents ({len(processed_items)})")
    
    summary_data = []
    for item in processed_items:
        data = item["data"]
        summary_data.append({
            "File": item["file"],
            "Record #": item["record_index"] + 1,
            "Entity": data.get("entity", data.get("vendor_name", data.get("employee_name", "N/A"))),
            "Date": data.get("date", data.get("invoice_date", "N/A")),
            "Amount": data.get("amount", data.get("total_amount", 0.0)),
            "Currency": data.get("currency", "N/A"),
            "Description": data.get("description", "N/A"),
            "Status": item["status"].upper(),
            "Confidence": f"{item['confidence']:.2f}"
        })
    
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(
        df_summary,
        column_config={
            "Confidence": st.column_config.NumberColumn(format="%.2f"),
            "Issues": st.column_config.NumberColumn()
        },
        hide_index=True,
        use_container_width=True
    )
    
    return df_summary

def render_download_section(df_summary: pd.DataFrame, processed_items: list):
    """Render download buttons for results."""
    st.subheader("Download Results")
    
    col1, col2, col3 = st.columns(3)
    
    # CSV Download
    with col1:
        csv_summary = df_summary.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Summary CSV",
            csv_summary,
            f"databot_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            "text/csv"
        )
    
    # JSON Download
    with col2:
        full_json = json.dumps([item["raw"] for item in processed_items], indent=2)
        st.download_button(
            "Download Full JSON",
            full_json,
            f"databot_full_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            "application/json"
        )
    
    # Excel Download
    with col3:
        if st.button("Generate & Download Excel"):
            with st.spinner("Generating Excel file..."):
                output = BytesIO()
                df_summary.to_excel(output, index=False, engine='openpyxl')
                output.seek(0)

                st.download_button(
                    "Download Excel (.xlsx)",
                    output,
                    f"databot_results_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

def render_detailed_results(processed_items: list, remove_callback):
    """Detailed results removed as per user request."""
    pass

def render_empty_results():
    """Render message when no results available."""
    st.info("Upload files to start extracting data.")

def render_upgrade_page(username: str):
    """Render pricing, subscription tier, cost tracking, and upgrade options."""
    import streamlit as st
    from config_enterprise import SubscriptionTier, PRICING, EnterpriseConfig, get_user_tier
    from rate_limiter import rate_limiter
    
    current_tier = get_user_tier(username)
    
    # Get limits and period for current tier
    limit = EnterpriseConfig.RATE_LIMITS[current_tier]
    # rate_limiter.get_remaining respects the tier-based reset period now
    usage = rate_limiter.get_remaining(username)
    period_seconds = EnterpriseConfig.RESET_PERIODS.get(current_tier, 3600)
    
    def format_period(seconds):
        if seconds >= 2592000: return "month"
        if seconds == 1209600: return "2 weeks"
        if seconds == 604800: return "week"
        if seconds == 86400: return "day"
        if seconds == 3600: return "hour"
        return f"{int(seconds/86400)} days"

    period_str = format_period(period_seconds)
    
    # Calculate usage
    used = limit - usage
    if used < 0: used = 0 # Safety check
    
    st.title("My Subscription")
    
    # Hero section with current plan
    col_info, col_stats = st.columns([1, 1])
    
    with col_info:
        st.subheader("Current Plan")
        st.markdown(f"# {current_tier.value.title()}")
        price = PRICING[current_tier]
        price_txt = "Free" if price == 0 else f"€{price}/{period_str}"
        st.markdown(f"**{price_txt}**")
        
        # Avoid showing progress bar for Unlimited plans
        if limit >= 1000000000:
            st.info("∞ Unlimited usage")
        elif limit > 0:
            st.progress(used / limit, text=f"Usage: {used} / {limit} files per {period_str}")
        else:
            st.info("Unlimited usage")
    
    with col_stats:
        st.subheader("Plan Limits")
        config = EnterpriseConfig.get_tier_config(current_tier)
        st.write(f"• **Quota:** {config['rate_limit']} files / {period_str}")
        st.write(f"• **File Size:** {config['file_size_limit']} MB")
        st.write(f"• **AI Models:** {', '.join(config['allowed_models'])}")

    st.markdown("---")
    st.subheader("Upgrade Options")
    
    cols = st.columns(4)
    tiers = [SubscriptionTier.FREE, SubscriptionTier.STARTER, SubscriptionTier.PROFESSIONAL, SubscriptionTier.ENTERPRISE]
    
    for i, tier in enumerate(tiers):
        with cols[i]:
            tp_seconds = EnterpriseConfig.RESET_PERIODS.get(tier, 3600)
            tp_str = format_period(tp_seconds)
            limit_val = EnterpriseConfig.RATE_LIMITS[tier]
            
            is_current = (tier == current_tier)
            st.markdown(f"### {tier.value.title()}")
            
            # Pricing
            p_val = PRICING[tier]
            p_display = "Free" if p_val == 0 else f"€{p_val}"
            st.markdown(f"**{p_display}** / {tp_str}")
            
            # Limits details
            if limit_val >= 1000000000:
                st.markdown("**Unlimited** files")
            else:
                st.markdown(f"**{limit_val}** files")
                
            st.caption(f"Resets every {tp_str}")
            st.caption(f"Max size: {EnterpriseConfig.FILE_SIZE_LIMITS[tier]}MB")
            
            # Feature check
            feats = EnterpriseConfig.get_tier_config(tier)["features"]
            if feats.get("priority_support"): st.caption("✅ Priority Support")
            if feats.get("api_access"): st.caption("✅ API Access")
            
            if is_current:
                st.button("Current Plan", key=f"btn_{tier}", disabled=True, use_container_width=True)
            else:
                if st.button("Upgrade", key=f"btn_{tier}", use_container_width=True):
                    st.toast("🚧 Upgrades are currently under construction!", icon="🚧")
                    st.warning("Payment processing is under construction. Upgrades are temporarily disabled.", icon="🚧")