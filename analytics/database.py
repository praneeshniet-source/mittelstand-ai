import os

import pandas as pd
import psycopg


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "dbname=mittelstand_ai"
)


def get_connection():
    """Create a PostgreSQL database connection."""
    return psycopg.connect(DATABASE_URL)


def fetch_dataframe(query, params=None):
    """Execute a SELECT query and return its results as a DataFrame."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            rows = cur.fetchall()
            columns = [column.name for column in cur.description]

    return pd.DataFrame(rows, columns=columns)
