import pandas as pd

# Load invoice data
invoices = pd.read_csv("data/raw/invoices.csv")

print("===== MITTELSTAND AI: DATA QUALITY REPORT =====")

# 1. Check missing values
print("\n--- MISSING VALUES ---")
print("Missing supplier names:", invoices["supplier"].isna().sum())
print("Missing amounts:", invoices["amount_eur"].isna().sum())
print("Missing due dates:", invoices["due_date"].isna().sum())

# 2. Check duplicate invoice IDs
print("\n--- DUPLICATE INVOICE IDs ---")
duplicates = invoices[invoices["invoice_id"].duplicated(keep=False)]
print("Duplicate rows found:", len(duplicates))

# 3. Check invalid amounts
print("\n--- INVALID AMOUNTS ---")
invalid_amounts = invoices[invoices["amount_eur"] <= 0]
print("Invalid amount rows:", len(invalid_amounts))

# 4. Check invoice date order
print("\n--- INVALID DATE ORDER ---")
invoices["invoice_date"] = pd.to_datetime(
    invoices["invoice_date"], errors="coerce"
)
invoices["due_date"] = pd.to_datetime(
    invoices["due_date"], errors="coerce"
)

invalid_dates = invoices[
    invoices["invoice_date"].isna()
    | invoices["due_date"].isna()
    | (invoices["due_date"] < invoices["invoice_date"])
]

print("Invalid date rows:", len(invalid_dates))
