
import sqlite3
import pandas as pd


def detect_anomalies(invoices):

    anomalies = []

    # Rule 1: Invalid invoice amounts
    for _, invoice in invoices.iterrows():

        if invoice["amount_eur"] <= 0:

            anomalies.append({
                "invoice_id": invoice["invoice_id"],
                "supplier": invoice["supplier"],
                "amount_eur": invoice["amount_eur"],
                "anomaly": "Invalid invoice amount",
                "severity": "High"
            })

        # Rule 2: Unusually high invoice amount
        if invoice["amount_eur"] > 5000:

            anomalies.append({
                "invoice_id": invoice["invoice_id"],
                "supplier": invoice["supplier"],
                "amount_eur": invoice["amount_eur"],
                "anomaly": "Unusually high invoice amount",
                "severity": "High"
            })

    # Rule 3: Invalid invoice dates
    invoice_dates = pd.to_datetime(
        invoices["invoice_date"], errors="coerce"
    )

    due_dates = pd.to_datetime(
        invoices["due_date"], errors="coerce"
    )

    invalid_dates = (
        (due_dates < invoice_dates) |
        invoice_dates.isna() |
        due_dates.isna()
    )

    for index in invoices[invalid_dates].index:

        invoice = invoices.loc[index]

        anomalies.append({
            "invoice_id": invoice["invoice_id"],
            "supplier": invoice["supplier"],
            "amount_eur": invoice["amount_eur"],
            "anomaly": "Invalid or inconsistent invoice dates",
            "severity": "High"
        })

    return pd.DataFrame(anomalies)


# Read invoices from SQLite and run anomaly detection
def detect_invoice_anomalies():

    conn = sqlite3.connect("mittelstand.db")

    try:
        invoices = pd.read_sql_query(
            "SELECT * FROM invoices",
            conn
        )

    finally:
        conn.close()

    return detect_anomalies(invoices)


# Run detector directly
if __name__ == "__main__":

    results = detect_invoice_anomalies()

    print("\nINVOICE ANOMALY DETECTION RESULTS")

    if results.empty:
        print("No anomalies detected.")
    else:
        print(results.to_string(index=False))
