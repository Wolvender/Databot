import json
from processor_registry import ProcessorRegistry
from langchain_groq import ChatGroq
from config import GROQ_API_KEY, LLM_MODEL

class Router:
    def __init__(self):
        self.llm = ChatGroq(model=LLM_MODEL, groq_api_key=GROQ_API_KEY, temperature=0)
        self.types = ProcessorRegistry.list_types()

    def identify_type(self, text: str) -> str:
        prompt = f"""You are a document classifier. Analyze the text and categorize it into one of the following types: {', '.join(self.types)}.

        Guidelines:
        - If the text mentions "Invoice", "Bill", "Payment", "Amount", "Currency", or "Hours", categorize it as 'invoice'.
        - If the text mentions "Inventory", "Warehouse", "Units", "Items", or "Stock", categorize it as 'inventory'.
        - Return ONLY the name of the type.

        Text: {text[:1000]}"""
        response = self.llm.invoke(prompt)
        return response.content.strip().lower()

# --- Test Script ---
if __name__ == "__main__":
    router = Router()
    
    test_inputs = [
        ("Invoice #123 from Apple, $500 total, date 2023-10-01", "ledger"),
        ("Storage box A contains 50 hammers", "inventory")
    ]
    
    for text, expected in test_inputs:
        result = router.identify_type(text)
        print(f"Text: {text[:30]}... -> Predicted: {result} (Expected: {expected})")
        assert result == expected
    
    print("Routing test passed!")
