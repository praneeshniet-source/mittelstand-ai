import pandas as pd
import matplotlib.pyplot as plt

# Load invoice data
invoices = pd.read_csv("data/raw/invoices.csv")

# Calculate total spending by supplier
supplier_spend = (
    invoices.groupby("supplier")["amount_eur"]
    .sum()
    .sort_values(ascending=True)
)

# Create the chart
plt.figure(figsize=(10, 6))
supplier_spend.plot(kind="barh")

# Calculate paid and unpaid invoice values
payment_summary = (
    invoices.groupby("status")["amount_eur"]
    .sum()
)

# Create payment comparison chart
plt.figure(figsize=(8, 6))

payment_summary.plot(kind="bar")

plt.title("Mittelstand AI — Paid vs Unpaid Invoice Value")
plt.xlabel("Payment Status")
plt.ylabel("Invoice Value (€)")
plt.xticks(rotation=0)
plt.tight_layout()

# Save chart
plt.savefig("data/processed/payment_summary.png", dpi=150)

plt.show()

print("Payment chart saved successfully!")
plt.xlabel("Invoice Value (€)")
plt.ylabel("Supplier")
plt.tight_layout()

# Save the chart
plt.savefig("data/processed/supplier_spending.png", dpi=150)

# Display the chart
plt.show()

print("Chart saved to data/processed/supplier_spending.png")
# Identify overdue unpaid invoices
reporting_date = pd.Timestamp("2026-10-27")

invoices["due_date"] = pd.to_datetime(invoices["due_date"])

overdue = invoices[
    (invoices["status"] == "Unpaid")
    & (invoices["due_date"] < reporting_date)
]

# Calculate overdue amounts by invoice
overdue_summary = overdue.set_index("invoice_id")["amount_eur"]

# Create overdue chart
plt.figure(figsize=(8, 5))

overdue_summary.plot(kind="bar")

plt.title("Mittelstand AI — Overdue Invoice Amounts")
plt.xlabel("Invoice ID")
plt.ylabel("Overdue Amount (€)")
plt.xticks(rotation=0)
plt.tight_layout()

plt.savefig("data/processed/overdue_invoices.png", dpi=150)

plt.show()

print("Overdue invoice chart saved successfully!")
