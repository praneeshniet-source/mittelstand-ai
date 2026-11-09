# Day 8 — Supplier Risk Scoring

## 1. Objective

Develop a rule-based supplier risk scoring system to help finance teams identify suppliers with significant overdue payment exposure and prioritise payment follow-ups.

## 2. Business Problem

Small and medium-sized businesses often manage multiple supplier invoices. Without a clear risk assessment, finance teams may struggle to identify which suppliers require immediate attention.

Mittelstand AI addresses this by analysing unpaid and overdue invoice data and assigning an understandable risk score to each supplier.

## 3. Data Used

The risk assessment uses the following invoice metrics:

- Unpaid invoice count
- Total unpaid amount
- Overdue invoice count
- Total overdue amount
- Overdue percentage of unpaid exposure

## 4. Risk Scoring Methodology

The system calculates a score between 0 and 100.

**Formula:**

Risk Score = (Overdue Percentage × 0.5) + (Overdue Invoice Count × 10)

Where:

- Overdue percentage is calculated as overdue value divided by unpaid value, multiplied by 100.
- Overdue percentage contribution is capped at 50 points.
- Overdue invoice count contribution is capped at 50 points.

## 5. Risk Classification

| Risk Score | Classification |
|---|---|
| 0–29.9 | Low Risk |
| 30–69.9 | Medium Risk |
| 70–100 | High Risk |

## 6. Dashboard Features

1. Supplier-level risk score calculation.
2. Automatic risk classification.
3. Supplier risk distribution chart.
4. Identification of the highest-risk supplier.
5. Recommended actions based on risk level.
6. Supplier action plan table.

## 7. Recommended Actions

- **High Risk:** Contact the supplier and review the payment position urgently.
- **Medium Risk:** Monitor the supplier closely and plan upcoming payments.
- **Low Risk:** Continue regular payment monitoring.

## 8. Business Value

- Improves visibility into supplier payment exposure.
- Helps finance teams prioritise overdue payments.
- Identifies suppliers requiring attention.
- Supports working-capital monitoring.
- Makes invoice data easier to interpret.

## 9. Limitations

- The scoring model is rule-based, not a statistically validated predictive model.
- Risk scores depend on invoice data quality.
- A small number of invoices may not represent long-term supplier behaviour.
- The project currently uses synthetic demonstration data.

## 10. Technology Used

- Python
- Pandas
- Streamlit
- SQLite
- Rule-based analytics

## 11. Outcome

Implemented an interactive supplier risk assessment module within Mittelstand AI, transforming invoice payment data into supplier-level risk indicators and recommended actions.