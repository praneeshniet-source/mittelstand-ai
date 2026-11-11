import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
from analytics.database import fetch_dataframe


# STEP 1: Load supplier invoices from PostgreSQL

invoices = fetch_dataframe(
    "SELECT * FROM invoices ORDER BY invoice_id"
)


# Convert PostgreSQL Decimal values into numeric data

invoices["amount_eur"] = pd.to_numeric(
    invoices["amount_eur"],
    errors="coerce"
)


# STEP 2: Create output directory

output_dir = Path("data/processed")
output_dir.mkdir(parents=True, exist_ok=True)


# STEP 3: Calculate supplier spending

supplier_spend = (
    invoices.groupby("supplier")["amount_eur"]
    .sum()
    .sort_values(ascending=True)
)


# STEP 4: Create supplier spending chart

fig, ax = plt.subplots(figsize=(10, 6))
supplier_spend.plot(kind="barh", ax=ax)

ax.set_title("Mittelstand AI — Supplier Spending")
ax.set_xlabel("Invoice Value (€)")
ax.set_ylabel("Supplier")

fig.tight_layout()
fig.savefig(output_dir / "supplier_spending.png", dpi=150)
plt.close(fig)

print("Supplier spending chart saved successfully!")


# STEP 5: Calculate payment summary

payment_summary = (
    invoices.groupby("status")["amount_eur"].sum()
)


# STEP 6: Create payment comparison chart

fig, ax = plt.subplots(figsize=(8, 6))
payment_summary.plot(kind="bar", ax=ax)

ax.set_title("Mittelstand AI — Paid vs Unpaid Invoice Value")
ax.set_xlabel("Payment Status")
ax.set_ylabel("Invoice Value (€)")
ax.tick_params(axis="x", rotation=0)

fig.tight_layout()
fig.savefig(output_dir / "payment_summary.png", dpi=150)
plt.close(fig)

print("Payment chart saved successfully!")


# STEP 7: Identify overdue invoices

reporting_date = pd.Timestamp("2026-10-27")

invoices["due_date"] = pd.to_datetime(
    invoices["due_date"],
    errors="coerce"
)

overdue = invoices[
    (invoices["status"].str.strip().str.lower() == "unpaid")
    & (invoices["due_date"] < reporting_date)
].copy()


# STEP 8: Create overdue invoice chart

overdue_summary = overdue.set_index("invoice_id")["amount_eur"]

fig, ax = plt.subplots(figsize=(8, 5))

if overdue_summary.empty:
    ax.text(
        0.5, 0.5, "No overdue invoices",
        ha="center", va="center",
        transform=ax.transAxes
    )
    ax.set_axis_off()
else:
    overdue_summary.plot(kind="bar", ax=ax)
    ax.set_xlabel("Invoice ID")
    ax.set_ylabel("Overdue Amount (€)")
    ax.tick_params(axis="x", rotation=0)

ax.set_title("Mittelstand AI — Overdue Invoice Amounts")

fig.tight_layout()
fig.savefig(output_dir / "overdue_invoices.png", dpi=150)
plt.close(fig)

print("Overdue invoice chart saved successfully!")
print("\nALL FINANCIAL CHARTS GENERATED")
