import logging
from urllib.parse import unquote, urlparse

from sqlalchemy import create_engine

from config import get_setting_on_cloud

logger = logging.getLogger("nl2sql.db")


def _parse_database_url(url: str) -> dict[str, str]:
    normalized = url.strip()
    for prefix in ("postgresql+psycopg2://", "postgresql://", "postgres://"):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
            break

    parsed = urlparse(f"postgresql://{normalized}")

    return {
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "host": parsed.hostname or "",
        "port": str(parsed.port or "5432"),
        "name": (parsed.path or "").lstrip("/"),
    }


def _looks_like_database_url(value: str) -> bool:
    lowered = value.lower()
    return (
        lowered.startswith("postgresql://")
        or lowered.startswith("postgres://")
        or lowered.startswith("postgresql+psycopg2://")
    )


def _resolve_db_config() -> dict[str, str]:
    database_url = get_setting_on_cloud("DATABASE_URL") or get_setting_on_cloud("DB_URL")
    if database_url:
        logger.info("Using DATABASE_URL / DB_URL for PostgreSQL connection")
        return _parse_database_url(database_url)

    db_host = get_setting_on_cloud("DB_HOST")
    if db_host and _looks_like_database_url(db_host):
        logger.info("DB_HOST contains a full database URL — parsing connection details")
        return _parse_database_url(db_host)

    raw_port = get_setting_on_cloud("DB_PORT", "5432")
    db_port = raw_port if raw_port else "5432"

    return {
        "host": db_host,
        "port": db_port,
        "name": get_setting_on_cloud("DB_NAME"),
        "user": get_setting_on_cloud("DB_USER"),
        "password": get_setting_on_cloud("DB_PASSWORD"),
    }


def get_engine():
    config = _resolve_db_config()
    db_host = config["host"]
    db_port = config["port"]
    db_name = config["name"]
    db_user = config["user"]
    db_password = config["password"]

    missing = [
        name
        for name, value in {
            "DB_HOST": db_host,
            "DB_NAME": db_name,
            "DB_USER": db_user,
        }.items()
        if not value
    ]

    if missing:
        message = (
            "Database configuration is incomplete. Missing: "
            + ", ".join(missing)
            + ". Set DATABASE_URL or DB_HOST/DB_NAME/DB_USER/DB_PASSWORD."
        )
        logger.error(message)
        raise ValueError(message)

    connection_string = (
        f"postgresql+psycopg2://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}"
    )

    logger.info(
        "Connecting to PostgreSQL at %s:%s/%s as %s",
        db_host,
        db_port,
        db_name,
        db_user,
    )
    return create_engine(connection_string, pool_pre_ping=True)


def test_connection():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        logger.info("PostgreSQL connection test succeeded")
        return True, None
    except Exception as e:
        logger.exception("PostgreSQL connection test failed")
        return False, str(e)
