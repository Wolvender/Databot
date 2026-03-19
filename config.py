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
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

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
"""

LOGO_SVG = """
<svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="50" cy="50" r="45" stroke="white" stroke-width="6" stroke-dasharray="10 10"/>
    <path d="M30 50 L45 65 L70 35" stroke="white" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

# ────────────────────────────────────────────────
# Page Config
# ────────────────────────────────────────────────
PAGE_TITLE = "DataBot – Intelligent Data Entry"
PAGE_ICON = "📊"
PAGE_LAYOUT = "wide"
APP_NAME = "Databot"  # Change this to customize the header name
