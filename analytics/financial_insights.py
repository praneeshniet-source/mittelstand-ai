
import sqlite3
import pandas as pd


# STEP 1: Retrieve invoice data
def get_invoice_data():

    conn = sqlite3.connect("mittelstand.db")

    try:
        invoices = pd.read_sql_query(
            "SELECT * FROM invoices",
            conn
        )
        return invoices

    finally:
        conn.close()


# STEP 2: Calculate supplier financial exposure
def calculate_supplier_exposure(invoices):

    unpaid_invoices = invoices[
        invoices["status"].str.strip().str.lower() == "unpaid"
    ]

    supplier_exposure = (
        unpaid_invoices
        .groupby("supplier")["amount_eur"]
        .sum()
        .reset_index()
    )

    return supplier_exposure.sort_values(
        by="amount_eur",
        ascending=False
    )


# STEP 3: Calculate overdue supplier exposure
def calculate_overdue_exposure(invoices):

    reporting_date = pd.Timestamp("2026-10-27")
    invoice_data = invoices.copy()

    invoice_data["due_date"] = pd.to_datetime(
        invoice_data["due_date"],
        errors="coerce"
    )

    overdue_invoices = invoice_data[
        (invoice_data["status"].str.strip().str.lower() == "unpaid") &
        (invoice_data["due_date"] < reporting_date)
    ]

    overdue_exposure = (
        overdue_invoices
        .groupby("supplier")["amount_eur"]
        .sum()
        .reset_index()
    )

    return overdue_exposure.sort_values(
        by="amount_eur",
        ascending=False
    )


# STEP 4: Calculate supplier risk
def calculate_supplier_risk(invoices):

    reporting_date = pd.Timestamp("2026-10-27")
    invoice_data = invoices.copy()

    invoice_data["due_date"] = pd.to_datetime(
        invoice_data["due_date"],
        errors="coerce"
    )

    unpaid = invoice_data[
        invoice_data["status"].str.strip().str.lower() == "unpaid"
    ].copy()

    unpaid["days_overdue"] = (
        reporting_date - unpaid["due_date"]
    ).dt.days

    overdue = unpaid[unpaid["days_overdue"] > 0].copy()

    unpaid_exposure = (
        unpaid.groupby("supplier")["amount_eur"]
        .sum()
        .rename("unpaid_exposure")
    )

    overdue_exposure = (
        overdue.groupby("supplier")["amount_eur"]
        .sum()
        .rename("overdue_exposure")
    )

    overdue_count = (
        overdue.groupby("supplier")["invoice_id"]
        .count()
        .rename("overdue_invoice_count")
    )

    max_overdue_days = (
        overdue.groupby("supplier")["days_overdue"]
        .max()
        .rename("max_days_overdue")
    )

    risk = pd.concat(
        [
            unpaid_exposure,
            overdue_exposure,
            overdue_count,
            max_overdue_days
        ],
        axis=1
    ).fillna(0).reset_index()

    def calculate_score(row):

        score = 0

        if row["overdue_exposure"] > 1000:
            score += 30
        elif row["overdue_exposure"] > 500:
            score += 20

        if row["overdue_invoice_count"] >= 2:
            score += 20

        if row["max_days_overdue"] > 30:
            score += 30
        elif row["max_days_overdue"] >= 15:
            score += 20

        if row["unpaid_exposure"] > 3000:
            score += 20

        return score

    risk["risk_score"] = risk.apply(
        calculate_score,
        axis=1
    )

    def classify_risk(score):

        if score >= 50:
            return "High"
        elif score >= 25:
            return "Medium"
        else:
            return "Low"

    risk["risk_level"] = risk["risk_score"].apply(
        classify_risk
    )

    return risk.sort_values(
        by="risk_score",
        ascending=False
    )


