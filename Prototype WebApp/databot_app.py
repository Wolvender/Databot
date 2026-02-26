# databot_app.py - Fixed overlap + premium header with SVG logo + all previous fixes + applied fixes + dark purple gray theme + removed filenames from expander labels
import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pypdf import PdfReader
import pandas as pd
from io import BytesIO
import hashlib

# ────────────────────────────────────────────────
# Persistent history file
# ────────────────────────────────────────────────
HISTORY_FILE = "history.json"

# ────────────────────────────────────────────────
# Load environment variables
# ────────────────────────────────────────────────
load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    st.error("Missing GROQ_API_KEY in .env file. Please add it and restart.")
    st.stop()

# ────────────────────────────────────────────────
# Page config
# ────────────────────────────────────────────────
st.set_page_config(page_title="DataBot – Intelligent Data Entry", page_icon="📊", layout="wide")

# Premium theme with fixed expander overlap
# Premium theme – dark purple and dark gray, trustworthy look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * {
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    }

    .stApp {
        background: #121212;
        color: #e0e0e0;
    }

    header, .stApp > header { 
        display: none !important; 
    }

    /* Premium header */
    .main-header {
        background: linear-gradient(135deg, #4a148c, #6a1b9a, #8e24aa);
        padding: 2.8rem 4rem;
        border-radius: 0 0 28px 28px;
        margin: -1rem -2rem 3.5rem -2rem;
        color: white;
        text-align: center;
        box-shadow: 0 12px 48px rgba(0,0,0,0.55);
    }

    .main-header .logo {
        font-size: 3.8rem;
        font-weight: 800;
        letter-spacing: -1.2px;
        margin: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1.2rem;
    }

    .main-header .logo svg {
        width: 64px;
        height: 64px;
    }

    .main-header p {
        font-size: 1.35rem;
        opacity: 0.92;
        margin: 14px 0 0;
        letter-spacing: 0.4px;
    }

    /* Glassmorphic cards – deeper & more premium */
    .glass-card {
        background: rgba(30, 30, 30, 0.72);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 20px;
        padding: 2.2rem;
        margin: 2.2rem 0;
        box-shadow: 0 10px 38px rgba(0,0,0,0.45);
    }

    /* Expander – clean, no overlap, better spacing */
    .stExpander {
        background: rgba(30, 30, 30, 0.7) !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        border-radius: 16px !important;
        margin-bottom: 1.8rem !important;
    }

    .stExpander summary {
        padding: 1.5rem 1.8rem !important;
        font-weight: 600 !important;
        color: #f0f0f0 !important;
        font-size: 1.15rem !important;
        line-height: 1.5 !important;
    }

    .stExpander > div > div {
        padding: 1.6rem 1.8rem !important;
        font-size: 1rem !important;
        line-height: 1.7 !important;
        color: #e0e0e0 !important;
    }

    /* Buttons – more premium feel */
    .stButton > button {
        background: linear-gradient(90deg, #10b981, #059669) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 14px 32px !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        box-shadow: 0 6px 20px rgba(16,185,129,0.35) !important;
        transition: all 0.28s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 32px rgba(16,185,129,0.5) !important;
        background: linear-gradient(90deg, #34d399, #10b981) !important;
    }

    /* Tabs */
    .stTabs [role="tab"] {
        font-size: 1.12rem;
        padding: 16px 32px;
        color: #a0a0a0;
        transition: all 0.2s;
    }

    .stTabs [aria-selected="true"] {
        color: white;
        background: rgba(106,27,154,0.22);
        border-radius: 14px 14px 0 0;
    }

    /* Confidence helpers (can be used later with st.markdown) */
    .conf-high  { color: #34d399; font-weight: 600; }
    .conf-medium { color: #fbbf24; font-weight: 600; }
    .conf-low    { color: #f87171; font-weight: 600; }

    /* Other elements */
    .stSuccess { 
        background: #1e4620; 
        color: #c8e6c9; 
        border: 1px solid #4caf50; 
        border-radius: 12px; 
        padding: 12px; 
    }
    hr { border-color: #333333; }
    .stSpinner { text-align: center; }

    /* Result banner */
    .result-banner {
        background: rgba(16,185,129,0.1);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #10b981;
        border: 1px solid rgba(16,185,129,0.2);
    }

    /* Additional spacing for detailed results to prevent overlap */
    .stColumn > div > div {
        padding: 0.5rem;
    }

    </style>
""", unsafe_allow_html=True)

# Header with made-up SVG logo
st.markdown("""
    <div class="main-header">
        <div class="logo">
            <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="50" cy="50" r="45" stroke="white" stroke-width="6" stroke-dasharray="10 10"/>
                <path d="M30 50 L45 65 L70 35" stroke="white" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            DataBot
        </div>
        <p>Intelligent Document Extraction • Fast • Accurate • Secure</p>
    </div>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# Authentication + Remember Me
# ────────────────────────────────────────────────
def check_password(username, password):
    users = {
        "admin": hashlib.sha256("admin123".encode()).hexdigest(),
        "user": hashlib.sha256("user456".encode()).hexdigest()
    }
    hashed = hashlib.sha256(password.encode()).hexdigest()
    return username in users and users[username] == hashed

if "remembered_username" not in st.session_state:
    st.session_state.remembered_username = ""

js_remember = """
<script>
    const remembered = localStorage.getItem('databot_username');
    if (remembered) {
        parent.document.querySelector('input[aria-label="Username"]').value = remembered;
        parent.window.streamlit.setComponentValue({remembered_username: remembered});
    }
    window.addEventListener('message', function(e) {
        if (e.data.type === 'rememberMe') {
            if (e.data.checked) {
                localStorage.setItem('databot_username', e.data.username);
            } else {
                localStorage.removeItem('databot_username');
            }
        }
    });
</script>
"""

st.components.v1.html(js_remember, height=0)

if st.session_state.remembered_username:
    st.session_state.username_input = st.session_state.remembered_username

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None

# Login page
if not st.session_state.logged_in:
    st.title("Welcome to DataBot")
    st.markdown("Intelligent Document Extraction – Fast, Secure, Accurate")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h3 style='text-align:center;'>Sign In</h3>", unsafe_allow_html=True)
        username = st.text_input("Username", value=st.session_state.get("username_input", ""), placeholder="admin / user", key="username_input")
        password = st.text_input("Password", type="password", placeholder="•••••••")

        remember_me = st.checkbox("Remember me on this device", value=True)

        if st.button("Sign In", type="primary", use_container_width=True):
            if check_password(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.components.v1.html(
                    f"""
                    <script>
                        window.parent.postMessage({{
                            type: 'rememberMe',
                            checked: {str(remember_me).lower()},
                            username: '{username.replace("'", "\\'")}'
                        }}, '*');
                    </script>
                    """,
                    height=0
                )
                st.success("Signed in successfully")
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.stop()

# ────────────────────────────────────────────────
# Sidebar (minimal)
# ────────────────────────────────────────────────
st.sidebar.title("DataBot")
st.sidebar.markdown(f"**{st.session_state.username}**")
st.sidebar.markdown("---")

if st.sidebar.button("Sign Out"):
    st.session_state.logged_in = False
    st.session_state.username = None
    st.components.v1.html("<script>localStorage.removeItem('databot_username');</script>", height=0)
    st.rerun()

# ────────────────────────────────────────────────
# Load LLM
# ────────────────────────────────────────────────
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.1,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# ────────────────────────────────────────────────
# Persistent history
# ────────────────────────────────────────────────
if "processed" not in st.session_state:
    st.session_state.processed = []
if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()
if "processed_hashes" not in st.session_state:
    st.session_state.processed_hashes = set()
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if os.path.exists(HISTORY_FILE):
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            st.session_state.processed = loaded
            st.session_state.processed_files = {item["file"] for item in loaded}
            st.session_state.processed_hashes = {item.get("file_hash", "") for item in loaded}
    except Exception as e:
        st.warning(f"Could not load history: {e}. Starting fresh.")

def save_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.processed, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.warning(f"Could not save history: {e}")

# ────────────────────────────────────────────────
# Cleanup functions
# ────────────────────────────────────────────────
def clean_number(value):
    if not value:
        return value
    value = str(value).strip()
    for token in ["EUR", "EURO", "EUROS", "€", "USD", "$", "GBP", "£", "EUREUR", "euro", "eur"]:
        value = value.replace(token, "").strip()
    try:
        return float(value)
    except ValueError:
        return value

def normalize_currency(currency):
    if not currency:
        return "UNKNOWN"
    currency = str(currency).upper().strip().replace(" ", "")
    mapping = {
        "EUR": "EUR", "EURO": "EUR", "EUROS": "EUR", "€": "EUR", "EUREUR": "EUR",
        "USD": "USD", "DOLLAR": "USD", "DOLLARS": "USD", "$": "USD",
        "GBP": "GBP", "POUND": "GBP", "POUNDS": "GBP", "£": "GBP",
    }
    return mapping.get(currency, "UNKNOWN")

def get_file_hash(file_bytes: bytes):
    return hashlib.sha256(file_bytes).hexdigest()

# ────────────────────────────────────────────────
# System prompt
# ────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are DataBot – a precise enterprise-grade data extraction assistant.

Rules:
- Output ONLY valid JSON. No other text, no markdown, no explanations.
- Use snake_case keys.
- Infer meaningful field names (examples: employee_name, vendor_name, invoice_number, po_number, total_amount, currency, invoice_date, due_date, billing_period, hours_worked, rate_per_hour, project_code, description, quantity, unit_price, line_total, notes)
- Always include line_items array if multiple items are present.
- Numeric fields (total_amount, unit_price, line_total, hours_worked, rate_per_hour, quantity) MUST be pure numbers (no currency symbols, words, or text attached).
  - Do NOT write "2681.25 EUR" — write 2681.25 and put "EUR" in currency field only.
- Currency field: ALWAYS use ONLY the 3-letter ISO code (EUR, USD, GBP). NEVER include symbols (€, $) or words (euro, dollar).
  - Convert all variations ("euro", "EURO", "eur", "€", "euros") → "EUR"
  - Convert "dollar", "USD", "$" → "USD"
  - If unclear, set to "UNKNOWN" and add validation issue
- validation_issues MUST be array of objects: {"field": "...", "severity": "error|warning|info", "message": "..."}
- Return exactly this structure:

{
  "status": "complete" | "partial" | "needs_review" | "invalid",
  "document_type": "invoice" | "timesheet" | "receipt" | "purchase_order" | "unknown",
  "records": [
    {
      "extracted_fields": { ... },
      "validation_issues": [ ... ],
      "confidence": 0.0–1.0
    }
  ],
  "overall_confidence": 0.0–1.0,
  "summary": "short one-sentence summary"
}

If no useful data can be extracted, return status "invalid" with explanation in validation_issues.
"""

# ────────────────────────────────────────────────
# File text extraction
# ────────────────────────────────────────────────
def extract_text(file_bytes: bytes, file_name: str) -> str:
    ext = Path(file_name).suffix.lower()
    try:
        if ext == ".pdf":
            reader = PdfReader(BytesIO(file_bytes))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text.strip() or "[No extractable text in PDF]"
        elif ext in [".txt", ".eml"]:
            return file_bytes.decode("utf-8", errors="ignore").strip()
        else:
            return f"[Unsupported file type: {ext}]"
    except Exception as e:
        return f"[Error reading file: {str(e)}]"

# ────────────────────────────────────────────────
# Parse LLM response
# ────────────────────────────────────────────────
def parse_llm_response(text: str):
    text = text.strip()
    # Remove common markdown fences
    if text.startswith("```json"):
        text = text.split("```json", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Simple fallback — try to find { ... }
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except:
            raise e

# ────────────────────────────────────────────────
# Process single file content
# ────────────────────────────────────────────────
def process_file_content(file_bytes: bytes, file_name: str):
    file_hash = get_file_hash(file_bytes)
    if file_hash in st.session_state.processed_hashes:
        return True, f"Skipped (identical content): {file_name}"

    text = extract_text(file_bytes, file_name)
    prompt = f"{SYSTEM_PROMPT}\n\nFile: {file_name}\n\nContent:\n{text}"

    try:
        response = llm.invoke(prompt)
        result_str = response.content.strip()
        result = parse_llm_response(result_str)

        if "records" in result and isinstance(result["records"], list) and result["records"]:
            records = result["records"]
            overall_conf = result.get("overall_confidence", 0.0)
            overall_status = result.get("status", "partial")
        else:
            # Fallback for single record
            records = [{"extracted_fields": result}]
            overall_conf = result.get("confidence", 0.0)
            overall_status = result.get("status", "unknown")

        for idx, rec in enumerate(records):
            data = rec.get("extracted_fields", {})
            if "currency" in data:
                data["currency"] = normalize_currency(data["currency"])
            for key in ["total_amount", "unit_price", "line_total", "hours_worked", "rate_per_hour", "quantity"]:
                if key in data:
                    data[key] = clean_number(data[key])

            st.session_state.processed.append({
                "file": file_name,
                "file_hash": file_hash,
                "record_index": idx,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": rec.get("status", overall_status),
                "confidence": rec.get("confidence", overall_conf),
                "document_type": rec.get("document_type", result.get("document_type", "unknown")),
                "data": data,
                "issues": rec.get("validation_issues", []),
                "raw": result
            })

        st.session_state.processed_files.add(file_name)
        st.session_state.processed_hashes.add(file_hash)
        save_history()
        return True, f"Processed: {file_name} ({len(records)} record(s))"

    except json.JSONDecodeError:
        return False, f"Invalid JSON for {file_name}"
    except Exception as e:
        return False, f"Error: {str(e)}"

# ────────────────────────────────────────────────
# UI - Top tabs
# ────────────────────────────────────────────────
tab_upload, tab_results = st.tabs(["Upload & Process", "View Results"])

with tab_upload:
    st.title("Upload & Process")
    st.markdown("Upload invoices, timesheets, receipts or any documents → get structured data ready for Excel/ERP")

    st.markdown("""
    **How to upload many files at once:**
    - Click **Browse files** → go to your folder → press **Ctrl+A** (select all) → Open
    - Or drag & drop files directly from your file explorer (hold Ctrl to select many)
    """)

    if st.session_state.processed:
        col_btn = st.columns([1, 3, 1])[1]
        with col_btn:
            if st.button("🔍 View Results Now", type="primary", use_container_width=True):
                st.session_state.current_tab = "View Results"  # Note: This is unused, but kept for potential future use
                st.rerun()

    uploaded_files = st.file_uploader(
        "Upload files (PDF or TXT)",
        accept_multiple_files=True,
        type=["pdf", "txt"],
        key=f"uploader_{st.session_state.uploader_key}"
    )

    if uploaded_files:
        progress_bar = st.progress(0)
        status_text = st.empty()

        total = len(uploaded_files)
        processed_count = 0
        skipped_count = 0

        for i, file in enumerate(uploaded_files):
            file_name = file.name

            file_bytes = file.read()
            file_hash = get_file_hash(file_bytes)

            if file_hash in st.session_state.processed_hashes:
                skipped_count += 1
                status_text.text(f"Skipped (identical content): {file_name}")
            else:
                with st.spinner(f"Processing {file_name}..."):
                    success, msg = process_file_content(file_bytes, file_name)
                    status_text.text(msg)
                    if success:
                        st.success(msg)
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

with tab_results:
    st.title("Processed Results")

    if st.session_state.processed:
        st.subheader(f"Processed Documents ({len(st.session_state.processed)})")

        summary_data = []
        for item in st.session_state.processed:
            summary_data.append({
                "File": item["file"],
                "Record #": item["record_index"] + 1,
                "Time": item["timestamp"],
                "Status": item["status"].upper(),
                "Confidence": f"{item['confidence']:.2f}",
                "Type": item["document_type"],
                "Vendor / Employee": item["data"].get("vendor_name") or item["data"].get("employee_name", "—"),
                "Total": item["data"].get("total_amount", "—"),
                "Currency": item["data"].get("currency", "—"),
                "Issues": len(item["issues"])
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

        if st.button("Clear All Processed Data"):
            st.session_state.processed = []
            st.session_state.processed_files = set()
            st.session_state.processed_hashes = set()
            st.session_state.uploader_key += 1
            if os.path.exists(HISTORY_FILE):
                os.remove(HISTORY_FILE)
            st.success("History cleared! Uploader and saved file reset.")
            st.rerun()

        st.subheader("Download Results")

        col1, col2, col3 = st.columns(3)

        with col1:
            csv_summary = df_summary.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Summary CSV",
                csv_summary,
                f"databot_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv"
            )

        with col2:
            full_json = json.dumps([item["raw"] for item in st.session_state.processed], indent=2)
            st.download_button(
                "Download Full JSON",
                full_json,
                f"databot_full_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                "application/json"
            )

        with col3:
            excel_buffer = BytesIO()
            try:
                df_summary.to_excel(excel_buffer, index=False, engine='openpyxl')
                excel_buffer.seek(0)
                excel_data = excel_buffer.getvalue()
            except Exception as e:
                excel_data = None
                st.warning(f"Excel generation failed: {e}")

            if excel_data:
                st.download_button(
                    label="Download Excel (.xlsx)",
                    data=excel_data,
                    file_name=f"databot_results_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.button("Download Excel (.xlsx)", disabled=True)

        st.subheader("Detailed Results")
        for item in st.session_state.processed:
            with st.expander(f"Record {item['record_index'] + 1} – {item['status'].upper()} (Conf: {item['confidence']:.2f})"):
                col1, col2 = st.columns([1,2])

                with col1:
                    st.markdown("**Extracted Fields**")
                    data = item["data"]
                    for k, v in data.items():
                        if v is not None and v != "":
                            st.markdown(f"**{k.replace('_',' ').title()}**: {v}")

                with col2:
                    st.markdown("**Raw LLM Output**")
                    st.json(item["raw"])

                if item["issues"]:
                    st.warning("Validation Issues:")
                    for issue in item["issues"]:
                        if isinstance(issue, dict):
                            field = issue.get('field', 'unknown')
                            severity = issue.get('severity', 'info')
                            message = issue.get('message', '(no message)')
                            st.write(f"- **{field}** ({severity}): {message}")
                        else:
                            st.write(f"- {issue}")

                if st.button("Remove this entry", key=f"del_{item['file']}_{item['record_index']}"):
                    st.session_state.processed = [
                        x for x in st.session_state.processed
                        if not (x["file"] == item["file"] and x["record_index"] == item["record_index"])
                    ]
                    st.session_state.processed_files.discard(item["file"])
                    st.session_state.processed_hashes.discard(item.get("file_hash", ""))
                    save_history()
                    st.rerun()

    else:
        st.info("Upload files to start extracting data.")