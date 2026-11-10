
import sys

from analytics.rag_pipeline import search_documents


TEST_CASES = [
    {
        "question": "Which supplier issued invoice DE-2026-001?",
        "expected_source": "german_invoice.pdf",
    },
    {
        "question": "What is the invoice number for Munich Tools AG?",
        "expected_source": "german_invoice.pdf",
    },
    {
        "question": "Which supplier issued invoice TEST-001?",
        "expected_source": "sample_invoice.pdf",
    },
    {
        "question": "What is the invoice number for Berlin Components GmbH?",
        "expected_source": "sample_invoice.pdf",
    },
    {
        "question": "Which supplier issued invoice OCR-001?",
        "expected_source": "scanned_invoice.pdf",
    },
]


def run_tests():
    passed = 0
    failed = 0

    print("\nRAG RETRIEVAL EVALUATION")
    print("=" * 55)

    for test in TEST_CASES:
        question = test["question"]
        expected = test["expected_source"]

        try:
            results = search_documents(question, top_k=3)
            actual = results[0]["source"] if results else None

            success = actual == expected

            if success:
                passed += 1
            else:
                failed += 1

            print(f"\nQuestion: {question}")
            print(f"Expected: {expected}")
            print(f"Actual:   {actual}")
            print(f"Result:   {'PASS' if success else 'FAIL'}")

        except Exception as error:
            failed += 1
            print(f"\nQuestion: {question}")
            print(f"ERROR: {error}")
            print("Result: FAIL")

    total = len(TEST_CASES)

    print("\n" + "=" * 55)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {failed}/{total}")
    print(f"Accuracy: {(passed / total) * 100:.1f}%")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
