
import sqlite3
import pandas as pd

# Reporting configuration
REPORTING_DATE = pd.Timestamp("2026-10-27")
OPENING_CASH = 20000

# Load customer invoices
customers = pd.read_csv("data/raw/customer_invoices.csv")

customers["due_date"] = pd.to_datetime(
    customers["due_date"]
)

customers["payment_date"] = pd.to_datetime(
    customers["payment_date"]
)

# Load supplier invoices from SQLite
connection = sqlite3.connect("mittelstand.db")

suppliers = pd.read_sql_query(
    "SELECT * FROM invoices",
    connection
)

connection.close()

suppliers["due_date"] = pd.to_datetime(
    suppliers["due_date"]
)

# Calculate expected customer collections
unpaid_customers = customers[
    customers["status"] == "Unpaid"
].copy()

unpaid_customers["expected_date"] = unpaid_customers[
    "due_date"
].clip(lower=REPORTING_DATE)

# Calculate expected supplier payments
unpaid_suppliers = suppliers[
    suppliers["status"] == "Unpaid"
].copy()

unpaid_suppliers["due_date"] = pd.to_datetime(
    unpaid_suppliers["due_date"]
)

unpaid_suppliers["expected_date"] = unpaid_suppliers[
    "due_date"
].clip(lower=REPORTING_DATE)

# Define 30-day forecast period
forecast_end = REPORTING_DATE + pd.Timedelta(days=30)

unpaid_customers = unpaid_customers[
    unpaid_customers["expected_date"] <= forecast_end
]

unpaid_suppliers = unpaid_suppliers[
    unpaid_suppliers["expected_date"] <= forecast_end
]

# Daily incoming collections
daily_incoming = (
    unpaid_customers.groupby("expected_date")["amount_eur"]
    .sum()
)

# Daily outgoing supplier payments
daily_outgoing = (
    unpaid_suppliers.groupby("expected_date")["amount_eur"]
    .sum()
)

# Create daily cash flow table
dates = pd.date_range(
    REPORTING_DATE,
    forecast_end,
    freq="D"
)

cash_flow = pd.DataFrame(index=dates)

cash_flow.index.name = "date"

cash_flow["Expected Customer Collections (€)"] = (
    daily_incoming.reindex(dates, fill_value=0)
)

cash_flow["Expected Supplier Payments (€)"] = (
    daily_outgoing.reindex(dates, fill_value=0)
)

cash_flow["Net Cash Flow (€)"] = (
    cash_flow["Expected Customer Collections (€)"]
    - cash_flow["Expected Supplier Payments (€)"]
)

cash_flow["Projected Cash Balance (€)"] = (
    OPENING_CASH
    + cash_flow["Net Cash Flow (€)"].cumsum()
)

# Calculate summary metrics
total_incoming = cash_flow[
    "Expected Customer Collections (€)"
].sum()

total_outgoing = cash_flow[
    "Expected Supplier Payments (€)"
].sum()

net_cash_flow = total_incoming - total_outgoing

closing_cash = OPENING_CASH + net_cash_flow

# Display results
print("\nNET CASH FLOW ANALYSIS")
print("-" * 45)

print(f"Opening cash balance: €{OPENING_CASH:,.2f}")
print(f"Expected customer collections: €{total_incoming:,.2f}")
print(f"Expected supplier payments: €{total_outgoing:,.2f}")
print(f"Net cash flow: €{net_cash_flow:,.2f}")
print(f"Projected closing cash: €{closing_cash:,.2f}")

print("\nDAILY CASH FLOW")
print(
    cash_flow[
        [
            "Expected Customer Collections (€)",
            "Expected Supplier Payments (€)",
            "Net Cash Flow (€)",
            "Projected Cash Balance (€)"
        ]
    ].to_string()
)

# Identify potential cash shortages
negative_balance = cash_flow[
    cash_flow["Projected Cash Balance (€)"] < 0
]

print("\nCASH SHORTAGE CHECK")

if negative_balance.empty:
    print("No projected negative cash balance.")
else:
    print("Warning: Projected cash balance becomes negative.")
    print(negative_balance)
