# ui_components.py - Reusable UI components and rendering
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from io import BytesIO
from pathlib import Path
from config import STREAMLIT_THEME, LOGO_SVG, APP_NAME

def apply_theme():
    """Apply premium theme styling to the app using config settings and custom CSS."""
    st.markdown(STREAMLIT_THEME, unsafe_allow_html=True)
    # Correct pathing: Ensure the path is relative or absolute as required by the environment
    css_path = Path("style.css")
    if css_path.exists():
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def render_header(show_logout: bool = True):
    """Render a slim top bar with logo, name, and sign-out. Returns 'logout' if Sign out clicked."""
    action = None
    col_brand, col_actions = st.columns([5, 1], vertical_alignment="center")

    with col_brand:
        st.markdown(f"""
<div class="app-topbar">
    <div class="logo-mark">{LOGO_SVG}</div>
    <span class="wordmark">{APP_NAME}</span>
    <span class="subtitle">Document extraction</span>
</div>
""", unsafe_allow_html=True)

    if show_logout:
        with col_actions:
            if st.button("Sign out", type="secondary", width="stretch"):
                action = "logout"

    st.markdown('<div class="app-divider"></div>', unsafe_allow_html=True)
    return action

def render_login_page() -> tuple[str, str, str, bool]:
    """
    Render premium login/signup page. Returns (action, username, password, remember_me).
    """
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"
        
    from auth import get_remembered_credentials
    rem_user, rem_pass, is_rem = get_remembered_credentials()

    col1, col2, col3 = st.columns([1.5, 2, 1.5])
    with col2:
        if st.session_state.auth_mode == "login":
            with st.form("login_form", clear_on_submit=False):
                st.markdown("<h3 class='auth-title'>Sign in</h3>", unsafe_allow_html=True)
                username = st.text_input("Username", value=rem_user, placeholder="Your username", autocomplete="username")
                password = st.text_input("Password", type="password", value=rem_pass, placeholder="Your password", autocomplete="current-password")
                remember_me = st.checkbox("Remember me on this device", value=is_rem)
                st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
                submitted = st.form_submit_button("Sign in", type="primary", width="stretch")
                st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
                switch = st.form_submit_button("Create an account", width="stretch")

            if switch:
                st.session_state.auth_mode = "signup"
                st.rerun()
            if submitted:
                return "login", username, password, remember_me
        else:
            with st.form("signup_form", clear_on_submit=False):
                st.markdown("<h3 class='auth-title'>Create account</h3>", unsafe_allow_html=True)
                username = st.text_input("Username", placeholder="Choose a username", autocomplete="username")
                password = st.text_input("Password", type="password", placeholder="Choose a password", autocomplete="new-password")
                remember_me = st.checkbox("Remember me on this device", value=True)
                st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
                submitted = st.form_submit_button("Create account", type="primary", width="stretch")
                st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
                switch = st.form_submit_button("Sign in instead", width="stretch")

            if switch:
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
    st.title("Upload & process")
    st.caption("Upload invoices, timesheets or receipts and get structured data back, ready for Excel or your ERP.")

    uploaded_files = st.file_uploader(
        "Upload files (PDF or TXT)",
        accept_multiple_files=True,
        type=["pdf", "txt"],
        key=f"uploader_{st.session_state.uploader_key}",
        label_visibility="hidden",
        help="Select multiple files at once: Ctrl+A in the file dialog, or drag and drop a selection from your file explorer."
    )

    if processed_count > 0:
        if st.button("View results", type="primary"):
            st.session_state.current_tab = "View Results"
            st.rerun()

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
                Processing finished — {processed_count} new, {skipped_count} skipped (already processed).
            </div>
        """, unsafe_allow_html=True)

    return processed_count, skipped_count

def build_summary_frames(processed_items: list) -> dict:
    """Build one summary DataFrame per document type (columns differ per type)."""
    summary_data = []
    for item in processed_items:
        data = item["data"]
        doc_type = item.get("document_type", "ledger")
        # ledger and invoice share the same schema — merge them into one group
        if doc_type == "ledger":
            doc_type = "invoice"

        row = {
            "File": item["file"],
            "Type": doc_type.upper(),
            "Record #": item.get("record_index", 0) + 1,
        }

        # Adaptive columns based on doc_type
        if doc_type == "inventory":
            row.update({
                "Item": data.get("item_name", "N/A"),
                "SKU": data.get("sku", "N/A"),
                "Quantity": data.get("quantity", 0),
                "Location": data.get("location", "N/A"),
            })
        elif doc_type == "timesheet":
            row.update({
                "Employee": data.get("employee", "N/A"),
                "Period": data.get("period", "N/A"),
                "Project": data.get("project", "N/A"),
                "Hours": data.get("hours", 0.0),
                "Rate": data.get("rate", "N/A"),
            })
        else:
            # Default to Ledger/Invoice columns
            row.update({
                "Entity": data.get("entity", data.get("vendor_name", "N/A")),
                "Date": data.get("date", "N/A"),
                "Reference": data.get("reference", "N/A"),
                "Amount": data.get("amount", 0.0),
                "Tax": data.get("tax_amount", 0.0),
                "Currency": data.get("currency", "N/A"),
                "Due date": data.get("due_date", "N/A"),
            })

        row.update({
            "Status": item["status"].upper(),
            "Confidence": f"{item.get('confidence', 0.0):.2f}"
        })
        summary_data.append(row)

    frames = {}
    df_all = pd.DataFrame(summary_data)
    for doc_type in df_all["Type"].unique():
        df_type = df_all[df_all["Type"] == doc_type].dropna(axis=1, how="all")
        # Consistent column order regardless of upload order: data fields
        # in the middle, Status/Confidence always at the end
        ordered = [c for c in df_type.columns if c not in ("Status", "Confidence")] + ["Status", "Confidence"]
        frames[doc_type] = df_type[ordered].reset_index(drop=True)
    return frames


_TYPE_LABELS = {
    "INVOICE": "Invoices & payments",
    "LEDGER": "Invoices & payments",
    "INVENTORY": "Inventory",
    "TIMESHEET": "Timesheets",
}


def render_results_table(processed_items: list) -> dict:
    """Render one summary table per document type. Returns the frames dict."""
    st.subheader(f"Processed documents ({len(processed_items)})")

    if not processed_items:
        return {}

    frames = build_summary_frames(processed_items)
    for doc_type, df_type in frames.items():
        st.markdown(f"**{_TYPE_LABELS.get(doc_type, doc_type.title())}** — {len(df_type)} records")
        st.dataframe(df_type, hide_index=True, width="stretch")

    return frames

def render_download_section(frames: dict, processed_items: list):
    """Render download buttons for results. `frames` is one DataFrame per document type."""
    st.subheader("Download results")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M')

    # Excel export scope chooser — rendered above the button row so the three
    # download buttons line up on the same baseline.
    # Map each available label to its doc_type key(s); group keys that share a
    # label (e.g. invoice/ledger) so they export together.
    label_to_types: dict = {}
    for dt in frames.keys():
        label = _TYPE_LABELS.get(dt, dt.title())
        label_to_types.setdefault(label, []).append(dt)

    export_options = ["All types"] + list(label_to_types.keys())
    selected = st.selectbox(
        "What to export (Excel)",
        export_options,
        key="excel_export_choice",
    )

    if selected == "All types":
        export_frames = frames
        file_suffix = "all"
    else:
        export_frames = {dt: frames[dt] for dt in label_to_types[selected]}
        file_suffix = selected.lower().replace(" & ", "_").replace(" ", "_")

    col1, col2, col3 = st.columns(3)

    # CSV Download — all types stacked, empty cells where columns differ
    with col1:
        df_combined = pd.concat(frames.values(), ignore_index=True) if frames else pd.DataFrame()
        csv_summary = df_combined.fillna("").to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download CSV",
            csv_summary,
            f"databot_summary_{timestamp}.csv",
            "text/csv",
            width="stretch"
        )

    # JSON Download — full records including validation issues and confidence
    with col2:
        export_items = [
            {
                "file": item.get("file"),
                "document_type": item.get("document_type"),
                "timestamp": item.get("timestamp"),
                "data": item.get("data", {}),
                "confidence": item.get("confidence", 0.0),
                "validation_issues": item.get("validation_issues", []),
                "status": item.get("status"),
            }
            for item in processed_items
        ]
        full_json = json.dumps(export_items, indent=2, ensure_ascii=False)
        st.download_button(
            "Download JSON",
            full_json,
            f"databot_full_{timestamp}.json",
            "application/json",
            width="stretch"
        )

    # Excel Download — exports the scope chosen in the selector above
    with col3:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for doc_type, df_type in export_frames.items():
                sheet = _TYPE_LABELS.get(doc_type, doc_type.title())[:31]
                df_type.to_excel(writer, sheet_name=sheet, index=False)
        st.download_button(
            "Download Excel",
            output.getvalue(),
            f"databot_{file_suffix}_{timestamp}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch"
        )

def render_detailed_results(processed_items: list, remove_callback):
    """Detailed results removed as per user request."""
    pass

def render_empty_results():
    """Render message when no results available."""
    st.caption("Nothing here yet — upload files in the first tab to start extracting data.")

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
    
    st.title("Subscription")

    # Hero section with current plan
    col_info, col_stats = st.columns([1, 1])

    with col_info:
        st.subheader("Current plan")
        st.markdown(f"# {current_tier.value.title()}")
        price = PRICING[current_tier]
        price_txt = "Free" if price == 0 else f"€{price}/{period_str}"
        st.markdown(f"**{price_txt}**")

        # Avoid showing progress bar for Unlimited plans
        if limit >= 1000000000 or limit <= 0:
            st.caption("Unlimited usage")
        else:
            st.progress(used / limit, text=f"Usage: {used} / {limit} files per {period_str}")

    with col_stats:
        st.subheader("Plan limits")
        config = EnterpriseConfig.get_tier_config(current_tier)
        st.write(f"**Quota:** {config['rate_limit']} files / {period_str}")
        st.write(f"**File size:** {config['file_size_limit']} MB")
        st.write(f"**AI models:** {', '.join(config['allowed_models'])}")

    st.markdown("---")
    st.subheader("Plans")

    cols = st.columns(4)
    tiers = [SubscriptionTier.FREE, SubscriptionTier.STARTER, SubscriptionTier.PROFESSIONAL, SubscriptionTier.ENTERPRISE]

    for i, tier in enumerate(tiers):
        with cols[i], st.container(border=True):
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
                st.markdown(f"**{limit_val:,}** files")

            st.caption(f"Resets every {tp_str}")
            st.caption(f"Max size: {EnterpriseConfig.FILE_SIZE_LIMITS[tier]} MB")

            # Feature check
            feats = EnterpriseConfig.get_tier_config(tier)["features"]
            if feats.get("priority_support"): st.caption("Priority support")
            if feats.get("api_access"): st.caption("API access")

            if is_current:
                st.button("Current plan", key=f"btn_{tier}", disabled=True, width="stretch")
            else:
                if st.button("Upgrade", key=f"btn_{tier}", type="primary", width="stretch"):
                    st.info("Payments aren't live yet — upgrades will be available soon.")