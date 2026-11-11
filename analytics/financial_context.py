
import pandas as pd

from analytics.database import fetch_dataframe


def get_financial_context(reporting_date="2026-10-27"):

    invoices = fetch_dataframe(
        "SELECT * FROM invoices"
    )

    if invoices.empty:
        return "No supplier invoice records found."

    invoices["amount_eur"] = pd.to_numeric(
        invoices["amount_eur"], errors="coerce"
    )

    invoices["due_date"] = pd.to_datetime(
        invoices["due_date"], errors="coerce"
    )

    invoices["status"] = invoices["status"].str.strip().str.title()

    reporting_date = pd.Timestamp(reporting_date)

    paid = invoices[invoices["status"] == "Paid"]
    unpaid = invoices[invoices["status"] == "Unpaid"]

    overdue = unpaid[
        unpaid["due_date"] < reporting_date
    ]

    not_yet_due = unpaid[
        unpaid["due_date"] >= reporting_date
    ]

    total_value = invoices["amount_eur"].sum()
    paid_value = paid["amount_eur"].sum()
    unpaid_value = unpaid["amount_eur"].sum()
    overdue_value = overdue["amount_eur"].sum()
    not_yet_due_value = not_yet_due["amount_eur"].sum()

    supplier_exposure = (
        unpaid.groupby("supplier")["amount_eur"]
        .sum().sort_values(ascending=False)
    )

    overdue_by_supplier = (
        overdue.groupby("supplier")["amount_eur"]
        .sum().sort_values(ascending=False)
    )

    context = f"""
MITTELSTAND AI — VERIFIED SUPPLIER FINANCIAL REPORT

Reporting date: {reporting_date.date()}

BUSINESS PERSPECTIVE:

These are invoices OUR BUSINESS received from suppliers.

OUR BUSINESS owes the suppliers money.

An overdue invoice means OUR BUSINESS has not paid
the supplier by the invoice due date.

VERIFIED FINANCIAL FIGURES:

Total invoices: {len(invoices)}

Total invoice value: €{total_value:,.2f}

Paid amount: €{paid_value:,.2f}

Total unpaid amount: €{unpaid_value:,.2f}

Overdue invoices: {len(overdue)}

Overdue amount: €{overdue_value:,.2f}

Unpaid but NOT overdue invoices: {len(not_yet_due)}

Unpaid but NOT overdue amount: €{not_yet_due_value:,.2f}

SUPPLIER UNPAID EXPOSURE:

{supplier_exposure.to_string()}

SUPPLIER OVERDUE EXPOSURE:

{overdue_by_supplier.to_string()}

IMPORTANT:

The unpaid but not overdue amount is already calculated:

€{not_yet_due_value:,.2f}

Do not recalculate or change these verified figures.

"""

    return context
