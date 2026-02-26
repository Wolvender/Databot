# data_processor.py - LLM and data processing logic
import json
import streamlit as st
from datetime import datetime
from langchain_groq import ChatGroq
from config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE, SYSTEM_PROMPT, HISTORY_FILE
from file_handler import get_file_hash, extract_text

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
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    st.session_state.processed = loaded
                    st.session_state.processed_files = {item["file"] for item in loaded}
                    st.session_state.processed_hashes = {item.get("file_hash", "") for item in loaded}
            except Exception as e:
                st.warning(f"Could not load history: {e}. Starting fresh.")
    
    def save_history(self):
        """Save processing history to file."""
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
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
    
    def parse_llm_response(self, text: str) -> dict:
        """Parse LLM response, handling markdown fences and extraneous text."""
        text = text.strip()
        
        # Remove markdown fences as a first pass
        if "```json" in text:
            # Multi-block check: take the first or largest block if multiple exist
            blocks = text.split("```json")
            if len(blocks) > 1:
                text = blocks[1].split("```")[0]
        elif "```" in text:
            blocks = text.split("```")
            if len(blocks) > 1:
                text = blocks[1]
        
        text = text.strip()
        
        # Try direct JSON load
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # More aggressive regex-style search for JSON boundaries
            try:
                # Find the first '{' and the last '}'
                start = text.find("{")
                end = text.rfind("}")
                if start != -1 and end != -1 and end > start:
                    candidate = text[start:end + 1]
                    return json.loads(candidate)
            except:
                pass
            
            # Final fallback: if it's very messy, maybe it didn't even output JSON
            # Log for debugging (in real app we might want to store this)
            raise json.JSONDecodeError("Could not extract valid JSON from LLM response. The data might be too complex or the model outputted conversational text.", text, 0)
    
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
            # Call LLM
            response = self.llm.invoke(prompt)
            result_str = response.content.strip()
            result = self.parse_llm_response(result_str)
            
            # Handle records
            if "records" in result and isinstance(result["records"], list) and result["records"]:
                records = result["records"]
                overall_conf = result.get("overall_confidence", 0.0)
                overall_status = result.get("status", "partial")
            else:
                # Fallback for single record
                records = [{"extracted_fields": result}]
                overall_conf = result.get("confidence", 0.0)
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
        
        except json.JSONDecodeError as e:
            from logger import logger
            # Log the full failed response for debugging
            logger.error(f"JSON Parsing failed for {file_name}", error=e, raw_response=result_str[:2000])
            
            # Fallback: Create a 'Raw Extraction' record so the user gets something
            st.session_state.processed.append({
                "file": file_name,
                "file_hash": file_hash,
                "record_index": 0,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "needs_review",
                "confidence": 0.3,
                "document_type": "raw_extraction",
                "data": {"raw_text_found": result_str},
                "issues": [{"field": "json_parsing", "severity": "error", "message": "The AI response was not in the expected format. Showing raw output instead."}],
                "raw": {"full_response": result_str}
            })
            st.session_state.processed_files.add(file_name)
            st.session_state.processed_hashes.add(file_hash)
            self.save_history()
            return True, f"Recovered raw info from: {file_name} (JSON parsing failed)"
            
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
        
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        
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
