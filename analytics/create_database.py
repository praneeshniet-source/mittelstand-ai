from analytics.database import fetch_dataframe


def verify_database():
    supplier_count = fetch_dataframe(
        "SELECT COUNT(*) AS total FROM invoices"
    ).iloc[0]["total"]

    customer_count = fetch_dataframe(
        "SELECT COUNT(*) AS total FROM customer_invoices"
    ).iloc[0]["total"]

    print("PostgreSQL database verified successfully!")
    print(f"Supplier invoices: {supplier_count}")
    print(f"Customer invoices: {customer_count}")


if __name__ == "__main__":
    verify_database()
