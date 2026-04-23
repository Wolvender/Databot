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

# --- Example Schemas ---

class LedgerSchema(BaseModel):
    date: str = Field(description="Date found in document")
    entity: str = Field(description="Company or Person name")
    amount: str = Field(description="Total amount as a number, e.g. 1100.00")
    currency: str = Field(description="3-letter currency code (e.g. EUR, USD).")

class InventorySchema(BaseModel):
    item_name: str = Field(description="Name of the item")
    quantity: int = Field(description="Number of items")
    location: str = Field(description="Storage location")

# --- Register Default Plugins ---
ProcessorRegistry.register("ledger", LedgerSchema, "Extract invoice details.")
ProcessorRegistry.register("invoice", LedgerSchema, "Extract invoice details.")
ProcessorRegistry.register("inventory", InventorySchema, "Extract inventory counts.")
