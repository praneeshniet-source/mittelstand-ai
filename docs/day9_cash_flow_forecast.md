# Day 9 — Cash Flow Forecasting

## Objective
Build a 30-day supplier payment forecast to help a small business understand its expected outgoing payments and projected cash balance.

## Features Implemented
- Synthetic opening cash balance of €20,000.
- Identification of unpaid supplier invoices.
- Overdue invoices scheduled for payment on the forecast start date.
- Future unpaid invoices scheduled on their respective due dates.
- Daily expected supplier payment calculation.
- Projected daily cash balance.
- Opening cash, expected payments and projected closing cash KPIs.
- Daily cash balance line chart.
- Upcoming supplier payment schedule.
- Cash shortage warning.
- Downloadable cash flow forecast CSV.

## Forecast Assumptions
- Reporting date: 27 October 2026.
- Forecast horizon: 27 October to 26 November 2026.
- Opening cash balance: €20,000 (synthetic demo value).
- Overdue unpaid invoices are assumed to be paid on 27 October 2026.
- Other unpaid invoices are assumed to be paid on their due dates.
- Already-paid invoices are excluded.
- No customer receipts or other operating expenses are included.

## Current Dataset Results
- Opening cash: €20,000.
- Total unpaid supplier obligations: €11,750.
- Expected supplier payments: €11,750.
- Projected closing cash: €8,250.

## Limitations
This is an outgoing supplier payment forecast, not a complete business cash flow statement. It does not include customer collections, payroll, rent, taxes, financing or other operating expenses.

The opening cash balance is synthetic and is used only for demonstration.

## Business Value
The forecast helps business owners anticipate upcoming supplier payments, monitor their projected cash position and identify potential cash shortages before they occur.

## Technical Implementation
- Python
- Pandas
- Streamlit
- SQLite
- Matplotlib / Streamlit charting
