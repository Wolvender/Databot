# router.py - LLM-based document type classification
from langchain_groq import ChatGroq
from config import GROQ_API_KEY, LLM_MODEL
from processor_registry import ProcessorRegistry

class Router:
    """Classifies raw document text into one of the registered processor types."""

    def __init__(self):
        self.llm = ChatGroq(model=LLM_MODEL, groq_api_key=GROQ_API_KEY, temperature=0)
        self.types = ProcessorRegistry.list_types()

    def identify_type(self, text: str) -> str:
        prompt = f"""You are a document classifier. Analyze the text and categorize it into one of the following types: {', '.join(self.types)}.

        Guidelines:
        - Invoices, bills, receipts, payment confirmations or amounts owed -> 'invoice'.
        - Timesheets, hours worked, employee hour registration or payroll periods -> 'timesheet'.
        - Inventory counts, warehouse stock, units on hand or count sheets -> 'inventory'.
        - Return ONLY the name of the type.

        Text: {text[:1000]}"""
        response = self.llm.invoke(prompt)
        # Strip quotes/punctuation the LLM sometimes wraps around the label
        return response.content.strip().lower().strip(".\"'` ")
