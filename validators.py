# validators.py - Data validation and quality checks
"""
Comprehensive validation for extracted data
Ensures data quality before export to ERP/Excel
"""

import re
from datetime import datetime
from typing import Dict, List, Tuple, Any

class DataValidator:
    """Validates extracted data against business rules."""
    
    # Validation rules
    CURRENCY_CODES = ["EUR", "USD", "GBP", "CHF", "JPY", "CNY", "AUD", "CAD"]
    EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE_REGEX = r'^\+?[\d\s\-\(\)]{7,20}$'
    DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d.%m.%Y"]
    
    @staticmethod
    def validate_currency(currency: str) -> Tuple[bool, str]:
        """Validate currency code."""
        if not currency:
            return False, "Currency is required"
        
        currency = currency.upper().strip()
        if currency not in DataValidator.CURRENCY_CODES:
            return False, f"Invalid currency code: {currency}"
        
        return True, ""
    
    @staticmethod
    def validate_amount(amount: Any, field_name: str = "amount") -> Tuple[bool, str]:
        """Validate monetary amount."""
        if amount is None or amount == "":
            return False, f"{field_name} is required"
        
        try:
            amount_float = float(amount)
            if amount_float < 0:
                return False, f"{field_name} cannot be negative"
            if amount_float > 1_000_000_000:  # 1 billion limit
                return False, f"{field_name} exceeds maximum allowed value"
            return True, ""
        except (ValueError, TypeError):
            return False, f"{field_name} must be a valid number"
    
    @staticmethod
    def validate_date(date_str: str, field_name: str = "date") -> Tuple[bool, str]:
        """Validate date format."""
        if not date_str:
            return False, f"{field_name} is required"
        
        for fmt in DataValidator.DATE_FORMATS:
            try:
                parsed_date = datetime.strptime(str(date_str), fmt)
                # Check if date is reasonable (not in future, not too old)
                if parsed_date > datetime.now():
                    return False, f"{field_name} cannot be in the future"
                if parsed_date.year < 1900:
                    return False, f"{field_name} is too old"
                return True, ""
            except ValueError:
                continue
        
        return False, f"{field_name} has invalid format"
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email address."""
        if not email:
            return True, ""  # Email is optional
        
        if not re.match(DataValidator.EMAIL_REGEX, email):
            return False, "Invalid email format"
        
        return True, ""
    
    @staticmethod
    def validate_vat_number(vat: str, country: str = "EU") -> Tuple[bool, str]:
        """Validate VAT number format."""
        if not vat:
            return True, ""  # VAT is optional
        
        vat = vat.upper().replace(" ", "").replace("-", "")
        
        # EU VAT format: 2 letters + 8-12 digits
        if country == "EU":
            if not re.match(r'^[A-Z]{2}\d{8,12}$', vat):
                return False, "Invalid EU VAT format (expected: XX12345678)"
        
        return True, ""
    
    @staticmethod
    def validate_invoice_number(invoice_num: str) -> Tuple[bool, str]:
        """Validate invoice number."""
        if not invoice_num:
            return False, "Invoice number is required"
        
        invoice_num = str(invoice_num).strip()
        if len(invoice_num) < 3:
            return False, "Invoice number too short"
        
        return True, ""
    
    @staticmethod
    def validate_record(data: Dict, document_type: str = "general") -> List[Dict]:
        """
        Validate entire record based on document type.
        Supports both specific (invoice_date) and generic (date) field names.
        
        Returns:
            List of validation issues
        """
        issues = []
        
        # Mapping generic fields to validation logic
        field_mapping = {
            "currency": DataValidator.validate_currency,
            "amount": lambda v: DataValidator.validate_amount(v, "amount"),
            "total_amount": lambda v: DataValidator.validate_amount(v, "total_amount"),
            "date": lambda v: DataValidator.validate_date(v, "date"),
            "invoice_date": lambda v: DataValidator.validate_date(v, "invoice_date"),
            "due_date": lambda v: DataValidator.validate_date(v, "due_date"),
            "reference": lambda v: DataValidator.validate_invoice_number(v) if v and v != "N/A" else (True, ""),
            "invoice_number": DataValidator.validate_invoice_number,
        }
        
        for field, validator in field_mapping.items():
            if field in data and data[field] not in [None, "", "N/A"]:
                valid, msg = validator(data[field])
                if not valid:
                    issues.append({
                        "field": field,
                        "severity": "error" if "required" in msg.lower() or "invalid" in msg.lower() else "warning",
                        "message": msg
                    })
        
        # Document-specific cross-field validations
        if "date" in data and "due_date" in data:
            try:
                d1 = str(data["date"])
                d2 = str(data["due_date"])
                # Basic YYYY-MM-DD check
                if re.match(r'^\d{4}-\d{2}-\d{2}$', d1) and re.match(r'^\d{4}-\d{2}-\d{2}$', d2):
                    if d2 < d1:
                        issues.append({
                            "field": "due_date",
                            "severity": "warning",
                            "message": "Due date is before the document date"
                        })
            except:
                pass
        
        # Email and VAT (if present)
        for field in ["email", "vat_number"]:
            if field in data and data[field] not in [None, "", "N/A"]:
                valid, msg = getattr(DataValidator, f"validate_{field}")(data[field])
                if not valid:
                    issues.append({
                        "field": field,
                        "severity": "warning",
                        "message": msg
                    })
        
        return issues
    
    @staticmethod
    def calculate_quality_score(data: Dict, issues: List[Dict]) -> float:
        """
        Calculate data quality score (0.0 - 1.0).
        
        Based on:
        - Number of fields extracted
        - Number of validation errors
        - Severity of issues
        """
        if not data:
            return 0.0
        
        # Base score from field completeness
        expected_fields = 10  # Adjust based on document type
        actual_fields = len([v for v in data.values() if v is not None and v != ""])
        completeness_score = min(1.0, actual_fields / expected_fields)
        
        # Penalty for validation issues
        error_penalty = sum(0.2 for issue in issues if issue.get("severity") == "error")
        warning_penalty = sum(0.05 for issue in issues if issue.get("severity") == "warning")
        
        quality_score = max(0.0, completeness_score - error_penalty - warning_penalty)
        
        return round(quality_score, 2)
