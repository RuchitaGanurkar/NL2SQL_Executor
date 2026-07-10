import logging

import pandas as pd
from sqlalchemy import text
from db.connection import get_engine

logger = logging.getLogger("nl2sql.sql")


class UnsafeQueryError(Exception):
    """Raised when generated SQL attempts a non-SELECT operation."""
    pass


def _is_safe_select(sql: str) -> bool:
    """
    Defensive check: only allow queries that start with SELECT
    (after stripping whitespace/comments) and don't contain
    dangerous keywords anywhere in the statement.
    """
    normalized = sql.strip().lower()

    if not normalized.startswith("select"):
        return False

    forbidden_keywords = [
        "drop", "delete", "update", "insert", "alter",
        "truncate", "grant", "revoke", "create",
    ]
    # use sqlglot library 
    tokens = normalized.replace(";", " ").replace(",", " ").split()
    if any(keyword in tokens for keyword in forbidden_keywords):
        return False

    return True


def execute_sql(sql: str):
    """
    Executes a SQL string against PostgreSQL.

    Returns a dict:
        {
            "success": True/False,
            "data": pandas.DataFrame (if success),
            "error": str (if failure),
            "row_count": int (if success)
        }
    """
    if not _is_safe_select(sql):
        logger.warning("Blocked unsafe SQL query")
        return {
            "success": False,
            "error": (
                "Blocked: only single SELECT statements are allowed. "
                "This query either isn't a SELECT or contains a forbidden keyword "
                "(DROP/DELETE/UPDATE/INSERT/ALTER/TRUNCATE/CREATE)."
            ),
        }

    try:
        logger.info("Executing SQL: %s", sql.strip().replace("\n", " "))
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()
            columns = list(result.keys())

        df = pd.DataFrame(rows, columns=columns)
        logger.info("SQL succeeded, %d row(s) returned", len(df))

        return {
            "success": True,
            "data": df,
            "row_count": len(df),
        }

    except Exception as e:
        logger.exception("SQL execution failed")
        return {
            "success": False,
            "error": str(e),
        }