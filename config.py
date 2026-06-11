# config.py - Configuration settings and constants
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ────────────────────────────────────────────────
# File & Storage
# ────────────────────────────────────────────────
HISTORY_FILE = "history.json"
INCOMING_DIR = "incoming"
ERRORS_DIR = os.path.join(INCOMING_DIR, "errors")
PROCESSED_DIR = os.path.join(INCOMING_DIR, "processed")

# Create directories if they don't exist
def _ensure_directories():
    for dir_path in [ERRORS_DIR, PROCESSED_DIR]:
        path = Path(dir_path)
        if path.exists() and path.is_file():
            os.remove(path)
        path.mkdir(parents=True, exist_ok=True)

_ensure_directories()

import streamlit as st

# ────────────────────────────────────────────────
# API & LLM Settings
# ────────────────────────────────────────────────
# Try to get from environment first, then Streamlit Secrets for cloud hosting
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    try:
        GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
    except Exception:
        # No secrets.toml present — st.secrets raises instead of returning None
        GROQ_API_KEY = None

if not GROQ_API_KEY:
    raise RuntimeError("Missing GROQ_API_KEY. Please add it to .env or Streamlit Secrets and restart.")

LLM_MODEL = "llama-3.3-70b-versatile"
LLM_TEMPERATURE = 0.1

# ────────────────────────────────────────────────
# Credentials (Demo - Replace with secure storage)
# ────────────────────────────────────────────────
USERS = {
    "admin": "admin123",
    "user": "user456"
}

# ────────────────────────────────────────────────
# System Prompt for LLM
# ────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are DataBot – a professional Data Entry Clerk with 100% accuracy.

Your task is to take unstructured, messy, or "jumbled" text and extract it into a structured data entry ledger.

