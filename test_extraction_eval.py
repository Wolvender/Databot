# test_extraction_eval.py - End-to-end extraction quality check
"""
Runs the real extraction pipeline (router -> schema -> LLM -> validation)
over the realistic business documents in test_documents/ and prints what
a company would actually get back. No Streamlit session needed.

Run with:  python test_extraction_eval.py
"""

import json
from pathlib import Path

from file_handler import extract_text
from router import Router
from processor_registry import ProcessorRegistry
from validators import DataValidator
from data_processor import DataProcessor
from langchain_groq import ChatGroq
from config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE

TEST_DIR = Path("test_documents")


def run_eval():
    llm = ChatGroq(model=LLM_MODEL, temperature=LLM_TEMPERATURE, groq_api_key=GROQ_API_KEY)
    router = Router()

    files = sorted(TEST_DIR.glob("*.txt"))
    if not files:
        print(f"No test files found in {TEST_DIR}/")
        return

    total_records = 0
    review_records = 0

    for path in files:
        print(f"\n{'=' * 70}")
        print(f"FILE: {path.name}")
        print('=' * 70)

        text = extract_text(path.read_bytes(), path.name)
        doc_type = router.identify_type(text)
        plugin = ProcessorRegistry.get(doc_type)
        if not plugin:
            doc_type = "ledger"
            plugin = ProcessorRegistry.get(doc_type)
        print(f"Routed as: {doc_type}")

        structured_llm = llm.with_structured_output(plugin.schema)
        result = structured_llm.invoke(f"{plugin.system_prompt}\n\nContent:\n{text}").model_dump()

        confidence = result.get("confidence", 0.0)
        records = result.get("records") or [result]
        print(f"Confidence: {confidence:.2f} | Records found: {len(records)}")

        for i, record in enumerate(records):
            for money_field in ("amount", "tax_amount"):
                if money_field in record:
                    record[money_field] = DataProcessor.clean_number(record[money_field])
            if "currency" in record:
                record["currency"] = DataProcessor.normalize_currency(record["currency"])

            issues = DataValidator.validate_record(record, doc_type)
            has_errors = any(x.get("severity") == "error" for x in issues)
            status = "REVIEW" if has_errors else "OK"

            total_records += 1
            if has_errors:
                review_records += 1

            print(f"\n  Record {i + 1} [{status}]")
            for key, value in record.items():
                print(f"    {key:<12} {value}")
            for issue in issues:
                print(f"    ! {issue['severity']}: {issue['field']} - {issue['message']}")

    print(f"\n{'=' * 70}")
    print(f"SUMMARY: {total_records} records extracted from {len(files)} documents, "
          f"{review_records} flagged for review")
    print('=' * 70)


if __name__ == "__main__":
    run_eval()
