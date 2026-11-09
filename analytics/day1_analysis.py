
import pandas as pd

# 1. Load invoice data
file_path = "data/raw/invoices.csv"
invoices = pd.read_csv(file_path)

# 2. Convert date columns into actual dates
invoices["invoice_date"] = pd.to_datetime(invoices["invoice_date"])
invoices["due_date"] = pd.to_datetime(invoices["due_date"])

# Use a fixed reporting date for reproducible results
reporting_date = pd.Timestamp("2026-10-27")

# 3. Basic business metrics
total_invoices = len(invoices)
total_value = invoices["amount_eur"].sum()

paid_invoices = invoices[invoices["status"] == "Paid"]
unpaid_invoices = invoices[invoices["status"] == "Unpaid"]

paid_value = paid_invoices["amount_eur"].sum()
unpaid_value = unpaid_invoices["amount_eur"].sum()

# 4. Identify overdue unpaid invoices
overdue_invoices = unpaid_invoices[
    unpaid_invoices["due_date"] < reporting_date
]

overdue_count = len(overdue_invoices)
overdue_value = overdue_invoices["amount_eur"].sum()

# 5. Supplier spending
supplier_spend = (
    invoices.groupby("supplier")["amount_eur"]
    .sum()
    .sort_values(ascending=False)
)

# 6. Print results
print("===== MITTELSTAND AI: BUSINESS REPORT =====")

print(f"\nTotal invoices: {total_invoices}")
print(f"Total invoice value: €{total_value:,.2f}")

print("\n--- PAYMENT SUMMARY ---")
print(f"Paid invoice value: €{paid_value:,.2f}")
print(f"Unpaid invoice value: €{unpaid_value:,.2f}")

print("\n--- OVERDUE SUMMARY ---")
print(f"Overdue unpaid invoices: {overdue_count}")
print(f"Overdue invoice value: €{overdue_value:,.2f}")

print("\n--- SPENDING BY SUPPLIER ---")
print(supplier_spend.to_string())
