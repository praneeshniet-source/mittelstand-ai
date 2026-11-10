import sqlite3
from pathlib import Path

import pandas as pd

from analytics.ollama_client import ask_ollama
from analytics.financial_context import get_financial_context

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "mittelstand.db"
DEFAULT_REPORTING_DATE = pd.Timestamp("2026-10-27")


def get_supplier_names():
    """Return supplier names currently present in the SQLite invoice table."""
    if not DATABASE_PATH.exists():
        return []
    with sqlite3.connect(DATABASE_PATH) as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT TRIM(supplier)
            FROM invoices
            WHERE supplier IS NOT NULL AND TRIM(supplier) <> ''
            ORDER BY TRIM(supplier)
            """
        ).fetchall()
    return [row[0] for row in rows]


def find_supplier_in_question(question):
    """Match a supplier mentioned in the question to a database supplier."""
    q = question.casefold()
    matches = [name for name in get_supplier_names() if name.casefold() in q]
    return max(matches, key=len) if matches else None


def get_supplier_metrics(supplier, reporting_date=DEFAULT_REPORTING_DATE):
    """Calculate verified unpaid, overdue and not-yet-due supplier balances."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    with sqlite3.connect(DATABASE_PATH) as conn:
        data = pd.read_sql_query(
            """
            SELECT invoice_id, supplier, due_date, amount_eur, status
            FROM invoices
            WHERE TRIM(supplier) = TRIM(?)
            """,
            conn,
            params=(supplier,),
        )

    if data.empty:
        return None

    data["amount_eur"] = pd.to_numeric(data["amount_eur"], errors="coerce")
    data["due_date"] = pd.to_datetime(data["due_date"], errors="coerce")
    data["status"] = data["status"].astype(str).str.strip().str.title()
    data = data.dropna(subset=["amount_eur", "due_date"])

    unpaid = data[data["status"] == "Unpaid"]
    report_date = pd.Timestamp(reporting_date).normalize()
    overdue = unpaid[unpaid["due_date"] < report_date]
    not_yet_due = unpaid[unpaid["due_date"] >= report_date]

    return {
        "supplier": supplier,
        "invoice_count": int(len(data)),
        "unpaid_invoice_count": int(len(unpaid)),
        "overdue_invoice_count": int(len(overdue)),
        "unpaid": float(unpaid["amount_eur"].sum()),
        "overdue": float(overdue["amount_eur"].sum()),
        "not_due": float(not_yet_due["amount_eur"].sum()),
        "reporting_date": report_date.date().isoformat(),
    }


