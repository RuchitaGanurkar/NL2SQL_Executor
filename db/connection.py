import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import streamlit as st

load_dotenv()  

def get_engine():
    db_host = os.getenv("DB_HOST", st.secrets.get("DB_HOST", ""))
    db_name = os.getenv("DB_NAME", st.secrets.get("DB_NAME", ""))
    db_user = os.getenv("DB_USER", st.secrets.get("DB_USER", ""))
    db_password = os.getenv("DB_PASSWORD", st.secrets.get("DB_PASSWORD", ""))
    
    
    raw_port = os.getenv("DB_PORT", st.secrets.get("DB_PORT", "5432"))
    
    if not raw_port or str(raw_port).strip() == "":
        db_port = "5432"
    else:
        db_port = str(raw_port).strip()

    if not db_host or not db_user:
        st.error("Database configuration variables are missing! Please check your Render Environment Variables.")
        st.stop()

    connection_string = (
        f"postgresql+psycopg2://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}?sslmode=require"
    )

    return create_engine(connection_string)

def test_connection():

    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return True, None
    except Exception as e:
        return False, str(e)