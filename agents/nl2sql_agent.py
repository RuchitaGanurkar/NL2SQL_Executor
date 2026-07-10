import logging

from agents.llm_client import chat
from db.sql_executor import execute_sql

logger = logging.getLogger("nl2sql.agent")

# How many times the agent is allowed to rewrite SQL before giving up
MAX_RETRIES = 3

SYSTEM_PROMPT = """You are a PostgreSQL expert. Your job is to convert a user's
natural language question into a single, valid PostgreSQL query.

RULES:
1. Output ONLY the SQL query. No explanations, no markdown code fences, no commentary.
2. Use ONLY the tables and columns provided in the schema below. Never invent column names.
3. Always use explicit JOINs (not comma-separated joins).
4. Use table aliases for readability when joining multiple tables.
5. If the question is ambiguous or cannot be answered with the given schema, output exactly:
   AMBIGUOUS: <short reason why>
6. Do not use SELECT * — always specify columns explicitly.
7. End the query with a semicolon.
"""

CORRECTION_SYSTEM_PROMPT = """You are a PostgreSQL expert fixing a broken SQL query.
You will be given:
  - The original user question
  - The database schema
  - The SQL query that failed
  - The exact error message from PostgreSQL

Your job is to write a CORRECTED SQL query that fixes the error.

RULES:
1. Output ONLY the corrected SQL query. No explanations, no markdown, no commentary.
2. Use ONLY the tables and columns from the schema. Never invent column names.
3. Study the error message carefully — it tells you exactly what is wrong.
4. End the query with a semicolon.
"""


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """Single LLM call — shared by generate and correct paths."""
    raw = chat(
        system_prompt,
        user_prompt,
        temperature=0,
        num_predict=300,
        top_k=10,
    )
    cleaned = _clean_sql(raw)
    logger.info("Generated SQL candidate (%d chars)", len(cleaned))
    return cleaned


def generate_sql(question: str, schema_text: str) -> str:
    """
    First-pass SQL generation from natural language.
    Returns clean SQL string or "AMBIGUOUS: ..." string.
    """
    user_prompt = f"""DATABASE SCHEMA:
{schema_text}

USER QUESTION:
{question}

SQL QUERY:"""

    return _call_llm(SYSTEM_PROMPT, user_prompt)


def _correct_sql(question: str, schema_text: str, bad_sql: str, error: str) -> str:
    """
    Correction pass — agent sees its own mistake and rewrites.
    This is the 'Observe → Reason again' part of ReAct.
    """
    user_prompt = f"""DATABASE SCHEMA:
{schema_text}

ORIGINAL USER QUESTION:
{question}

SQL THAT FAILED:
{bad_sql}

POSTGRESQL ERROR:
{error}

CORRECTED SQL QUERY:"""

    return _call_llm(CORRECTION_SYSTEM_PROMPT, user_prompt)


def generate_sql_with_retry(question: str, schema_text: str) -> dict:
    """
    Full agentic loop with self-correction.

    Returns a dict:
    {
        "success": True/False,
        "final_sql": str,           # the SQL that eventually worked (or last attempt)
        "data": DataFrame,          # only present if success=True
        "row_count": int,           # only present if success=True
        "error": str,               # only present if success=False
        "attempts": int,            # how many SQL generations were needed (1 = first try)
        "attempt_log": [            # list of each attempt for the summary UI
            {"attempt": 1, "sql": "...", "error": "..." or None},
            ...
        ]
    }
    """
    attempt_log = []
    logger.info("Starting NL2SQL for question: %s", question)

    # --- Attempt 1: first-pass generation ---
    sql = generate_sql(question, schema_text)

    if sql.startswith("AMBIGUOUS:"):
        return {
            "success": False,
            "final_sql": None,
            "error": sql,
            "attempts": 0,
            "attempt_log": [],
        }

    logger.info("Attempt 1 SQL: %s", sql)
    result = execute_sql(sql)
    attempt_log.append({
        "attempt": 1,
        "sql": sql,
        "error": None if result["success"] else result["error"],
    })

    if result["success"]:
        return {
            "success": True,
            "final_sql": sql,
            "data": result["data"],
            "row_count": result["row_count"],
            "attempts": 1,
            "attempt_log": attempt_log,
        }

    # --- Correction loop: attempts 2, 3, 4 (MAX_RETRIES more tries) ---
    last_error = result["error"]
    last_sql = sql

    for attempt_num in range(2, MAX_RETRIES + 2):
        corrected_sql = _correct_sql(question, schema_text, last_sql, last_error)
        result = execute_sql(corrected_sql)

        attempt_log.append({
            "attempt": attempt_num,
            "sql": corrected_sql,
            "error": None if result["success"] else result["error"],
        })

        if result["success"]:
            return {
                "success": True,
                "final_sql": corrected_sql,
                "data": result["data"],
                "row_count": result["row_count"],
                "attempts": attempt_num,
                "attempt_log": attempt_log,
            }

        last_error = result["error"]
        last_sql = corrected_sql

    # All retries exhausted
    return {
        "success": False,
        "final_sql": last_sql,
        "error": last_error,
        "attempts": MAX_RETRIES + 1,
        "attempt_log": attempt_log,
    }


def _clean_sql(raw_output: str) -> str:
    """Strip markdown code fences LLMs sometimes add despite instructions."""
    text = raw_output.strip()

    if text.startswith("AMBIGUOUS:"):
        return text

    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    return text