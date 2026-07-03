import streamlit as st
from sqlalchemy import inspect
from db.connection import get_engine


@st.cache_data(ttl=300) 
def fetch_schema():
    """
    Returns schema as a list of dicts, one per table:
    [
        {
            "table_name": "customers",
            "columns": [
                {"name": "customer_id", "type": "INTEGER", "primary_key": True},
                {"name": "name", "type": "VARCHAR(100)", "primary_key": False},
                ...
            ],
            "foreign_keys": [
                {"column": "customer_id", "references_table": "customers", "references_column": "customer_id"}
            ]
        },
        ...
    ]
    """
    engine = get_engine()
    inspector = inspect(engine)

    schema = []

    for table_name in inspector.get_table_names():
        columns_raw = inspector.get_columns(table_name)
        pk_constraint = inspector.get_pk_constraint(table_name)
        pk_columns = pk_constraint.get("constrained_columns", []) if pk_constraint else []
        fks_raw = inspector.get_foreign_keys(table_name)

        columns = [
            {
                "name": col["name"],
                "type": str(col["type"]),
                "primary_key": col["name"] in pk_columns,
            }
            for col in columns_raw
        ]

        foreign_keys = [
            {
                "column": fk["constrained_columns"][0],
                "references_table": fk["referred_table"],
                "references_column": fk["referred_columns"][0],
            }
            for fk in fks_raw
            if fk.get("constrained_columns") and fk.get("referred_columns")
        ]

        schema.append({
            "table_name": table_name,
            "columns": columns,
            "foreign_keys": foreign_keys,
        })

    return schema


def schema_to_prompt_string(schema):
    """
    Converts the schema list into a compact text block.
    This is the format we'll hand to the LLM in Phase 3 — LLMs work
    better with concise, structured text than with nested JSON.

    Example output:
        Table: customers
          - customer_id (INTEGER, PRIMARY KEY)
          - name (VARCHAR(100))
          - region (VARCHAR(50))

        Table: orders
          - order_id (INTEGER, PRIMARY KEY)
          - customer_id (INTEGER) -> references customers.customer_id
    """
    lines = []
    for table in schema:
        lines.append(f"Table: {table['table_name']}")
        fk_map = {fk["column"]: fk for fk in table["foreign_keys"]}

        for col in table["columns"]:
            col_line = f"  - {col['name']} ({col['type']})"
            if col["primary_key"]:
                col_line += " [PRIMARY KEY]"
            if col["name"] in fk_map:
                fk = fk_map[col["name"]]
                col_line += f" -> references {fk['references_table']}.{fk['references_column']}"
            lines.append(col_line)
        lines.append("") 

    return "\n".join(lines)