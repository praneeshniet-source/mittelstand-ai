import csv
from pathlib import Path

from analytics.database import get_connection


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SUPPLIER_CSV = PROJECT_ROOT / "data" / "raw" / "invoices.csv"
CUSTOMER_CSV = PROJECT_ROOT / "data" / "raw" / "customer_invoices.csv"


SUPPLIER_COLUMNS = {
    "invoice_id", "supplier", "country", "category",
    "invoice_date", "due_date", "amount_eur", "status"
}

CUSTOMER_COLUMNS = {
    "invoice_id", "customer", "country", "category",
    "invoice_date", "due_date", "amount_eur", "status",
    "payment_date"
}


def read_csv(path, required_columns):
    """Read and validate a CSV file."""

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)

        headers = next(
            (row for row in reader if any(cell.strip() for cell in row)),
            None
        )

        if headers is None:
            raise ValueError(f"CSV file is empty: {path}")

        headers = [header.strip() for header in headers]

        if len(headers) != len(set(headers)):
            raise ValueError(f"Duplicate column names in {path}")

        missing_columns = required_columns - set(headers)

        if missing_columns:
            raise ValueError(
                f"{path.name} is missing columns: "
                f"{sorted(missing_columns)}"
            )

        rows = []

        for line_number, row in enumerate(reader, start=2):
            if not any(cell.strip() for cell in row):
                continue

            if len(row) != len(headers):
                raise ValueError(
                    f"Invalid number of fields in {path.name}, "
                    f"line {line_number}: expected {len(headers)}, "
                    f"received {len(row)}"
                )

            rows.append({
                header: value.strip()
                for header, value in zip(headers, row)
            })

    if not rows:
        raise ValueError(f"No invoice records found in {path}")

    return rows


def import_data():
    """Import supplier and customer invoices safely."""

    supplier_rows = read_csv(SUPPLIER_CSV, SUPPLIER_COLUMNS)
    customer_rows = read_csv(CUSTOMER_CSV, CUSTOMER_COLUMNS)

    # Validate essential fields before database insertion
    for table_name, rows, entity_column in [
        ("supplier invoices", supplier_rows, "supplier"),
        ("customer invoices", customer_rows, "customer"),
    ]:
        required_values = [
            "invoice_id", entity_column,
            "invoice_date", "due_date", "amount_eur", "status"
        ]

        for index, row in enumerate(rows, start=2):
            for column in required_values:
                if not row.get(column):
                    raise ValueError(
                        f"Missing {column} in {table_name}, "
                        f"CSV data row {index}"
                    )

    supplier_data = [
        (
            row["invoice_id"],
            row["supplier"],
            row["country"] or None,
            row["category"] or None,
            row["invoice_date"],
            row["due_date"],
            row["amount_eur"],
            row["status"],
        )
        for row in supplier_rows
    ]

    customer_data = [
        (
            row["invoice_id"],
            row["customer"],
            row["country"] or None,
            row["category"] or None,
            row["invoice_date"],
            row["due_date"],
            row["amount_eur"],
            row["status"],
            row["payment_date"] or None,
        )
        for row in customer_rows
    ]

    # Both imports run in one transaction.
    # Existing invoice IDs are skipped safely.
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.executemany(
                """
                INSERT INTO invoices (
                    invoice_id, supplier, country, category,
                    invoice_date, due_date, amount_eur, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (invoice_id) DO NOTHING
                """,
                supplier_data,
            )

            supplier_inserted = cur.rowcount

            cur.executemany(
                """
                INSERT INTO customer_invoices (
                    invoice_id, customer, country, category,
                    invoice_date, due_date, amount_eur, status,
                    payment_date
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (invoice_id) DO NOTHING
                """,
                customer_data,
            )

            customer_inserted = cur.rowcount

            cur.execute("SELECT COUNT(*) FROM invoices")
            supplier_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM customer_invoices")
            customer_count = cur.fetchone()[0]

            cur.execute(
                """
                SELECT COUNT(*)
                FROM customer_invoices
                WHERE payment_date IS NULL
                """
            )
            missing_payment_dates = cur.fetchone()[0]

    print("PostgreSQL import completed successfully!")
    print(f"New supplier invoices inserted: {supplier_inserted}")
    print(f"New customer invoices inserted: {customer_inserted}")
    print(f"Total supplier invoices: {supplier_count}")
    print(f"Total customer invoices: {customer_count}")
    print(f"Missing payment dates: {missing_payment_dates}")


if __name__ == "__main__":
    import_data()
