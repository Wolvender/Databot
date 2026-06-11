from pydantic import BaseModel, Field
from typing import Dict, Type, List, Optional

# Define the interface for a Processor Plugin
class ProcessorPlugin:
    def __init__(self, name: str, schema: Type[BaseModel], system_prompt: str):
        self.name = name
        self.schema = schema
        self.system_prompt = system_prompt

# Registry to hold our plugins
class ProcessorRegistry:
    _registry: Dict[str, ProcessorPlugin] = {}

    @classmethod
    def register(cls, name: str, schema: Type[BaseModel], system_prompt: str):
        cls._registry[name] = ProcessorPlugin(name, schema, system_prompt)

    @classmethod
    def get(cls, name: str) -> Optional[ProcessorPlugin]:
        return cls._registry.get(name)

    @classmethod
    def list_types(cls) -> List[str]:
        return list(cls._registry.keys())

# --- Record Schemas ---
# Every document schema wraps a list of records: real business documents
# (count sheets, payment emails, timesheets) usually contain several entries.

class InvoiceRecord(BaseModel):
    date: str = Field(default="N/A", description="Invoice or transaction date in YYYY-MM-DD format")
    entity: str = Field(default="N/A", description="The party that issued the invoice or made the payment (the vendor/sender), not the bill-to recipient")
    reference: str = Field(default="N/A", description="Invoice number, PO number or payment reference")
    amount: float = Field(default=0.0, description="Total amount including tax, as a pure number")
    tax_amount: float = Field(default=0.0, description="VAT/BTW/tax amount if explicitly stated, as a pure number")
    currency: str = Field(default="N/A", description="3-letter ISO currency code, e.g. EUR, USD")
    due_date: str = Field(default="N/A", description="Payment due date in YYYY-MM-DD format, if stated")
    description: str = Field(default="N/A", description="Short description of what this invoice or payment is for")

class InvoiceDocument(BaseModel):
    records: List[InvoiceRecord] = Field(default_factory=list, description="One record per distinct invoice, payment or transaction found")
    confidence: float = Field(default=0.0, description="Overall extraction confidence between 0.0 and 1.0")

class InventoryRecord(BaseModel):
    item_name: str = Field(default="N/A", description="Name of the item")
    sku: str = Field(default="N/A", description="SKU, article number or product code, if present")
    quantity: int = Field(default=0, description="Counted number of units")
    location: str = Field(default="N/A", description="Storage location, bin or zone")

class InventoryDocument(BaseModel):
    records: List[InventoryRecord] = Field(default_factory=list, description="One record per counted item or stock line")
    confidence: float = Field(default=0.0, description="Overall extraction confidence between 0.0 and 1.0")

class TimesheetRecord(BaseModel):
    employee: str = Field(default="N/A", description="Employee or contractor name")
    period: str = Field(default="N/A", description="Week, date or date range the hours apply to")
    project: str = Field(default="N/A", description="Client, project or cost center")
    hours: float = Field(default=0.0, description="Total hours worked in the period, as a pure number")
    rate: str = Field(default="N/A", description="Hourly rate if stated, e.g. EUR 85/hour")

class TimesheetDocument(BaseModel):
    records: List[TimesheetRecord] = Field(default_factory=list, description="One record per employee per period")
    confidence: float = Field(default=0.0, description="Overall extraction confidence between 0.0 and 1.0")

# --- System Prompts ---

INVOICE_PROMPT = """You are a meticulous accounts-payable data entry clerk.
Extract every distinct invoice, payment or transaction in the document as its own record.
Rules:
- Dates in YYYY-MM-DD format. Amounts as pure numbers without currency symbols or thousands separators.
- tax_amount only if VAT/BTW/tax is explicitly stated; otherwise 0.0.
- Use "N/A" for missing text fields. Never invent or guess values that are not in the document.
- Set confidence between 0.0 and 1.0 based on how clear and complete the source text is."""

INVENTORY_PROMPT = """You are a meticulous warehouse data entry clerk.
Extract every counted item or stock line in the document as its own record.
Rules:
- quantity is the counted number of units as a whole number.
- Use "N/A" for missing text fields. Never invent or guess values that are not in the document.
- Set confidence between 0.0 and 1.0 based on how clear and complete the source text is."""

TIMESHEET_PROMPT = """You are a meticulous payroll data entry clerk.
Extract one record per employee per period from the timesheet.
Rules:
- hours is the total hours for the period as a number (sum the days if only daily hours are given).
- Use "N/A" for missing text fields. Never invent or guess values that are not in the document.
- Set confidence between 0.0 and 1.0 based on how clear and complete the source text is."""

# --- Register Default Plugins ---
ProcessorRegistry.register("ledger", InvoiceDocument, INVOICE_PROMPT)
ProcessorRegistry.register("invoice", InvoiceDocument, INVOICE_PROMPT)
ProcessorRegistry.register("inventory", InventoryDocument, INVENTORY_PROMPT)
ProcessorRegistry.register("timesheet", TimesheetDocument, TIMESHEET_PROMPT)