# STEP 5: Generate supplier recommendations
def generate_supplier_recommendations(risk_results):

    recommendations = []

    for _, supplier in risk_results.iterrows():

        risk_level = supplier["risk_level"]
        overdue_amount = supplier["overdue_exposure"]
        unpaid_amount = supplier["unpaid_exposure"]
        overdue_count = supplier["overdue_invoice_count"]
        overdue_days = supplier["max_days_overdue"]

        if overdue_amount > 0:

            if overdue_days > 30:
                action = (
                    "Urgently contact the supplier's accounts "
                    "payable team and resolve long-overdue invoices."
                )

            elif overdue_days >= 15:
                action = (
                    "Follow up with the supplier and request "
                    "a confirmed payment settlement date."
                )

            else:
                action = (
                    "Send a payment reminder and monitor "
                    "the upcoming settlement."
                )

        elif unpaid_amount > 0:
            action = (
                "Monitor outstanding invoices and confirm "
                "that payments are scheduled before their due dates."
            )

        else:
            action = "No outstanding payment action required."

        if risk_level == "High":
            priority = "Immediate attention"
        elif risk_level == "Medium":
            priority = "Follow-up required"
        else:
            priority = "Routine monitoring"

        recommendations.append({
            "supplier": supplier["supplier"],
            "risk_level": risk_level,
            "priority": priority,
            "overdue_amount": overdue_amount,
            "unpaid_amount": unpaid_amount,
            "overdue_invoice_count": int(overdue_count),
            "recommended_action": action
        })

    return pd.DataFrame(recommendations)


# STEP 6: Generate financial executive summary
def generate_financial_summary(invoices, risk_results):

    total_invoices = len(invoices)

    unpaid = invoices[
        invoices["status"].str.strip().str.lower() == "unpaid"
    ]

    paid = invoices[
        invoices["status"].str.strip().str.lower() == "paid"
    ]

    total_unpaid = unpaid["amount_eur"].sum()
    total_paid = paid["amount_eur"].sum()

    reporting_date = pd.Timestamp("2026-10-27")
    invoice_data = invoices.copy()

    invoice_data["due_date"] = pd.to_datetime(
        invoice_data["due_date"],
        errors="coerce"
    )

    overdue = invoice_data[
        (invoice_data["status"].str.strip().str.lower() == "unpaid") &
        (invoice_data["due_date"] < reporting_date)
    ]

    total_overdue = overdue["amount_eur"].sum()
    overdue_count = len(overdue)

    print("\nFINANCIAL INTELLIGENCE EXECUTIVE SUMMARY")
    print("----------------------------------------")

    print(f"Total invoices analysed: {total_invoices}")
    print(f"Total paid amount: €{total_paid:,.2f}")
    print(f"Total unpaid amount: €{total_unpaid:,.2f}")
    print(f"Total overdue amount: €{total_overdue:,.2f}")
    print(f"Number of overdue invoices: {overdue_count}")

    if not risk_results.empty:

        highest_risk_supplier = risk_results.iloc[0]

        high_risk_count = len(
            risk_results[risk_results["risk_level"] == "High"]
        )

        print(
            f"\nHighest risk supplier: "
            f"{highest_risk_supplier['supplier']}"
        )

        print(
            f"Supplier risk score: "
            f"{highest_risk_supplier['risk_score']}"
        )

        print(f"High-risk suppliers: {high_risk_count}")

        print("\nBUSINESS INSIGHTS")
        print("-----------------")

        if total_overdue > 0:
            print(
                f"URGENT: €{total_overdue:,.2f} in supplier "
                f"payments are overdue."
            )

        print(
            f"PRIORITY: Review outstanding payments to "
            f"{highest_risk_supplier['supplier']}."
        )

        print(
            "RECOMMENDATION: Follow up on overdue invoices "
            "and monitor upcoming payment deadlines."
        )


# MAIN PROGRAM
if __name__ == "__main__":

    invoices = get_invoice_data()

    print("\nFINANCIAL INTELLIGENCE ENGINE")
    print("-----------------------------")

    print("Total invoices:", len(invoices))

    print("\nInvoice data:")
    print(invoices.to_string(index=False))

    # Supplier financial exposure
    print("\nSUPPLIER FINANCIAL EXPOSURE")
    print("---------------------------")

    exposure = calculate_supplier_exposure(invoices)
    print(exposure.to_string(index=False))

    # Overdue supplier exposure
    print("\nOVERDUE SUPPLIER EXPOSURE")
    print("-------------------------")

    overdue = calculate_overdue_exposure(invoices)
    print(overdue.to_string(index=False))

    # Supplier risk assessment
    print("\nSUPPLIER RISK ASSESSMENT")
    print("------------------------")

    risk_results = calculate_supplier_risk(invoices)
    print(risk_results.to_string(index=False))

    # Supplier recommendations
    print("\nSUPPLIER BUSINESS RECOMMENDATIONS")
    print("---------------------------------")

    recommendations = generate_supplier_recommendations(
        risk_results
    )

    print(recommendations.to_string(index=False))

    # Financial executive summary
    generate_financial_summary(
        invoices,
        risk_results
    )

    print("\nFINANCIAL ANALYSIS COMPLETED")
