This is the Result Explainer Agent — the second LLM-powered agent
in the pipeline (after NL2SQL Agent).

Job: take the user's original question + the SQL that ran + the
result rows, and write a concise plain-English insight summary.

Why a separate agent (not just a function)?
  - It has its own system prompt, its own reasoning task, and its
    own failure mode (if the result is empty or weird, it handles
    that gracefully).
  - Keeping it separate means you can swap it independently — e.g.
    plug in a different model just for explanation while keeping
    mistral for SQL generation.

Why different options from nl2sql_agent?
  - SQL generation needs temperature=0 (deterministic, correct syntax).
  - Explanation needs slight creativity (temperature=0.3) so it
    doesn't produce robotic identical phrasing every time.
  - num_predict=400 because explanations are naturally longer than SQL.

This is an AGENT (not a tool) — it uses an LLM (Ollama) to REASON,
not just execute deterministic code.

Self-correction loop (ReAct pattern)
  - Agent writes SQL
  - SQL Executor runs it
  - If it fails, the error is fed BACK to the agent as context
  - Agent rewrites the SQL knowing what went wrong
  - Repeats up to MAX_RETRIES times

This is the core of what makes this "agentic" vs just an LLM wrapper.
The agent Reasons (writes SQL) → Acts (executor runs it) → Observes
(sees the error) → Reasons again (rewrites with error context).


