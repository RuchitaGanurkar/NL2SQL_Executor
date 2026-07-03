import json
import ollama

MODEL_NAME = "mistral"

EXPLAINER_SYSTEM_PROMPT = """You are a data analyst assistant explaining query results
to a non-technical business user.

You will receive:
  - The user's original question
  - The SQL query that was executed
  - The result rows as JSON

Your job: write 2-4 sentences of plain-English insight.

RULES:
1. Lead with the most important finding — the direct answer to the question.
2. Mention specific numbers, names, or values from the results.
3. If relevant, note patterns, outliers, or comparisons.
4. If the result is empty (0 rows), say so clearly and suggest why.
5. Do NOT mention SQL, tables, columns, or technical terms.
6. Do NOT start with "The query..." or "Based on the results...".
7. Write as if you are a colleague summarizing a report.
"""


def explain_result(question: str, sql: str, df) -> str:
    """
    Generates a plain-English explanation of query results.

    Args:
        question: original user question
        sql: the SQL that ran successfully
        df: pandas DataFrame of results

    Returns:
        A 2-4 sentence plain-English insight string.
        Falls back to a safe message if LLM call fails.
    """
    if df is None or df.empty:
        return "The query returned no results. This could mean the data doesn't exist yet, or the filter conditions matched nothing."

    # Convert DataFrame to compact JSON for the prompt
    # Limit to first 20 rows — LLMs don't need all 10,000 rows to explain a pattern
    rows_sample = df.head(20).to_dict(orient="records")
    rows_json = json.dumps(rows_sample, indent=2, default=str)

    # Truncate if too long (safety for wide tables)
    if len(rows_json) > 2000:
        rows_json = rows_json[:2000] + "\n... (truncated)"

    user_prompt = f"""USER QUESTION:
{question}

SQL EXECUTED:
{sql}

RESULT ROWS (JSON):
{rows_json}

INSIGHT:"""

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": EXPLAINER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            options={
                "temperature": 0.3,   # slight creativity — not robotic, not hallucinating
                "num_predict": 400,   # explanations are longer than SQL
                "top_k": 20,
            },
        )
        return response["message"]["content"].strip()

    except Exception as e:
        # Never crash the UI because explanation failed
        return f"Results loaded successfully. (Explanation unavailable: {str(e)})"