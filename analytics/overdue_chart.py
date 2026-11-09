import pandas as pd
import matplotlib.pyplot as plt

# Load invoice data
invoices = pd.read_csv("data/raw/invoices.csv")

# Convert due date
invoices["due_date"] = pd.to_datetime(invoices["due_date"])

# Reporting date
reporting_date = pd.Timestamp("2026-10-27")

# Filter overdue unpaid invoices
overdue = invoices[
    (invoices["status"] == "Unpaid")
    & (invoices["due_date"] < reporting_date)
]

# Calculate overdue amounts
overdue_summary = overdue.set_index("invoice_id")["amount_eur"]

# Create chart
plt.figure(figsize=(8, 5))
overdue_summary.plot(kind="bar")

plt.title("Mittelstand AI — Overdue Invoice Amounts")
plt.xlabel("Invoice ID")
plt.ylabel("Overdue Amount (€)")
plt.xticks(rotation=0)
plt.tight_layout()

# Save chart
plt.savefig("data/processed/overdue_invoices.png", dpi=150)

plt.show()

print("Overdue invoice chart saved successfully!")
print(f"Overdue invoices: {len(overdue)}")
print(f"Total overdue value: €{overdue['amount_eur'].sum():,.2f}")