Rules for Extraction:
1. **Identify Entries**: Look for every distinct transaction, event, or record in the text.
2. **Fixed Schema**: Every record MUST be mapped to these specific keys where possible:
   - `date`: (YYYY-MM-DD or best guess)
   - `entity`: (The person, company, or subject of the record)
   - `reference`: (Invoice #, PO #, Case ID, or unique identifier)
   - `amount`: (The net or total numeric value. Pure number ONLY)
   - `tax_amount`: (VAT/Tax amount if explicitly stated)
   - `currency`: (3-letter ISO code: EUR, USD, etc.)
   - `vat_number`: (VAT/Tax ID of the entity if found)
   - `description`: (A concise summary of what this entry is about)
3. **Multi-Record Output**: If the file contains many "items" or "notes", extract each as its own object in the `records` list.
4. **Clean Input**: Strip out conversational filler. If a field is missing, set it to "N/A" rather than leaving it out.

Output Format (STRICT JSON ONLY):
{
  "status": "complete" | "partial",
  "document_type": "ledger_entry",
  "records": [
    {
      "extracted_fields": {
        "date": "...",
        "entity": "...",
        "reference": "...",
        "amount": 0.0,
        "tax_amount": 0.0,
        "currency": "...",
        "vat_number": "...",
        "description": "..."
      },
      "confidence": 0.0-1.0,
      "validation_issues": []
    }
  ],
  "summary": "Short clerical summary of the batch"
}
"""

# ────────────────────────────────────────────────
# CSS Styling
# ────────────────────────────────────────────────
STREAMLIT_THEME = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --bg: #0e1014;
        --surface: #161920;
        --surface-2: #1c2029;
        --border: #262b36;
        --border-strong: #343b49;
        --text: #e7e9ee;
        --muted: #8b93a4;
        --accent: #6366f1;
        --accent-hover: #7c7ff5;
        --success: #34d399;
        --warning: #fbbf24;
        --danger: #f87171;
        --radius: 8px;
    }

    html, body, .stApp, .stApp * {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    .stApp {
        background: var(--bg);
        color: var(--text);
    }

    header, .stApp > header {
        display: none !important;
    }

    .block-container {
        max-width: 1180px;
        padding-top: 1.25rem;
    }

    /* Typography — calmer scale than Streamlit defaults */
    h1 { font-size: 1.6rem !important; font-weight: 650 !important; letter-spacing: -0.01em; }
    h2 { font-size: 1.2rem !important; font-weight: 600 !important; }
    h3 { font-size: 1.05rem !important; font-weight: 600 !important; }

    /* Top bar */
    .app-topbar {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        padding: 0.3rem 0;
    }

    .app-topbar .logo-mark {
        width: 30px;
        height: 30px;
        border-radius: 8px;
        background: var(--accent);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }

    .app-topbar .wordmark {
        font-size: 1.15rem;
        font-weight: 650;
        letter-spacing: -0.01em;
        color: var(--text);
    }

    .app-topbar .subtitle {
        color: var(--muted);
        font-size: 0.88rem;
        margin-left: 0.4rem;
        padding-left: 0.9rem;
        border-left: 1px solid var(--border);
    }

    .app-divider {
        border-bottom: 1px solid var(--border);
        margin: 0.4rem 0 1.4rem 0;
    }

    /* Buttons — flat, one accent */
    .stButton > button,
    .stDownloadButton > button,
    [data-testid="stFormSubmitButton"] > button {
        background: var(--surface);
        color: var(--text);
        border: 1px solid var(--border-strong);
        border-radius: var(--radius);
        padding: 0.5rem 1.1rem;
        font-weight: 500;
        font-size: 0.95rem;
        box-shadow: none;
        transition: background 0.15s ease, border-color 0.15s ease;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        background: var(--surface-2);
        border-color: var(--accent);
        color: var(--text);
    }

    .stButton > button[kind="primary"],
    .stDownloadButton > button[kind="primary"],
    [data-testid="stFormSubmitButton"] > button[kind="primary"],
    [data-testid="baseButton-primary"] {
        background: var(--accent);
        border-color: var(--accent);
        color: #ffffff;
    }

    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button[kind="primary"]:hover,
    [data-testid="stFormSubmitButton"] > button[kind="primary"]:hover,
    [data-testid="baseButton-primary"]:hover {
        background: var(--accent-hover);
        border-color: var(--accent-hover);
        color: #ffffff;
    }

    .stButton > button:disabled {
        opacity: 0.45;
        border-color: var(--border);
    }

    /* Tabs — underline style */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.35rem;
        border-bottom: 1px solid var(--border);
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        padding: 0.55rem 0.9rem;
        color: var(--muted);
        font-size: 0.95rem;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        color: var(--text);
        background: transparent;
    }

    .stTabs [data-baseweb="tab-highlight"] {
        background-color: var(--accent);
    }

    .stTabs [data-baseweb="tab-border"] {
        background-color: transparent;
    }

    /* Inputs */
    .stTextInput [data-baseweb="input"] {
        background: var(--surface);
        border-color: var(--border-strong);
        border-radius: var(--radius);
    }

    .stTextInput [data-baseweb="input"]:focus-within {
        border-color: var(--accent);
    }

    .stTextInput input {
        color: var(--text);
    }

    /* Forms (login card) */
    [data-testid="stForm"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.8rem;
    }

    /* File uploader */
    [data-testid="stFileUploaderDropzone"] {
        background: var(--surface);
        border: 1px dashed var(--border-strong);
        border-radius: 10px;
    }

    /* Expander */
    [data-testid="stExpander"] {
        background: var(--surface);
        border: 1px solid var(--border) !important;
        border-radius: 10px;
    }

    /* Dataframe */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 10px;
    }

    /* Progress bar */
    .stProgress > div > div > div > div {
        background-color: var(--accent);
    }

    /* Result banner */
    .result-banner {
        background: var(--surface);
        border: 1px solid var(--border);
        border-left: 3px solid var(--success);
        border-radius: var(--radius);
        padding: 0.8rem 1rem;
        margin: 1rem 0;
        color: var(--text);
        font-size: 0.95rem;
    }

    /* Auth card heading */
    .auth-title {
        text-align: center;
        margin-bottom: 1.25rem;
        color: var(--text);
    }

    .auth-switch {
        text-align: center;
        margin-top: 1rem;
        color: var(--muted);
        font-size: 0.9rem;
    }

    /* Confidence helpers */
    .conf-high   { color: var(--success); font-weight: 600; }
    .conf-medium { color: var(--warning); font-weight: 600; }
    .conf-low    { color: var(--danger); font-weight: 600; }

    hr { border-color: var(--border); }
    </style>
"""

LOGO_SVG = """
<svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="1" y="1.5" width="12" height="2.4" rx="1.2" fill="white"/>
    <rect x="1" y="5.8" width="8.5" height="2.4" rx="1.2" fill="white" opacity="0.75"/>
    <rect x="1" y="10.1" width="11" height="2.4" rx="1.2" fill="white" opacity="0.5"/>
</svg>
"""

# ────────────────────────────────────────────────
# Page Config
# ────────────────────────────────────────────────
PAGE_TITLE = "DataBot – Intelligent Data Entry"
PAGE_ICON = "📊"
PAGE_LAYOUT = "wide"
APP_NAME = "DataBot"  # Change this to customize the header name
