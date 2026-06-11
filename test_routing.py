from router import Router

# --- Test Script ---
if __name__ == "__main__":
    router = Router()

    test_inputs = [
        ("Invoice #123 from Apple, $500 total, date 2023-10-01", "invoice"),
        ("Storage box A contains 50 hammers", "inventory")
    ]
    
    for text, expected in test_inputs:
        result = router.identify_type(text)
        print(f"Text: {text[:30]}... -> Predicted: {result} (Expected: {expected})")
        assert result == expected
    
    print("Routing test passed!")
