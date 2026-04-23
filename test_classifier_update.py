import sys
import os

# Ensure the script can import from DataEntry
sys.path.append(os.path.join(os.getcwd(), "DataEntry"))

from test_routing import Router

def test_manual_routing():
    router = Router()
    
    samples = {
        "invoice": "Invoice #123 from Apple, $500 total, date 2023-10-01",
        "inventory": "Inventory Report - April 2026. Items: Hammer: 45 units, Screwdriver: 120 units."
    }
    
    for category, text in samples.items():
        predicted = router.identify_type(text)
        print(f"Sample: {category} | Predicted: {predicted}")

if __name__ == "__main__":
    test_manual_routing()
