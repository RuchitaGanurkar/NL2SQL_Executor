import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()  # reads .env file into environment variables


def get_engine():
    """
    Builds a PostgreSQL connection string from .env values
    and returns a SQLAlchemy engine (a reusable connection handler).
    """
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    connection_string = (
        f"postgresql+psycopg2://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}"
    )

    engine = create_engine(connection_string)
    return engine


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