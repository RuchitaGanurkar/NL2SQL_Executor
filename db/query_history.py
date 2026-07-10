import logging

from sqlalchemy import text
from db.connection import get_engine

logger = logging.getLogger("nl2sql.history")


def save_query(
    question: str,
    generated_sql: str | None,
    row_count: int | None,
    attempts: int,
    status: str,
    error_message: str | None = None,
    explanation: str | None = None,
) -> int | None:
    """
    Saves one query run to query_history.
    Returns the new record's id, or None if insert failed.

    Args:
        question      : the user's natural language question
        generated_sql : the final SQL (None if ambiguous)
        row_count     : rows returned (None if failed/ambiguous)
        attempts      : how many SQL generation attempts were made
        status        : 'success' | 'failed' | 'ambiguous'
        error_message : last error from PostgreSQL (if failed)
        explanation   : plain-English insight from explainer agent (if success)
    """
    try:
        engine = get_engine()
        with engine.begin() as conn:   
            result = conn.execute(
                text("""
                    INSERT INTO query_history
                        (question, generated_sql, row_count, attempts,
                         status, error_message, explanation)
                    VALUES
                        (:question, :generated_sql, :row_count, :attempts,
                         :status, :error_message, :explanation)
                    RETURNING id
                """),
                {
                    "question": question,
                    "generated_sql": generated_sql,
                    "row_count": row_count,
                    "attempts": attempts,
                    "status": status,
                    "error_message": error_message,
                    "explanation": explanation,
                }
            )
            row = result.fetchone()
            return row[0] if row else None
    except Exception as e:
        logger.exception("query_history save failed")
        return None


def fetch_history(limit: int = 20) -> list[dict]:
    """
    Returns the most recent `limit` queries from history,
    newest first.

    Each record is a dict:
    {
        "id": int,
        "question": str,
        "generated_sql": str | None,
        "row_count": int | None,
        "attempts": int,
        "status": str,
        "error_message": str | None,
        "explanation": str | None,
        "created_at": datetime
    }
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, question, generated_sql, row_count,
                           attempts, status, error_message, explanation,
                           created_at
                    FROM query_history
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"limit": limit}
            )
            columns = list(result.keys())
            rows = result.fetchall()

        return [dict(zip(columns, row)) for row in rows]

    except Exception as e:
        logger.exception("query_history fetch failed")
        return []