import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import streamlit as st

load_dotenv()  


def get_engine():

    db_host = st.secrets.get("DB_HOST", os.getenv("DB_HOST", ""))
    db_name = st.secrets.get("DB_NAME", os.getenv("DB_NAME", ""))
    db_user = st.secrets.get("DB_USER", os.getenv("DB_USER", ""))
    db_password = st.secrets.get("DB_PASSWORD", os.getenv("DB_PASSWORD", ""))
    
    db_port = str(st.secrets.get("DB_PORT", os.getenv("DB_PORT", "5432")))

   
    if not db_host or not db_user:
        st.error("Database configuration variables are missing! Please check your Streamlit Cloud Secrets.")
        st.stop()

    connection_string = (
        f"postgresql+psycopg2://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}"
    )

    return create_engine(connection_string)

def test_connection():
    """
    Quick sanity check: tries to connect and run SELECT 1.
    Returns (True, None) on success, (False, error_message) on failure.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return True, None
    except Exception as e:
        return False, str(e)