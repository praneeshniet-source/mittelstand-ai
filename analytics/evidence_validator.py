
import re


# Recognised invoice fields and their labels in English and German.
FIELD_PATTERNS = {
    "invoice_number": (
        r"\binvoice\s*(?:number|no\.?|na)\b",
        r"\brechnungsnummer\b",
    ),
    "supplier": (
        r"\bsupplier\b",
        r"\bvendor\b",
        r"\blieferant\b",
    ),
    "invoice_date": (
        r"\binvoice\s*date\b",
        r"\brechnungsdatum\b",
    ),
    "due_date": (
        r"\bpayment\s*due\s*date\b",
        r"\bdue\s*date\b",
        r"\bfälligkeitsdatum\b",
    ),
    "amount": (
        r"\bamount\b",
        r"\btotal\b",
        r"\bgesamtbetrag\b",
    ),
    "bank_account": (
        r"\bbank\s*account\b",
        r"\biban\b",
        r"\baccount\s*(?:number|details)\b",
    ),
}


QUESTION_INTENTS = {
    "invoice_number": (
        "invoice number", "invoice no", "rechnungsnummer",
    ),
    "supplier": (
        "which supplier", "who issued", "supplier name",
        "vendor name", "lieferant",
    ),
    "invoice_date": (
        "invoice date", "when was the invoice issued",
        "rechnungsdatum",
    ),
    "due_date": (
        "due date", "payment deadline", "when is payment due",
        "fälligkeitsdatum",
    ),
    "amount": (
        "amount", "total", "how much", "invoice value",
        "gesamtbetrag",
    ),
    "bank_account": (
        "bank account", "iban", "account number",
    ),
}


IDENTIFIER_PATTERN = (
    r"\b[A-Z]{2,5}-\d{3,4}(?:-\d{3,4})?\b"
)


def detect_invoice_identifiers(question):
    """Extract invoice-style identifiers from a question."""
    return {
        value.upper()
        for value in re.findall(
            IDENTIFIER_PATTERN,
            question.upper()
        )
    }


def detect_question_intent(question):
    """Identify which invoice field the user is asking about."""
    normalised_question = question.lower()

    for field, phrases in QUESTION_INTENTS.items():
        if any(
            phrase in normalised_question
            for phrase in phrases
        ):
            return field

    return None

def extract_supplier_name(document):
    """Extract supplier name from an invoice document."""

    match = re.search(
        r"^\s*(?:Supplier|Vendor|Lieferant)\s*[:#]?\s*(.+)$",
        document,
        re.IGNORECASE | re.MULTILINE
    )

    if match:
        return match.group(1).strip()

    return None

def validate_evidence(question, results):
    """
    Check whether retrieved document chunks contain
    evidence relevant to the requested invoice information.
    """

    if not question or not question.strip():
        return {
            "supported": False,
            "relevant_results": [],
            "reason": "The question is empty.",
        }

    if not results:
        return {
            "supported": False,
            "relevant_results": [],
            "reason": "No documents were retrieved.",
        }

    # Priority 1: Exact invoice identifier.
    identifiers = detect_invoice_identifiers(question)

    if identifiers:
        matching_results = [
            result for result in results
            if any(
                identifier in result["document"].upper()
                for identifier in identifiers
            )
        ]

        if matching_results:
            return {
                "supported": True,
                "relevant_results": matching_results,
                "reason": "Exact invoice identifier found.",
            }

        return {
            "supported": False,
            "relevant_results": [],
            "reason": "The requested invoice identifier was not found.",
        }

    # Priority 2: Recognised invoice-field questions.
    intent = detect_question_intent(question)

    if intent is None:
        return {
            "supported": False,
            "relevant_results": [],
            "reason": "The question does not match a recognised invoice field.",
        }

    patterns = FIELD_PATTERNS[intent]

    matching_results = [
        result for result in results
        if any(
            re.search(pattern, result["document"], re.IGNORECASE)
            for pattern in patterns
        )
    ]

    if not matching_results:
        return {
            "supported": False,
            "relevant_results": [],
            "reason": f"No evidence for the requested field: {intent}.",
        }

       # Match the supplier named in the question.
    question_normalised = re.sub(
        r"[^a-z0-9]",
        "",
        question.lower()
    )

    supplier_matches = []

    for result in matching_results:
        supplier = extract_supplier_name(result["document"])

        if supplier:
            supplier_normalised = re.sub(
                r"[^a-z0-9]",
                "",
                supplier.lower()
            )

            if supplier_normalised in question_normalised:
                supplier_matches.append(result)

        # Reject explicitly requested suppliers not found in documents.
    supplier_reference = re.search(
        r"\b(?:for|of)\s+(.+?)(?:\?|$)",
        question,
        re.IGNORECASE
    )

    if supplier_reference and not supplier_matches:
        return {
            "supported": False,
            "relevant_results": [],
            "reason": "The requested supplier was not found in the documents.",
        }

    if supplier_matches:
        matching_results = supplier_matches

    return {
        "supported": True,
        "relevant_results": matching_results,
        "reason": f"Document evidence found for: {intent}.",
    }