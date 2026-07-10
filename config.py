import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

_LOCAL_SECRETS = PROJECT_ROOT / ".streamlit" / "secrets.toml"
_USER_SECRETS = Path.home() / ".streamlit" / "secrets.toml"


def _secrets_file_exists() -> bool:
    return _LOCAL_SECRETS.is_file() or _USER_SECRETS.is_file()


def get_setting(key: str, default: str = "") -> str:
    """Prefer OS env / .env, then Streamlit secrets when available."""
    value = os.getenv(key)
    if value is not None and str(value).strip() != "":
        return str(value).strip()

    if not _secrets_file_exists():
        return default

    try:
        import streamlit as st

        return str(st.secrets[key])
    except Exception:
        return default


def get_setting_on_cloud(key: str, default: str = "") -> str:
    """
    Like get_setting, but also reads Streamlit Cloud secrets
    (injected at runtime without a local secrets.toml file).
    """
    value = os.getenv(key)
    if value is not None and str(value).strip() != "":
        return str(value).strip()

    try:
        import streamlit as st
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        if get_script_run_ctx() is not None:
            return str(st.secrets[key])
    except Exception:
        pass

    return get_setting(key, default)
