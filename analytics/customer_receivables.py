
import pandas as pd

# Load customer invoice dataset
df = pd.read_csv("data/raw/customer_invoices.csv")

# Convert date columns
df["invoice_date"] = pd.to_datetime(df["invoice_date"])
df["due_date"] = pd.to_datetime(df["due_date"])
df["payment_date"] = pd.to_datetime(df["payment_date"])

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

# Calculate average payment delay for paid invoices
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

print(f"\nAverage payment delay: {average_delay:.1f} days")

print("\nOVERDUE INVOICE DETAILS")
if overdue.empty:
    print("No overdue invoices.")
else:
    print(overdue[[
        "invoice_id",
        "customer",
        "amount_eur",
        "due_date",
        "days_overdue"
    ]].to_string(index=False))
