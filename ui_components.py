# ui_components.py - Reusable UI components and rendering
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from io import BytesIO
from config import STREAMLIT_THEME, LOGO_SVG, APP_NAME

def apply_theme():
    """Apply premium theme styling to the app."""
    # Updated CSS with dark purple and dark gray theme
    # Dark gray for backgrounds (#111827), dark purple for accents (#6b21a8)
    # Added cool effects: glassmorphism, hover transitions, subtle animations
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * {
        font-family: 'Inter', sans-serif !important;
    }

    .stApp {
        background-color: #111827; /* Dark gray background */
        color: #e0e0e0;
    }

    .stSidebar {
        background-color: #1f2937; /* Darker gray for sidebar */
        border-right: 1px solid #374151;
    }

    /* Global: Hide kbd elements */
    kbd {
        display: none !important;
    }

    /* Targeted: Hide only shortcut containers (usually spans) in buttons */
    /* Sidebar buttons */
    [data-testid="stSidebar"] button span[class*="keyboard"],
    [data-testid="stSidebar"] button span:nth-child(2),
    [data-testid="stSidebar"] button svg {
        display: none !important;
    }

    /* Expander buttons */
    .stExpander button span[class*="keyboard"],
    .stExpander button svg {
        display: none !important;
    }

    /* Ensure text (usually in div or p) remains VISIBLE */
    button div,
    button p {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }

    /* Premium header with gradient (dark purple theme) */
    .main-header {
        background: linear-gradient(135deg, #6b21a8, #581c87); /* Dark purple gradient */
        padding: 1.5rem 2rem;
        border-radius: 0 0 12px 12px;
        margin: -1rem -2rem 2rem -2rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        animation: fadeInHeader 1s ease-out;
    }

    @keyframes fadeInHeader {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .main-header h1 {
        margin: 0;
        font-size: 2.2rem;
    }

    .main-header p {
        margin: 4px 0 0;
        opacity: 0.9;
    }

    /* Buttons with hover effects */
    .stButton > button {
        background-color: #6b21a8; /* Dark purple */
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 600;
        width: 100%;
        margin-bottom: 8px;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background-color: #581c87; /* Darker purple */
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(106,33,168,0.3);
    }

    .stButton > button:disabled {
        background-color: #374151;
        color: #9ca3af;
    }

    .stSuccess {
        background-color: #064e3b;
        color: #a7f3d0;
        border: 1px solid #10b981;
        border-radius: 8px;
        padding: 12px;
    }

    .stExpander {
        background-color: #1f2937; /* Dark gray glass effect */
        border: 1px solid #374151;
        border-radius: 8px;
        margin-bottom: 12px;
        transition: all 0.3s ease;
    }

    .stExpander:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }

    .stExpander > div > div {
        line-height: 1.6;
        padding: 12px;
    }

    /* Hide keyboard shortcuts in expanders */
    .stExpander kbd,
    .stExpander button kbd {
        display: none !important;
    }

    .stDataFrame {
        background-color: #111827; /* Dark gray */
    }

    hr {
        border-color: #374151;
    }

    .stSpinner {
        text-align: center;
    }

    .result-banner {
        background-color: #6b21a8; /* Dark purple banner */
        color: #e0e0e0;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #581c87;
        margin: 16px 0;
        font-size: 1.1em;
        text-align: center;
        animation: fadeInBanner 0.8s ease-out;
    }

    @keyframes fadeInBanner {
        from { opacity: 0; transform: scale(0.95); }
        to { opacity: 1; transform: scale(1); }
    }

    /* Glassmorphism for cards (cool premium effect) */
    .glass-card {
        background: rgba(55, 65, 81, 0.5); /* Semi-transparent dark gray */
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }

    .glass-card:hover {
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def render_header():
    """Render a clean, premium app header with logo, name, and tagline. Returns 'logout' if Sign Out clicked."""
    
    # Top bar with Sign Out button
    col1, col2 = st.columns([1, 6])
    with col1:
        if st.button("Sign Out", type="secondary", use_container_width=True):
            return "logout"
    
    st.markdown("""
        <div class="main-header">
            <div class="logo">
                <!-- Simple SVG logo (replace later if needed) -->
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

def render_login_page() -> tuple[str, str, bool]:
    """
    Render login page with full Remember Me (User + Password).
    Note: Storing passwords in localStorage is not secure for production.
    """
    st.title("Welcome to DataBot")
    st.markdown("Intelligent Document Extraction – Fast, Secure, Accurate")

    # JavaScript to handle localStorage for username AND password
    # Loaded from external file for cleanliness
    login_js = ""
    try:
        with open("login_script.js", "r") as f:
            login_js = f.read()
    except FileNotFoundError:
        st.error("Error: login_script.js not found.")

    st.components.v1.html(f"<script>{login_js}</script>", height=0)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h3 style='text-align:center;'>Sign In</h3>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin / user", autocomplete="username")
            password = st.text_input("Password", type="password", placeholder="•••••••", autocomplete="current-password")
            remember_me = st.checkbox("Remember me", value=False)
            
            submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
        
        if submitted:
            # Send JS message to save/clear creds
            if remember_me:
                st.components.v1.html(
                    f"""<script>
                    window.parent.postMessage({{type: 'save_creds', u: '{username}', p: '{password}'}}, '*');
                    </script>""", 
                    height=0
                )
            else:
                st.components.v1.html(
                    "<script>window.parent.postMessage({type: 'clear_creds'}, '*');</script>", 
                    height=0
                )
            return username, password, remember_me
    
    return "", "", False

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
                    from user_manager import user_manager
                    if user_manager.update_tier(username, tier):
                        st.toast(f"🎉 Upgraded to {tier.value.title()}!", icon="🚀")
                        # Allow UI update
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Error updating plan.")