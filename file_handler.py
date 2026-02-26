# file_handler.py - File reading and text extraction
import hashlib
from pathlib import Path
from io import BytesIO
from pypdf import PdfReader

def extract_text(file_bytes: bytes, file_name: str) -> str:
    """
    Extract text from file based on file type.
    Supports: PDF, TXT, EML
    """
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

def get_file_extension(file_name: str) -> str:
    """Get file extension."""
    return Path(file_name).suffix.lower()

def is_supported_file(file_name: str) -> bool:
    """Check if file type is supported."""
    ext = get_file_extension(file_name)
    return ext in [".pdf", ".txt", ".eml"]

def get_file_size(file_bytes: bytes) -> int:
    """Get file size in bytes."""
    return len(file_bytes)

def get_file_size_mb(file_bytes: bytes) -> float:
    """Get file size in MB."""
    return round(get_file_size(file_bytes) / (1024 * 1024), 2)

def get_file_hash(file_bytes: bytes) -> str:
    """Calculate SHA256 hash of file content."""
    return hashlib.sha256(file_bytes).hexdigest()
