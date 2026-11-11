from psycopg.errors import UniqueViolation

from analytics.database import get_connection


def _check_duplicate_invoice(cur, details):
    """Check for exact and potential duplicate invoices."""

    cur.execute(
        """
        SELECT invoice_id
        FROM invoices
        WHERE invoice_id = %s
        """,
        (details["invoice_number"],),
    )

    if cur.fetchone():
        return "DUPLICATE"

    cur.execute(
        """
        SELECT invoice_id
        FROM invoices
        WHERE LOWER(TRIM(supplier)) = LOWER(TRIM(%s))
          AND invoice_date = %s
          AND amount_eur = %s
        LIMIT 1
        """,
        (
            details["supplier"],
            details["invoice_date"],
            details["amount"],
        ),
    )

    if cur.fetchone():
        return "POTENTIAL_DUPLICATE"

    return "UNIQUE"


def check_duplicate_invoice(details):
    """Check whether an invoice already exists in PostgreSQL."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            return _check_duplicate_invoice(cur, details)


def save_invoice(
    details,
    country="Unknown",
    category="Unclassified",
    status="Unpaid",
):
    """Save a validated invoice to PostgreSQL."""

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                duplicate_status = _check_duplicate_invoice(cur, details)

                if duplicate_status != "UNIQUE":
                    return duplicate_status

                cur.execute(
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
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        details["invoice_number"],
                        details["supplier"],
                        country,
                        category,
                        details["invoice_date"],
                        details["due_date"],
                        details["amount"],
                        status,
                    ),
                )

        return "SAVED"

    except UniqueViolation:
        return "DUPLICATE"
