
import pytest

from analytics.invoice_importer import check_duplicate_invoice


@pytest.fixture
def exact_duplicate():
    return {
        "invoice_number": "INV001",
        "supplier": "Berlin Components GmbH",
        "invoice_date": "2026-09-01",
        "due_date": "2026-09-30",
        "amount": 1200
    }


def test_existing_invoice_id_is_duplicate(exact_duplicate):
    result = check_duplicate_invoice(exact_duplicate)

    assert result == "DUPLICATE"


def test_matching_supplier_date_and_amount_is_potential_duplicate():
    invoice = {
        "invoice_number": "INV999",
        "supplier": "Berlin Components GmbH",
        "invoice_date": "2026-09-01",
        "due_date": "2026-09-30",
        "amount": 1200
    }

    result = check_duplicate_invoice(invoice)

    assert result == "POTENTIAL_DUPLICATE"


def test_new_invoice_is_unique():
    invoice = {
        "invoice_number": "INV998",
        "supplier": "New Supplier GmbH",
        "invoice_date": "2026-10-20",
        "due_date": "2026-11-20",
        "amount": 750
    }

    result = check_duplicate_invoice(invoice)

    assert result == "UNIQUE"
