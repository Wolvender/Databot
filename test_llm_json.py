
import os
import json
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
model = "llama-3.3-70b-versatile"

llm = ChatGroq(
    model=model,
    temperature=0.1,
    groq_api_key=GROQ_API_KEY
)

SYSTEM_PROMPT = """
You are DataBot – a high-intelligence enterprise data discovery and extraction assistant.

Your primary goal is to find STRUCTURE in UNSTRUCTURED data. 
If the user provides a "messy" file, your job is to:
1. Identify all logical "entities" or "records" hidden in the text.
2. Segment them into a list of records.
3. Infer the purpose of each record (e.g., invoice, note, contact, task, event).

Rules:
- Output ONLY valid JSON. No conversational filler or markdown explanations outside the JSON.
- If the input is a single document (like one invoice), return one record.
- If the input is "random info", find all valuable pieces of data and return them as separate records.
- For EVERY record, you MUST provide a "record_type" (e.g. "invoice", "contact_info", "meeting_note", "expense_claim").
- Use snake_case keys.
- Infer meaningful field names based on the context.
- validation_issues MUST be an array of objects: {"field": "...", "severity": "error|warning|info", "message": "..."}

Return exactly this structure:

{
  "status": "complete" | "partial" | "needs_review" | "invalid",
  "document_type": "composite" | "invoice" | "timesheet" | "receipt" | "unknown",
  "records": [
    {
      "extracted_fields": { ... },
      "record_type": "e.g. invoice, project_note, employee_update",
      "validation_issues": [ ... ],
      "confidence": 0.0–1.0
    }
  ],
  "overall_confidence": 0.0–1.0,
  "summary": "Overall summary of what was found in the random info"
}

If the data is extremely messy, do your best to summarize the main points into a "general_note" record type.
"""

messy_text = """
Hey, this is John from ACME. Just wanted to let you know that the meeting is at 2 PM tomorrow.
Also, I found an old receipt for that lunch we had. It was 45.50 Euro at 'The Burger Joint' on 2024-05-12.
Oh, and here is a new lead: Sarah Smith, email: sarah@example.com, phone: +1-555-0199.
Wait, I also have an invoice here. Invoice #INV-2024-001 from CloudCorp for $1200.50 due next Friday.
"""

prompt = f"{SYSTEM_PROMPT}\n\nContent:\n{messy_text}"

print(f"Calling LLM ({model})...")
try:
    response = llm.invoke(prompt)
    print("--- RAW RESPONSE ---")
    print(response.content)
    print("--- END RAW RESPONSE ---")
    
    # Simple JSON check
    content = response.content.strip()
    if content.startswith("```json"):
        content = content.split("```json")[1].split("```")[0].strip()
    
    data = json.loads(content)
    print("\n✅ Successfully parsed as JSON!")
    print(f"Found {len(data.get('records', []))} records.")
except Exception as e:
    print(f"\n❌ FAILED: {str(e)}")
