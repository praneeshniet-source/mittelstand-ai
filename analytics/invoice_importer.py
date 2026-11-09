
import sqlite3


def check_duplicate_invoice(details):

    conn = sqlite3.connect("mittelstand.db")

    try:
        # Check exact invoice ID
        exact_match = conn.execute(
            """
            SELECT invoice_id
            FROM invoices
            WHERE invoice_id = ?
            """,
            (details["invoice_number"],)
        ).fetchone()

        if exact_match:
            return "DUPLICATE"

        # Check potential duplicate
        potential_match = conn.execute(
            """
            SELECT invoice_id
            FROM invoices
            WHERE LOWER(TRIM(supplier)) = LOWER(TRIM(?))
            AND invoice_date = ?
            AND amount_eur = ?
            LIMIT 1
            """,
            (
                details["supplier"],
                details["invoice_date"],
                details["amount"]
            )
        ).fetchone()

        if potential_match:
            return "POTENTIAL_DUPLICATE"

        return "UNIQUE"

    finally:
        conn.close()

def save_invoice(details, country="Unknown",
                 category="Unclassified", status="Unpaid"):

    duplicate_status = check_duplicate_invoice(details)

    if duplicate_status != "UNIQUE":
        return duplicate_status

    conn = sqlite3.connect("mittelstand.db")

    try:
        conn.execute(
            """
            INSERT INTO invoices (
                invoice_id,
                supplier,
                country,
                category,
                invoice_date,
                due_date,
                amount_eur,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                details["invoice_number"],
                details["supplier"],
                country,
                category,
                details["invoice_date"],
                details["due_date"],
                details["amount"],
                status
            )
        )

        conn.commit()
        return "SAVED"

    finally:
        conn.close()
