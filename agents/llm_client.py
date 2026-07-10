import json
import logging
import urllib.error
import urllib.request

from config import get_setting_on_cloud

logger = logging.getLogger("nl2sql.llm")


def get_llm_provider() -> str:
    return get_setting_on_cloud("LLM_PROVIDER", "ollama").lower()


def get_model_name() -> str:
    return get_setting_on_cloud("OLLAMA_MODEL", "mistral")


def get_ollama_host() -> str:
    return get_setting_on_cloud("OLLAMA_HOST", "http://127.0.0.1:11434")


def _chat_ollama(
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    num_predict: int,
    top_k: int,
) -> str:
    import ollama

    model = get_model_name()
    host = get_ollama_host()
    logger.info("Calling Ollama model=%s host=%s", model, host)

    client = ollama.Client(host=host)
    response = client.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={
            "temperature": temperature,
            "num_predict": num_predict,
            "top_k": top_k,
        },
    )
    content = response["message"]["content"].strip()
    logger.info("Ollama response received (%d chars)", len(content))
    return content


def chat(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float = 0.0,
    num_predict: int = 300,
    top_k: int = 10,
) -> str:
    logger.info(
        "LLM chat start provider=ollama model=%s host=%s prompt_chars=%d",
        get_model_name(),
        get_ollama_host(),
        len(user_prompt),
    )
    return _chat_ollama(system_prompt, user_prompt, temperature, num_predict, top_k)


def test_llm_connection() -> tuple[bool, str | None]:
    model = get_model_name()
    host = get_ollama_host()

    try:
        import ollama

        client = ollama.Client(host=host)
        client.list()
        return True, f"Ollama ({model} @ {host})"
    except Exception as e:
        logger.exception("LLM connection test failed")
        hint = (
            "Ollama must be reachable from where this app runs. "
            "Locally: run `ollama serve`. "
            "On Streamlit Cloud: host Streamlit on the same machine as Ollama, "
            "or expose Ollama via a tunnel and set OLLAMA_HOST in secrets."
        )
        return False, f"{e}\n\n{hint}"
