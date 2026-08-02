"""
BasketPilot — Streamlit deployment entry point.

Starts the FastAPI backend in a background thread and embeds the BasketPilot demo UI.
Use: streamlit run streamlit_app.py
"""

from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

import httpx
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_BASE = f"http://{API_HOST}:{API_PORT}"


def _load_secrets_into_env() -> None:
    """Map Streamlit Cloud secrets → environment variables for pydantic-settings."""
    try:
        secrets = st.secrets
    except Exception:
        return

    mapping = {
        "GROK_API_KEY": "GROK_API_KEY",
        "GROQ_API_KEY": "GROQ_API_KEY",
        "GROK_MODEL": "GROK_MODEL",
        "USE_LLM": "USE_LLM",
        "SURVEY_PDF_PATH": "SURVEY_PDF_PATH",
        "APP_ENV": "APP_ENV",
        "API_PORT": "API_PORT",
    }
    for secret_key, env_key in mapping.items():
        if secret_key in secrets:
            os.environ[env_key] = str(secrets[secret_key])


def _wait_for_backend(url: str, attempts: int = 40) -> bool:
    for _ in range(attempts):
        try:
            resp = httpx.get(f"{url}/health", timeout=1.0)
            if resp.status_code == 200:
                return True
        except httpx.HTTPError:
            pass
        time.sleep(0.25)
    return False


@st.cache_resource(show_spinner="Starting BasketPilot backend…")
def start_backend() -> str:
    """Run Uvicorn once per Streamlit session."""
    _load_secrets_into_env()

    import uvicorn

    config = uvicorn.Config(
        "src.app.main:app",
        host=API_HOST,
        port=API_PORT,
        log_level=os.getenv("LOG_LEVEL", "warning").lower(),
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    if not _wait_for_backend(API_BASE):
        st.error("Backend failed to start. Check logs and `SURVEY_PDF_PATH` in secrets.")
    return API_BASE


st.set_page_config(
    page_title="BasketPilot — Discovery Pilot",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 1rem; padding-bottom: 0; max-width: 480px; }
      iframe { border: none; border-radius: 24px; }
    </style>
    """,
    unsafe_allow_html=True,
)

api_url = start_backend()

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.caption("BasketPilot · Smart Discovery MVP · Demo user: `user_001`")

st.components.v1.iframe(f"{api_url}/", height=860, scrolling=True)

with st.expander("Deployment info"):
    st.markdown(
        f"""
        - **Backend:** [{api_url}/health]({api_url}/health)
        - **API docs:** [{api_url}/docs]({api_url}/docs)
        - **Local run:** `streamlit run streamlit_app.py`
        - **Cloud:** set secrets in Streamlit Community Cloud (see README)
        """
    )
