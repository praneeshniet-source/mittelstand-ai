import logging

import pandas as pd
import psycopg

from config.settings import settings


logger = logging.getLogger("mittelstand_ai.database")


def get_connection():
    """Create a PostgreSQL database connection using central settings."""
    try:
        return psycopg.connect(
            settings.database_url,
            connect_timeout=settings.database_connect_timeout,
            application_name=settings.app_name,
        )
    except psycopg.Error:
        logger.exception("Unable to connect to PostgreSQL.")
        raise


def fetch_dataframe(query, params=None):
    """Execute a SELECT query and return its results as a DataFrame."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                rows = cur.fetchall()
                columns = [column.name for column in cur.description]

        return pd.DataFrame(rows, columns=columns)

    except psycopg.Error:
        logger.exception("PostgreSQL query execution failed.")
        raise