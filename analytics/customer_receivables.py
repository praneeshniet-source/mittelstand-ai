import pandas as pd

from analytics.database import fetch_dataframe


# Load customer invoices from PostgreSQL
df = fetch_dataframe(
    "SELECT * FROM customer_invoices ORDER BY invoice_id"
)

# Convert numeric and date columns
df["amount_eur"] = pd.to_numeric(
    df["amount_eur"], errors="coerce"
)

for column in ["invoice_date", "due_date", "payment_date"]:
    df[column] = pd.to_datetime(df[column], errors="coerce")

# Reporting date
reporting_date = pd.Timestamp("2026-10-27")

# Separate paid and unpaid invoices
paid = df[df["status"] == "Paid"].copy()
unpaid = df[df["status"] == "Unpaid"].copy()

# Calculate receivables
total_invoiced = df["amount_eur"].sum()
collected_amount = paid["amount_eur"].sum()
outstanding_amount = unpaid["amount_eur"].sum()

# Identify overdue customer invoices
overdue = unpaid[
    unpaid["due_date"] < reporting_date
].copy()

overdue["days_overdue"] = (
    reporting_date - overdue["due_date"]
).dt.days

overdue_amount = overdue["amount_eur"].sum()

# Calculate customer-wise outstanding amounts
customer_exposure = (
    unpaid.groupby("customer")["amount_eur"]
    .sum()
    .sort_values(ascending=False)
)

# Calculate average payment delay
paid["payment_delay_days"] = (
    paid["payment_date"] - paid["due_date"]
).dt.days

average_delay = paid["payment_delay_days"].mean()

# Display results
print("\nCUSTOMER RECEIVABLES ANALYSIS")
print("-" * 40)

print(f"Total invoices: {len(df)}")
print(f"Paid invoices: {len(paid)}")
print(f"Unpaid invoices: {len(unpaid)}")

print(f"\nTotal invoiced: €{total_invoiced:,.2f}")
print(f"Amount collected: €{collected_amount:,.2f}")
print(f"Outstanding receivables: €{outstanding_amount:,.2f}")

print(f"\nOverdue invoices: {len(overdue)}")
print(f"Overdue amount: €{overdue_amount:,.2f}")

print("\nCUSTOMER-WISE OUTSTANDING")
print(customer_exposure)

if pd.isna(average_delay):
    print("\nAverage payment delay: Not available")
else:
    print(f"\nAverage payment delay: {average_delay:.1f} days")

print("\nOVERDUE INVOICE DETAILS")

if overdue.empty:
    print("No overdue invoices.")
else:
    print(
        overdue[
            [
                "invoice_id",
                "customer",
                "amount_eur",
                "due_date",
                "days_overdue"
            ]
        ].to_string(index=False)
    )
