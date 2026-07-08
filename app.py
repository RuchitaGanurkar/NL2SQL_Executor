import streamlit as st
from db.connection import test_connection
from db.schema_fetcher import fetch_schema, schema_to_prompt_string
from agents.nl2sql_agent import generate_sql_with_retry
from agents.explainer_agent import explain_result
from db.query_history import save_query, fetch_history

st.set_page_config(
    page_title="NL2SQL Agent",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── Global ─────────────────────────────────────────────────── */
[data-testid="stAppViewContainer"] {
    background-color: #0f1117;
}
[data-testid="stSidebar"] {
    background-color: #161b27;
    border-right: 1px solid #2a2f3e;
}

/* ── Typography ─────────────────────────────────────────────── */
h1 { color: #e2e8f0 !important; font-size: 1.6rem !important; }
h2, h3 { color: #cbd5e1 !important; }
p, li, label { color: #94a3b8 !important; }
.stCaption { color: #64748b !important; }

/* ── Query input ─────────────────────────────────────────────── */
.stTextInput input {
    background-color: #1e2433 !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-size: 1rem !important;
    padding: 0.75rem 1rem !important;
}
.stTextInput input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
}

/* ── Primary button ─────────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 2rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    transition: opacity 0.2s !important;
}
.stButton > button[kind="primary"]:hover { opacity: 0.85 !important; }

/* ── Secondary button ───────────────────────────────────────── */
.stButton > button:not([kind="primary"]) {
    background-color: #1e2433 !important;
    color: #94a3b8 !important;
    border: 1px solid #334155 !important;
    border-radius: 6px !important;
}

/* ── Result cards ───────────────────────────────────────────── */
.result-card {
    background: #1e2433;
    border: 1px solid #2a2f3e;
    border-radius: 10px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}
.stat-pill {
    display: inline-block;
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 20px;
    padding: 0.25rem 0.85rem;
    font-size: 0.8rem;
    color: #94a3b8;
    margin-right: 0.5rem;
    margin-bottom: 0.5rem;
}
.success-pill { border-color: #22c55e; color: #22c55e; }
.warn-pill    { border-color: #f59e0b; color: #f59e0b; }
.error-pill   { border-color: #ef4444; color: #ef4444; }

/* ── Dataframe ───────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #2a2f3e !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}

/* ── Expander ─────────────────────────────────────────────────── */
.streamlit-expanderHeader {
    background-color: #1e2433 !important;
    border-radius: 6px !important;
    color: #94a3b8 !important;
}

/* ── Sidebar schema labels ────────────────────────────────────── */
.schema-col {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.78rem;
    color: #64748b;
    padding: 2px 0;
    border-left: 2px solid #2a2f3e;
    padding-left: 8px;
    margin: 2px 0;
}
.schema-col-pk { border-left-color: #6366f1; color: #818cf8; }
.schema-col-fk { border-left-color: #f59e0b; color: #fbbf24; }

/* ── Divider ──────────────────────────────────────────────────── */
hr { border-color: #2a2f3e !important; }
</style>
""", unsafe_allow_html=True)


with st.sidebar:
    st.markdown("### NL2SQL Agent")
    st.divider()

    try:
        ok, err = test_connection()
        if ok:
            st.markdown('<span class="stat-pill success-pill"> PostgreSQL connected</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="stat-pill error-pill"> PostgreSQL disconnected</span>', unsafe_allow_html=True)
            st.code(err, language="text")
    except Exception as e:
        st.markdown('<span class="stat-pill error-pill"> Connection error</span>', unsafe_allow_html=True)

    st.divider()

    st.markdown("**Schema Explorer**")
    try:
        schema = fetch_schema()
        if not schema:
            st.warning("No tables found. Run seed.sql first.")
        else:
            for table in schema:
                fk_map = {fk["column"]: fk for fk in table["foreign_keys"]}
                col_count = len(table["columns"])
                with st.expander(f"**{table['table_name']}** · {col_count} cols"):
                    for col in table["columns"]:
                        is_pk = col["primary_key"]
                        is_fk = col["name"] in fk_map
                        cls = "schema-col-pk" if is_pk else ("schema-col-fk" if is_fk else "schema-col")
                        icon = "" if is_pk else ("→ " if is_fk else "")
                        fk_ref = ""
                        if is_fk:
                            fk = fk_map[col["name"]]
                            fk_ref = f' → {fk["references_table"]}.{fk["references_column"]}'
                        st.markdown(
                            f'<div class="{cls}">{icon}{col["name"]} <span style="color:#475569">({col["type"]}){fk_ref}</span></div>',
                            unsafe_allow_html=True
                        )
    except Exception as e:
        st.error(f"Schema error: {e}")

    st.divider()

    with st.expander("Raw schema (LLM text)", expanded=False):
        try:
            st.code(schema_to_prompt_string(fetch_schema()), language="text")
        except Exception as e:
            st.error(str(e))

    st.divider()

    st.markdown("**Query History**")
    history = fetch_history(limit=15)

    if not history:
        st.caption("No queries yet — run one to start.")
    else:
        for record in history:
            status = record["status"]
            badge = "" if status == "success" else ("" if status == "failed" else "")

            q_display = record["question"]
            if len(q_display) > 42:
                q_display = q_display[:42] + "..."

            ts = record["created_at"].strftime("%d %b, %H:%M")
            attempts = record["attempts"]
            attempt_label = f" · {attempts} attempt{'s' if attempts > 1 else ''}" if attempts > 1 else ""

            with st.expander(f"{badge} {q_display}", expanded=False):
                st.caption(f"{ts}{attempt_label}")
                if record["explanation"]:
                    st.markdown(
                        f'<p style="color:#94a3b8;font-size:0.82rem;">{record["explanation"]}</p>',
                        unsafe_allow_html=True
                    )
                if record["generated_sql"]:
                    st.code(record["generated_sql"], language="sql")
                if record["error_message"]:
                    st.caption(f"Error: {record['error_message']}")


st.markdown("## Ask your database anything")
st.caption("Write a question in plain English — the agent writes SQL, runs it, and self-corrects if it fails.")

st.markdown("")  

col_input, col_btn = st.columns([5, 1])
with col_input:
    question = st.text_input(
        label="question",
        label_visibility="collapsed",
        placeholder="e.g.  Which product category generated the most revenue?",
    )
with col_btn:
    run = st.button("Run →", type="primary", use_container_width=True)

st.markdown("")

st.markdown("**Try these:**")
examples = [
    "Top 5 customers by total orders",
    "Revenue by product category",
    "Customers with no orders",
    "Average order value by region",
]
ex_cols = st.columns(len(examples))
for i, (col, ex) in enumerate(zip(ex_cols, examples)):
    with col:
        if st.button(ex, key=f"ex_{i}"):
            question = ex
            run = True

st.divider()

if run:
    if not question.strip():
        st.warning("Type a question first.")
    else:
        try:
            schema = fetch_schema()
            schema_text = schema_to_prompt_string(schema)

            with st.spinner("Agent is thinking..."):
                result = generate_sql_with_retry(question, schema_text)

            if result.get("final_sql") is None:
                save_query(
                    question=question,
                    generated_sql=None,
                    row_count=None,
                    attempts=result.get("attempts", 0),
                    status="ambiguous",
                    error_message=result.get("error"),
                )
                st.markdown(
                    f'<div class="result-card">'
                    f'<span class="stat-pill warn-pill"> Ambiguous</span><br><br>'
                    f'{result["error"]}'
                    f'</div>',
                    unsafe_allow_html=True
                )
            elif result["success"]:
                attempts = result["attempts"]
                badge = (
                    '<span class="stat-pill success-pill"> 1st attempt</span>'
                    if attempts == 1 else
                    f'<span class="stat-pill warn-pill"> Self-corrected in {attempts} attempts</span>'
                )
                rows = result["row_count"]
                st.markdown(
                    f'<div class="result-card">'
                    f'{badge}'
                    f'<span class="stat-pill">{rows} row{"s" if rows != 1 else ""} returned</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                with st.spinner("Generating insight..."):
                    explanation = explain_result(
                        question,
                        result["final_sql"],
                        result["data"]
                    )

                save_query(
                    question=question,
                    generated_sql=result["final_sql"],
                    row_count=result["row_count"],
                    attempts=result["attempts"],
                    status="success",
                    explanation=explanation,
                )

                tab_insight, tab_result, tab_sql, tab_log = st.tabs([
                    " Insight", " Results", " SQL", " Attempt Log"
                ])

                with tab_insight:
                    st.markdown(
                        f'<div class="result-card" style="border-left: 3px solid #6366f1;">'
                        f'<p style="color:#e2e8f0; font-size:1.05rem; line-height:1.7;">'
                        f'{explanation}'
                        f'</p></div>',
                        unsafe_allow_html=True
                    )
                    st.caption("Generated by Result Explainer Agent (Ollama/mistral)")

                with tab_result:
                    st.dataframe(result["data"], use_container_width=True, height=400)

                with tab_sql:
                    st.code(result["final_sql"], language="sql")

                with tab_log:
                    if attempts == 1:
                        st.success("Succeeded on first attempt — no retries needed.")
                    else:
                        for log in result["attempt_log"]:
                            n = log["attempt"]
                            if log["error"] is None:
                                st.markdown(f"**Attempt {n} —  succeeded**")
                                st.code(log["sql"], language="sql")
                            else:
                                st.markdown(f"**Attempt {n} —  failed**")
                                st.code(log["sql"], language="sql")
                                st.caption(f"PostgreSQL error: {log['error']}")
                            if n < attempts:
                                st.divider()
            else:
                attempts = result["attempts"]
                save_query(
                    question=question,
                    generated_sql=result.get("final_sql"),
                    row_count=None,
                    attempts=attempts,
                    status="failed",
                    error_message=result.get("error"),
                )
                st.markdown(
                    f'<div class="result-card">'
                    f'<span class="stat-pill error-pill"> Failed after {attempts} attempts</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                tab_sql, tab_log = st.tabs([" Last SQL", " Attempt Log"])

                with tab_sql:
                    st.code(result["final_sql"], language="sql")
                    st.error(result["error"])

                with tab_log:
                    for log in result["attempt_log"]:
                        n = log["attempt"]
                        st.markdown(f"**Attempt {n}**")
                        st.code(log["sql"], language="sql")
                        if log["error"]:
                            st.caption(f"Error: {log['error']}")
                        if n < attempts:
                            st.divider()

        except Exception as e:
            st.error("Something went wrong")
            st.code(str(e), language="text")
            st.info("Make sure Ollama is running: `ollama serve` and `ollama pull mistral`")