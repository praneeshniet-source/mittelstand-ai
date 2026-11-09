
# Day 11 — Net Cash Flow Analysis

## Objective
Combine customer receivables and supplier payables to estimate the business's projected cash position.

## Data Sources
- Customer invoices: data/raw/customer_invoices.csv
- Supplier invoices: mittelstand.db
- Reporting date: 27 October 2026

## Key Results
- Opening cash: €20,000
- Expected customer collections: €20,000
- Expected supplier payments: €11,750
- Net cash flow: €8,250
- Projected closing cash: €28,250

## Features Implemented
- Customer invoice data integration.
- Supplier invoice data integration using SQLite.
- Overdue customer collections scheduled on the reporting date.
- Overdue supplier payments scheduled on the reporting date.
- Future collections and payments scheduled on their due dates.
- Daily incoming and outgoing cash flow.
- Daily net cash flow calculation.
- Projected cash balance.
- Cash shortage detection.

## Business Insights
- Expected customer collections exceed supplier payments.
- Net projected cash flow is positive by €8,250.
- No negative projected cash balance occurs in the forecast period.

## Assumptions
- Opening cash is a synthetic demo balance of €20,000.
- All unpaid customer invoices are assumed to be collected on their due dates.
- All unpaid supplier invoices are assumed to be paid on their due dates.
- Overdue invoices are scheduled on 27 October 2026.
- Forecast period: 27 October to 26 November 2026.

## Limitations
This is a simplified scenario-based forecast, not a complete cash flow statement. It excludes payroll, rent, taxes, operating expenses, financing and uncertain collection delays.

## Technical Skills
- Python
- Pandas
- SQLite
- Financial data integration
- Cash flow forecasting
- Date-based aggregation
- Business analytics
EOF
```
