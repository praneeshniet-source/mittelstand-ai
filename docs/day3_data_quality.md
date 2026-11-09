# Day 3 — Data Quality Checks

## Dataset
- Total invoices: 10
- Database: SQLite
- Table: invoices

## Checks Performed
1. Missing supplier names
2. Missing invoice amounts
3. Missing due dates
4. Duplicate invoice IDs
5. Zero or negative invoice amounts
6. Due dates earlier than invoice dates

## Results
- Missing supplier names: 0
- Missing invoice amounts: 0
- Missing due dates: 0
- Duplicate invoice IDs: None found, assuming the query returned no rows
- Invalid invoice amounts: None found, assuming the query returned no rows
- Invalid invoice date order: None found, assuming the query returned no rows

## Business Value
Data-quality checks help prevent inaccurate financial reports
and improve confidence in business decisions.

## Next Steps
- Automate these checks using Python
- Add more validation rules
- Generate a data-quality summary
