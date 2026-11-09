
import pandas as pd
from analytics.anomaly_detector import detect_anomalies


test_data = pd.DataFrame([
    {
        "invoice_id": "TEST001",
        "supplier": "Test Supplier",
        "amount_eur": -100,
        "invoice_date": "2026-10-01",
        "due_date": "2026-10-15"
    },
    {
        "invoice_id": "TEST002",
        "supplier": "Test Supplier",
        "amount_eur": 6500,
        "invoice_date": "2026-10-01",
        "due_date": "2026-10-15"
    },
    {
        "invoice_id": "TEST003",
        "supplier": "Test Supplier",
        "amount_eur": 1000,
        "invoice_date": "2026-10-20",
        "due_date": "2026-10-10"
    }
])

results = detect_anomalies(test_data)

print("\nANOMALY DETECTION TEST RESULTS")
print(results.to_string(index=False))
