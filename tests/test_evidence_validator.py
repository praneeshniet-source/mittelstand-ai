
import sys

from analytics.evidence_validator import validate_evidence


def make_result(document, source="test_invoice.pdf"):
    return {
        "document": document,
        "source": source,
    }


invoice = make_result("""
INVOICE
Invoice Number: DE-2026-001
Supplier: Munich Tools AG
Invoice Date: 2026-10-05
Due Date: 2026-11-05
Amount: 2450.75 EUR
""")

tests = [
    (
        "Which supplier issued invoice DE-2026-001?",
        [invoice],
        True,
    ),
    (
        "What is the due date for Munich Tools AG?",
        [invoice],
        True,
    ),
    (
        "What is the employee salary structure?",
        [invoice],
        False,
    ),
    (
        "What is the bank account number?",
        [invoice],
        False,
    ),
    (
        "Which supplier issued invoice XX-999?",
        [invoice],
        False,
    ),
    (
        "What is the due date for Unknown Supplier GmbH?",
        [invoice],
        False,
    ),
    (
        "",
        [invoice],
        False,
    ),
]


def run_tests():
    passed = 0
    failed = 0

    print("\nEVIDENCE VALIDATION TESTS")
    print("=" * 55)

    for question, results, expected in tests:
        try:
            output = validate_evidence(question, results)
            actual = output["supported"]
            success = actual == expected

            if success:
                passed += 1
            else:
                failed += 1

            print(f"\nQuestion: {question or '[EMPTY QUESTION]'}")
            print(f"Expected: {expected}")
            print(f"Actual:   {actual}")
            print(f"Reason:   {output['reason']}")
            print(f"Result:   {'PASS' if success else 'FAIL'}")

        except Exception as error:
            failed += 1
            print(f"\nQuestion: {question or '[EMPTY QUESTION]'}")
            print(f"ERROR: {error}")
            print("Result: FAIL")

    total = len(tests)

    print("\n" + "=" * 55)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {failed}/{total}")
    print(f"Accuracy: {(passed / total) * 100:.1f}%")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
