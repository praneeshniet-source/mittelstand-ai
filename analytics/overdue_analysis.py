import pandas as pd

# Load invoice data
invoices = pd.read_csv("data/raw/invoices.csv")

# Convert due dates into dates
invoices["due_date"] = pd.to_datetime(invoices["due_date"])

# Set the reporting date
reporting_date = pd.Timestamp("2026-10-27")

# Identify overdue, unpaid invoices
overdue = invoices[
    (invoices["status"] == "Unpaid")
    & (invoices["due_date"] < reporting_date)
].copy()

# Calculate days overdue
overdue["days_overdue"] = (
    reporting_date - overdue["due_date"]
).dt.days

# Display results
print("===== MITTELSTAND AI: OVERDUE INVOICES =====")

if overdue.empty:
    print("No overdue unpaid invoices found.")
else:
    print(
        overdue[
            [
                "invoice_id",
                "supplier",
                "amount_eur",
                "due_date",
                "days_overdue",
            ]
        ].to_string(index=False)
    )

    print(f"\nOverdue invoice count: {len(overdue)}")
    print(f"Total overdue value: €{overdue['amount_eur'].sum():,.2f}")
