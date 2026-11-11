from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from analytics.database import fetch_dataframe


# Load supplier invoices from PostgreSQL
invoices = fetch_dataframe(
    "SELECT * FROM invoices ORDER BY invoice_id"
)

# Convert PostgreSQL values for analysis and plotting
invoices["amount_eur"] = pd.to_numeric(
    invoices["amount_eur"], errors="coerce"
)
invoices["due_date"] = pd.to_datetime(
    invoices["due_date"], errors="coerce"
)

# Reporting configuration
reporting_date = pd.Timestamp("2026-10-27")

# Identify overdue unpaid invoices
overdue = invoices[
    (invoices["status"].str.strip().str.lower() == "unpaid")
    & (invoices["due_date"] < reporting_date)
].copy()

# Prepare output directory
output_dir = Path("data/processed")
output_dir.mkdir(parents=True, exist_ok=True)

# Create chart
fig, ax = plt.subplots(figsize=(8, 5))

if overdue.empty:
    ax.text(
        0.5, 0.5,
        "No overdue invoices",
        ha="center",
        va="center",
        transform=ax.transAxes
    )
    ax.set_axis_off()
else:
    overdue_summary = overdue.set_index("invoice_id")["amount_eur"]
    overdue_summary.plot(kind="bar", ax=ax)
    ax.set_xlabel("Invoice ID")
    ax.set_ylabel("Overdue Amount (€)")
    ax.tick_params(axis="x", rotation=0)

ax.set_title("Mittelstand AI — Overdue Invoice Amounts")
fig.tight_layout()

# Save chart
fig.savefig(output_dir / "overdue_invoices.png", dpi=150)
plt.close(fig)

# Display results
print("Overdue invoice chart saved successfully!")
print(f"Overdue invoices: {len(overdue)}")
print(
    f"Total overdue value: "
    f"€{overdue['amount_eur'].sum():,.2f}"
)
