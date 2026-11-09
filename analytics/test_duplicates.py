
from invoice_importer import check_duplicate_invoice

# Test 1: Existing invoice ID
exact_duplicate = {
    "invoice_number": "INV001",
    "supplier": "Berlin Components GmbH",
    "invoice_date": "2026-09-01",
    "due_date": "2026-09-30",
    "amount": 1200
}

# Test 2: New ID, but matching supplier, date and amount
potential_duplicate = {
    "invoice_number": "INV999",
    "supplier": "Berlin Components GmbH",
    "invoice_date": "2026-09-01",
    "due_date": "2026-09-30",
    "amount": 1200
}

# Test 3: Completely new invoice
unique_invoice = {
    "invoice_number": "INV998",
    "supplier": "New Supplier GmbH",
    "invoice_date": "2026-10-20",
    "due_date": "2026-11-20",
    "amount": 750
}

print("Test 1:", check_duplicate_invoice(exact_duplicate))
print("Test 2:", check_duplicate_invoice(potential_duplicate))
print("Test 3:", check_duplicate_invoice(unique_invoice))