def get_portfolio_metrics(reporting_date=DEFAULT_REPORTING_DATE):
    """Calculate portfolio totals directly from the supplier invoice database."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    with sqlite3.connect(DATABASE_PATH) as conn:
        data = pd.read_sql_query(
            "SELECT amount_eur, due_date, status FROM invoices", conn
        )

    if data.empty:
        return None

    data["amount_eur"] = pd.to_numeric(data["amount_eur"], errors="coerce")
    data["due_date"] = pd.to_datetime(data["due_date"], errors="coerce")
    data["status"] = data["status"].astype(str).str.strip().str.title()
    data = data.dropna(subset=["amount_eur", "due_date"])

    unpaid = data[data["status"] == "Unpaid"]
    report_date = pd.Timestamp(reporting_date).normalize()
    overdue = unpaid[unpaid["due_date"] < report_date]
    not_yet_due = unpaid[unpaid["due_date"] >= report_date]

    return {
        "invoice_count": int(len(data)),
        "total_value": float(data["amount_eur"].sum()),
        "paid": float(data.loc[data["status"] == "Paid", "amount_eur"].sum()),
        "unpaid": float(unpaid["amount_eur"].sum()),
        "overdue": float(overdue["amount_eur"].sum()),
        "not_due": float(not_yet_due["amount_eur"].sum()),
        "overdue_invoice_count": int(len(overdue)),
        "not_due_invoice_count": int(len(not_yet_due)),
    }


def _format_supplier_answer(metrics, question):
    """Format common supplier questions from verified calculated metrics."""
    q = question.casefold()
    name = metrics["supplier"]

    if any(word in q for word in ("why", "attention", "risk", "priority")):
        if metrics["overdue"] > 0:
            opening = (
                f"{name} requires payment attention because our business has "
                f"€{metrics['overdue']:,.2f} in overdue supplier invoices. "
            )
        else:
            opening = (
                f"{name} has no overdue supplier balance as of "
                f"{metrics['reporting_date']}. "
            )
        return (
            opening
            + f"Total unpaid exposure is €{metrics['unpaid']:,.2f}, of which "
            + f"€{metrics['not_due']:,.2f} is not yet due. "
            + "Review the underlying invoices and payment schedule before "
              "taking action."
        )

    if "overdue" in q:
        return (
            f"{name} has €{metrics['overdue']:,.2f} in overdue supplier "
            f"invoices across {metrics['overdue_invoice_count']} invoice(s), "
            f"as of {metrics['reporting_date']}."
        )

    if any(term in q for term in ("not yet due", "not overdue", "upcoming", "due later")):
        return (
            f"{name} has €{metrics['not_due']:,.2f} in unpaid invoices that "
            f"are not yet due, as of {metrics['reporting_date']}."
        )

    return (
        f"{name} has €{metrics['unpaid']:,.2f} in total unpaid supplier "
        f"exposure: €{metrics['overdue']:,.2f} overdue and "
        f"€{metrics['not_due']:,.2f} not yet due, as of "
        f"{metrics['reporting_date']}."
    )




def _answer_portfolio_question(question, metrics):
    """Answer common portfolio questions with calculated values."""
    q = question.casefold()

    # 1. Highest unpaid supplier
    if any(term in q for term in (
        "highest unpaid",
        "largest unpaid",
        "most unpaid",
    )):
        with sqlite3.connect(DATABASE_PATH) as conn:
            row = conn.execute(
                """
                SELECT TRIM(supplier) AS supplier,
                       SUM(amount_eur) AS unpaid
                FROM invoices
                WHERE LOWER(TRIM(status)) = 'unpaid'
                  AND supplier IS NOT NULL
                  AND TRIM(supplier) <> ''
                GROUP BY TRIM(supplier)
                ORDER BY unpaid DESC
                LIMIT 1
                """
            ).fetchone()

        if row and row[0] is not None:
            return (
                f"{row[0]} has the highest unpaid supplier exposure "
                f"at €{float(row[1]):,.2f}."
            )

    # 2. Unpaid invoices that are not yet due
    if any(term in q for term in (
        "not yet due",
        "not overdue",
        "unpaid but not overdue",
        "unpaid but not yet due",
    )):
        return (
            f"Unpaid supplier invoices that are not yet due total "
            f"€{metrics['not_due']:,.2f} across "
            f"{metrics['not_due_invoice_count']} invoice(s)."
        )

    # 3. Highest overdue supplier
    if any(term in q for term in (
        "highest overdue",
        "largest overdue",
        "most overdue",
    )):
        with sqlite3.connect(DATABASE_PATH) as conn:
            row = conn.execute(
                """
                SELECT TRIM(supplier) AS supplier,
                       SUM(amount_eur) AS overdue
                FROM invoices
                WHERE LOWER(TRIM(status)) = 'unpaid'
                  AND date(due_date) < date(?)
                  AND supplier IS NOT NULL
                  AND TRIM(supplier) <> ''
                GROUP BY TRIM(supplier)
                ORDER BY overdue DESC
                LIMIT 1
                """,
                (DEFAULT_REPORTING_DATE.strftime("%Y-%m-%d"),),
            ).fetchone()

        if row and row[0] is not None:
            return (
                f"{row[0]} has the highest overdue supplier exposure "
                f"at €{float(row[1]):,.2f}."
            )

    # 4. Total overdue supplier exposure
    if "overdue" in q:
        return (
            f"Total overdue supplier exposure is "
            f"€{metrics['overdue']:,.2f} across "
            f"{metrics['overdue_invoice_count']} invoice(s)."
        )

    # 5. Total unpaid supplier exposure
    if "unpaid" in q or "outstanding" in q:
        return (
            f"Total unpaid supplier exposure is "
            f"€{metrics['unpaid']:,.2f}."
        )

    # 6. Total paid supplier invoice value
    if "paid" in q:
        return (
            f"Total paid supplier invoice value is "
            f"€{metrics['paid']:,.2f}."
        )

    # 7. Total invoice value
    if "total" in q and "invoice" in q:
        return (
            f"Total supplier invoice value is "
            f"€{metrics['total_value']:,.2f} "
            f"across {metrics['invoice_count']} invoices."
        )

    return None


def get_customer_names():
    """Return customer names currently present in the customer invoice CSV."""
    customer_path = PROJECT_ROOT / "data" / "raw" / "customer_invoices.csv"
    if not customer_path.exists():
        return []
    data = pd.read_csv(customer_path, usecols=["customer"])
    return sorted(
        data["customer"].dropna().astype(str).str.strip().unique().tolist()
    )


def find_customer_in_question(question):
    """Match a customer mentioned in the question to the CSV dataset."""
    q = question.casefold()
    matches = [name for name in get_customer_names() if name.casefold() in q]
    return max(matches, key=len) if matches else None


def get_customer_metrics(customer=None, reporting_date=DEFAULT_REPORTING_DATE):
    """Calculate verified customer receivables from customer_invoices.csv."""
    customer_path = PROJECT_ROOT / "data" / "raw" / "customer_invoices.csv"
    if not customer_path.exists():
        raise FileNotFoundError(
            f"Customer invoice file not found: {customer_path}"
        )

    data = pd.read_csv(customer_path)
    required = {
        "invoice_id", "customer", "due_date", "amount_eur", "status",
        "payment_date"
    }
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(
            f"Customer invoice file is missing required columns: {sorted(missing)}"
        )

    data["customer"] = data["customer"].astype(str).str.strip()
    data["status"] = data["status"].astype(str).str.strip().str.title()
    data["amount_eur"] = pd.to_numeric(data["amount_eur"], errors="coerce")
    data["due_date"] = pd.to_datetime(data["due_date"], errors="coerce")
    data["payment_date"] = pd.to_datetime(data["payment_date"], errors="coerce")
    data = data.dropna(subset=["customer", "amount_eur", "due_date"])

    if customer is not None:
        data = data[data["customer"].str.casefold() == customer.casefold()]

    if data.empty:
        return None

    report_date = pd.Timestamp(reporting_date).normalize()
    unpaid = data[data["status"] == "Unpaid"]
    paid = data[data["status"] == "Paid"]
    overdue = unpaid[unpaid["due_date"] < report_date]
    not_yet_due = unpaid[unpaid["due_date"] >= report_date]

    delay_days = (paid["payment_date"] - paid["due_date"]).dt.days.dropna()

    return {
        "customer": customer,
        "invoice_count": int(len(data)),
        "paid_invoice_count": int(len(paid)),
        "unpaid_invoice_count": int(len(unpaid)),
        "overdue_invoice_count": int(len(overdue)),
        "total_invoiced": float(data["amount_eur"].sum()),
        "collected": float(paid["amount_eur"].sum()),
        "outstanding": float(unpaid["amount_eur"].sum()),
        "overdue": float(overdue["amount_eur"].sum()),
        "not_due": float(not_yet_due["amount_eur"].sum()),
        "average_payment_delay_days": (
            float(delay_days.mean()) if not delay_days.empty else None
        ),
        "reporting_date": report_date.date().isoformat(),
    }


def _format_customer_answer(metrics, question):
    """Format common customer questions using verified receivables metrics."""
    q = question.casefold()
    name = metrics["customer"]

    if any(term in q for term in ("overdue", "late", "past due")):
        return (
            f"{name} has €{metrics['overdue']:,.2f} in overdue customer "
            f"receivables across {metrics['overdue_invoice_count']} invoice(s), "
            f"as of {metrics['reporting_date']}."
        )

    if any(term in q for term in (
        "not yet due", "not overdue", "due later", "upcoming"
    )):
        return (
            f"{name} has €{metrics['not_due']:,.2f} in outstanding customer "
            f"invoices that are not yet due, as of {metrics['reporting_date']}."
        )

    if any(term in q for term in ("paid", "collected", "received")):
        return (
            f"Our business has collected €{metrics['collected']:,.2f} "
            f"from {name} across {metrics['paid_invoice_count']} paid invoice(s)."
        )

    return (
        f"{name} has €{metrics['outstanding']:,.2f} outstanding to our business: "
        f"€{metrics['overdue']:,.2f} overdue and "
        f"€{metrics['not_due']:,.2f} not yet due, as of "
        f"{metrics['reporting_date']}."
    )


def _answer_customer_portfolio_question(question):
    """Answer portfolio-level customer receivables questions."""
    q = question.casefold()

    # Avoid intercepting generic supplier questions such as "unpaid but not overdue".
    customer_intent = any(term in q for term in (
        "customer", "receivable", "collected", "amount collected",
        "owe us", "owed to us", "customer invoice", "customers"
    ))
    if not customer_intent:
        return None

    metrics = get_customer_metrics()
    if metrics is None:
        return "No customer invoice records were found."

    if any(term in q for term in (
        "highest outstanding", "largest outstanding", "owes us the most",
        "highest receivable", "largest receivable"
    )):
        customer_path = PROJECT_ROOT / "data" / "raw" / "customer_invoices.csv"
        data = pd.read_csv(customer_path)
        data["amount_eur"] = pd.to_numeric(data["amount_eur"], errors="coerce")
        data["status"] = data["status"].astype(str).str.strip().str.title()
        unpaid = data[data["status"] == "Unpaid"]
        exposure = unpaid.groupby("customer")["amount_eur"].sum().sort_values(
            ascending=False
        )
        if not exposure.empty:
            return (
                f"{exposure.index[0]} has the highest outstanding customer "
                f"receivable at €{exposure.iloc[0]:,.2f}."
            )

    if any(term in q for term in ("overdue", "past due", "late payment")):
        return (
            f"Total overdue customer receivables are €{metrics['overdue']:,.2f} "
            f"across {metrics['overdue_invoice_count']} invoice(s)."
        )

    if any(term in q for term in (
        "not yet due", "not overdue", "unpaid but not overdue"
    )):
        return (
            f"Outstanding customer invoices that are not yet due total "
            f"€{metrics['not_due']:,.2f} across "
            f"{metrics['unpaid_invoice_count'] - metrics['overdue_invoice_count']} "
            f"invoice(s)."
        )

    if any(term in q for term in ("collected", "received", "amount collected")):
        return (
            f"Our business has collected €{metrics['collected']:,.2f} "
            f"from customers."
        )

    if any(term in q for term in ("outstanding", "receivable", "owe us", "owed to us")):
        return (
            f"Total outstanding customer receivables are "
            f"€{metrics['outstanding']:,.2f}."
        )

    if "average payment delay" in q or "payment delay" in q:
        delay = metrics["average_payment_delay_days"]
        if delay is None:
            return "There is not enough paid-invoice payment-date data to calculate an average delay."
        if delay < 0:
            return (
                f"Customers paid an average of {abs(delay):.1f} days before "
                "the due date."
            )
        return f"Customers paid an average of {delay:.1f} days after the due date."

    if "customer invoice" in q or "total invoiced" in q:
        return (
            f"Total customer invoices are €{metrics['total_invoiced']:,.2f} "
            f"across {metrics['invoice_count']} invoices."
        )

    return None


def ask_financial_assistant(question):
    """Answer supplier-finance questions using calculations before the LLM."""
    if not question or not question.strip():
        return "Please enter a financial question."

    try:
        customer = find_customer_in_question(question)
        if customer:
            customer_metrics = get_customer_metrics(customer)
            if customer_metrics is not None:
                return _format_customer_answer(customer_metrics, question)

        customer_answer = _answer_customer_portfolio_question(question)
        if customer_answer:
            return customer_answer

        supplier = find_supplier_in_question(question)
        if supplier:
            supplier_metrics = get_supplier_metrics(supplier)
            if supplier_metrics is not None:
                return _format_supplier_answer(supplier_metrics, question)

        portfolio_metrics = get_portfolio_metrics()
        if portfolio_metrics is None:
            return "No supplier invoice records were found in the database."

        portfolio_answer = _answer_portfolio_question(question, portfolio_metrics)
        if portfolio_answer:
            return portfolio_answer

        context = get_financial_context(
            reporting_date=DEFAULT_REPORTING_DATE.strftime("%Y-%m-%d")
        )
        prompt = f"""
You are Mittelstand AI, a financial assistant for a German SME.

BUSINESS PERSPECTIVE:
The database contains invoices OUR BUSINESS received from suppliers.
OUR BUSINESS owes money to suppliers. An overdue invoice means OUR BUSINESS
has not paid the supplier by its due date.

INSTRUCTIONS:
- Use only the supplied financial context.
- Do not invent amounts, suppliers, invoice details or reasons for delays.
- Do not calculate financial totals if the context does not provide the values.
- Clearly distinguish overdue invoices from unpaid invoices that are not yet due.
- If requested information is unavailable, say so.
- Explain the result in clear, concise professional language.

VERIFIED FINANCIAL CONTEXT:
{context}

USER QUESTION:
{question}

Answer:
"""
        answer = ask_ollama(prompt)
        if not answer or not answer.strip():
            return "I couldn't generate an answer. Please try rephrasing your question."
        return answer.strip()

    except (sqlite3.Error, FileNotFoundError, ValueError) as exc:
        return f"I couldn't retrieve the financial data: {exc}"
    except Exception as exc:
        return f"The financial assistant encountered an unexpected error: {exc}"
