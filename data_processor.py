# data_processor.py - LLM and data processing logic
import json
import streamlit as st
from datetime import datetime
from langchain_groq import ChatGroq
from config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE, SYSTEM_PROMPT, HISTORY_FILE
from file_handler import get_file_hash, extract_text
from pydantic import BaseModel, Field
from typing import List, Optional

from validators import DataValidator

class ExtractedField(BaseModel):
    date: str = Field(description="YYYY-MM-DD or best guess", default="N/A")
    entity: str = Field(description="The person, company, or subject", default="N/A")
    reference: str = Field(description="Invoice #, PO #, Case ID", default="N/A")
    amount: float = Field(description="The numeric value. Pure number ONLY", default=0.0)
    tax_amount: float = Field(description="VAT/Tax amount if explicitly stated", default=0.0)
    currency: str = Field(description="3-letter ISO code: EUR, USD, etc.", default="N/A")
    vat_number: str = Field(description="VAT/Tax ID of the entity if found", default="N/A")
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
        """Remove currency symbols and convert to number, handling both . and , as decimals."""
        if value is None or value == "" or value == "N/A":
            return 0.0
        
        value = str(value).strip()
        # Remove common currency symbols and filler
        for token in ["EUR", "EURO", "EUROS", "€", "USD", "$", "GBP", "£", "eur", "usd", "gbp"]:
            value = value.replace(token, "").strip()
        
        if not value:
            return 0.0

        try:
            # Handle European format: "1.234,56" -> "1234.56"
            if "," in value and "." in value:
                if value.find(".") < value.find(","): # Dot is thousands separator
                    value = value.replace(".", "").replace(",", ".")
                else: # Comma is thousands separator
                    value = value.replace(",", "")
            elif "," in value: # Only comma - could be decimal or thousands
                # If only one comma and it's near the end, assume decimal
                if value.count(",") == 1 and len(value.split(",")[1]) <= 2:
                    value = value.replace(",", ".")
                else:
                    value = value.replace(",", "")
            
            return float(value)
        except ValueError:
            return value
    
    @staticmethod
    def normalize_currency(currency: str) -> str:
        """Normalize currency codes to ISO 3-letter codes without losing data."""
        if not currency or currency == "N/A":
            return "N/A"
        
        original = str(currency).strip()
        currency = original.upper().replace(" ", "")
        
        mapping = {
            "EURO": "EUR", "EUROS": "EUR", "€": "EUR",
            "DOLLAR": "USD", "DOLLARS": "USD", "$": "USD",
            "POUND": "GBP", "POUNDS": "GBP", "£": "GBP",
        }
        
        if currency in mapping:
            return mapping[currency]
            
        # If it's already a 3-letter alpha code (like CHF, AUD, SEK), keep it!
        if len(currency) == 3 and currency.isalpha():
            return currency
            
        return original # Keep original if we're not sure, don't just say "UNKNOWN"
    
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
            
            # Initial extraction results
            if "records" in result and isinstance(result["records"], list) and result["records"]:
                records = result["records"]
                overall_conf = result.get("overall_confidence", 0.0)
                overall_status = result.get("status", "partial")
            else:
                records = [{"extracted_fields": {}}]
                overall_conf = result.get("overall_confidence", 0.0)
                overall_status = result.get("status", "unknown")
            
            # Smart Self-Correction Loop
            needs_correction = False
            correction_feedback = []
            
            for idx, rec in enumerate(records):
                data = rec.get("extracted_fields", {})
                issues = DataValidator.validate_record(data)
                rec["validation_issues"] = issues
                
                # If we have errors, we trigger a correction pass
                if any(i["severity"] == "error" for i in issues):
                    needs_correction = True
                    error_msgs = [f"Field '{i['field']}': {i['message']}" for i in issues if i["severity"] == "error"]
                    correction_feedback.append(f"Record {idx+1} issues: {', '.join(error_msgs)}")

            if needs_correction:
                # Second pass: Self-Correction
                correction_prompt = f"""
                {SYSTEM_PROMPT}
                
                I previously extracted data from the file below, but there were validation errors.
                Please re-examine the source text and provide CORRECTED structured data.
                
                SOURCE TEXT:
                {text[:4000]}
                
                ERRORS FOUND IN PREVIOUS EXTRACTION:
                {chr(10).join(correction_feedback)}
                
                Return the full corrected LedgerResponse.
                """
                try:
                    corrected_obj = structured_llm.invoke(correction_prompt)
                    result = corrected_obj.model_dump()
                    records = result.get("records", records)
                    overall_conf = result.get("overall_confidence", overall_conf)
                except Exception as correction_err:
                    from logger import logger
                    logger.warning(f"Self-correction failed for {file_name}: {correction_err}")

            # Process and store each record (Final version)
            for idx, rec in enumerate(records):
                data = rec.get("extracted_fields", {})
                
                # Normalize fields
                if "currency" in data:
                    data["currency"] = self.normalize_currency(data["currency"])
                
                # Run validation one last time for the final report
                final_issues = DataValidator.validate_record(data)
                quality_score = DataValidator.calculate_quality_score(data, final_issues)
                
                # Dynamic normalization for any numeric fields
                common_numeric = ["amount", "tax_amount", "total", "price", "hours"]
                for key in data.keys():
                    if any(term in key.lower() for term in common_numeric):
                        data[key] = self.clean_number(data[key])
                
                # Store processed record
                st.session_state.processed.append({
                    "file": file_name,
                    "file_hash": file_hash,
                    "record_index": idx,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "verified" if not any(i["severity"] == "error" for i in final_issues) else "needs_review",
                    "confidence": max(rec.get("confidence", overall_conf), quality_score),
                    "document_type": rec.get("document_type", result.get("document_type", "unknown")),
                    "data": data,
                    "issues": final_issues,
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
