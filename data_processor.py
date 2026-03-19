# data_processor.py - LLM and data processing logic
import json
import streamlit as st
from datetime import datetime
from langchain_groq import ChatGroq
from config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE, SYSTEM_PROMPT, HISTORY_FILE
from file_handler import get_file_hash, extract_text
from pydantic import BaseModel, Field
from typing import List, Optional

class ExtractedField(BaseModel):
    date: str = Field(description="YYYY-MM-DD or best guess", default="N/A")
    entity: str = Field(description="The person, company, or subject", default="N/A")
    reference: str = Field(description="Invoice #, PO #, Case ID", default="N/A")
    amount: float = Field(description="The numeric value. Pure number ONLY", default=0.0)
    currency: str = Field(description="3-letter ISO code: EUR, USD, etc.", default="N/A")
    description: str = Field(description="A concise summary", default="N/A")

class LedgerRecord(BaseModel):
    extracted_fields: ExtractedField
    confidence: float = Field(description="Confidence score 0.0-1.0", default=0.0)
    validation_issues: List[dict] = Field(description="List of issues", default_factory=list)
    status: str = Field(description="'complete' or 'partial'", default="partial")
    document_type: str = Field(description="Document type", default="unknown")

class LedgerResponse(BaseModel):
    status: str
    document_type: str
    records: List[LedgerRecord]
    summary: str
    overall_confidence: float = 0.0


class DataProcessor:
    """Handles LLM-based data extraction and processing."""
    
    def __init__(self):
        """Initialize the LLM and history."""
        self.llm = ChatGroq(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            groq_api_key=GROQ_API_KEY
        )
        self.load_history()
    
    def get_history_file(self):
        """Get user-specific history file path to prevent multi-tenant data leaks."""
        from auth import get_current_username
        import os
        username = get_current_username()
        if not username or username == "Unknown" or username == "":
            return HISTORY_FILE
            
        directory = os.path.dirname(HISTORY_FILE) or "."
        base = os.path.basename(HISTORY_FILE)
        name, ext = os.path.splitext(base)
        user_file = f"{name}_{username}{ext}"
        return os.path.join(directory, user_file)

    def load_history(self):
        """Load processing history from file."""
        if "processed" not in st.session_state:
            st.session_state.processed = []
        if "processed_files" not in st.session_state:
            st.session_state.processed_files = set()
        if "processed_hashes" not in st.session_state:
            st.session_state.processed_hashes = set()
        if "uploader_key" not in st.session_state:
            st.session_state.uploader_key = 0
        
        import os
        history_file = self.get_history_file()
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    st.session_state.processed = loaded
                    st.session_state.processed_files = {item["file"] for item in loaded}
                    st.session_state.processed_hashes = {item.get("file_hash", "") for item in loaded}
            except Exception as e:
                st.warning(f"Could not load history: {e}. Starting fresh.")
    
    def save_history(self):
        """Save processing history to file."""
        history_file = self.get_history_file()
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(st.session_state.processed, f, indent=2, ensure_ascii=False)
        except Exception as e:
            st.warning(f"Could not save history: {e}")
    
    @staticmethod
    def clean_number(value):
        """Remove currency symbols and convert to number."""
        if not value:
            return value
        
        value = str(value).strip()
        for token in ["EUR", "EURO", "EUROS", "€", "USD", "$", "GBP", "£", "EUREUR", "euro", "eur"]:
            value = value.replace(token, "").strip()
        
        try:
            return float(value)
        except ValueError:
            return value
    
    @staticmethod
    def normalize_currency(currency: str) -> str:
        """Normalize currency codes to ISO 3-letter codes."""
        if not currency:
            return "UNKNOWN"
        
        currency = str(currency).upper().strip().replace(" ", "")
        mapping = {
            "EUR": "EUR", "EURO": "EUR", "EUROS": "EUR", "€": "EUR", "EUREUR": "EUR",
            "USD": "USD", "DOLLAR": "USD", "DOLLARS": "USD", "$": "USD",
            "GBP": "GBP", "POUND": "GBP", "POUNDS": "GBP", "£": "GBP",
        }
        return mapping.get(currency, "UNKNOWN")
    
    def process_content(self, file_bytes: bytes, file_name: str) -> tuple[bool, str]:
        """
        Process file content with LLM and store results.
        Returns: (success: bool, message: str)
        """
        file_hash = get_file_hash(file_bytes)
        
        # Check if file already processed
        if file_hash in st.session_state.processed_hashes:
            return True, f"Skipped (identical content): {file_name}"
        
        # Extract text from file
        text = extract_text(file_bytes, file_name)
        prompt = f"{SYSTEM_PROMPT}\n\nFile: {file_name}\n\nContent:\n{text}"
        
        try:
            # Call LLM with native structured output
            structured_llm = self.llm.with_structured_output(LedgerResponse)
            result_obj = structured_llm.invoke(prompt)
            result = result_obj.model_dump()
            
            # Handle records
            if "records" in result and isinstance(result["records"], list) and result["records"]:
                records = result["records"]
                overall_conf = result.get("overall_confidence", 0.0)
                overall_status = result.get("status", "partial")
            else:
                # Fallback for empty records list
                records = [{"extracted_fields": {}}]
                overall_conf = result.get("overall_confidence", 0.0)
                overall_status = result.get("status", "unknown")
            
            # Process and store each record
            for idx, rec in enumerate(records):
                data = rec.get("extracted_fields", {})
                
                # Normalize fields
                if "currency" in data:
                    data["currency"] = self.normalize_currency(data["currency"])
                
                # Dynamic normalization for any numeric fields we recognize
                common_numeric = ["total_amount", "amount", "price", "unit_price", "line_total", "hours_worked", "rate_per_hour", "quantity", "total"]
                for key in data.keys():
                    if any(term in key.lower() for term in common_numeric):
                        data[key] = self.clean_number(data[key])
                
                # Store processed record
                st.session_state.processed.append({
                    "file": file_name,
                    "file_hash": file_hash,
                    "record_index": idx,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": rec.get("status", overall_status),
                    "confidence": rec.get("confidence", overall_conf),
                    "document_type": rec.get("record_type", rec.get("document_type", result.get("document_type", "unknown"))),
                    "data": data,
                    "issues": rec.get("validation_issues", []),
                    "raw": result
                })
            
            st.session_state.processed_files.add(file_name)
            st.session_state.processed_hashes.add(file_hash)
            self.save_history()
            
            return True, f"Processed: {file_name} ({len(records)} record(s))"
            
        except Exception as e:
            from logger import logger
            logger.error(f"Unexpected error processing {file_name}", error=e)
            return False, f"Error: {str(e)}"
    
    def clear_history(self):
        """Clear all processed data."""
        import os
        st.session_state.processed = []
        st.session_state.processed_files = set()
        st.session_state.processed_hashes = set()
        st.session_state.uploader_key += 1
        
        history_file = self.get_history_file()
        if os.path.exists(history_file):
            os.remove(history_file)
        
        self.save_history()

    def remove_entry(self, file_name: str, record_index: int):
        """Remove a specific processed record."""
        st.session_state.processed = [
            x for x in st.session_state.processed
            if not (x["file"] == file_name and x["record_index"] == record_index)
        ]
        st.session_state.processed_files.discard(file_name)
        st.session_state.processed_hashes.discard(file_name)
        self.save_history()
