"""
BasketPilot — Streamlit deployment (Streamlit Community Cloud compatible).

Embeds the real BasketPilot web UI (index.html + app.js + styles.css) and preloads
recommendation data via in-process TestClient — no browser → localhost calls.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "src" / "phase2" / "frontend"
sys.path.insert(0, str(ROOT))

DEMO_USER = "user_001"


def _load_secrets_into_env() -> None:
    try:
        secrets = st.secrets
    except Exception:
        return
    for key in ("GROK_API_KEY", "GROQ_API_KEY", "GROK_MODEL", "USE_LLM", "SURVEY_PDF_PATH", "APP_ENV"):
        try:
            os.environ[key] = str(secrets[key])
        except Exception:
            pass


@st.cache_resource(show_spinner="Starting BasketPilot engine…")
def get_api_client():
    _load_secrets_into_env()
    from starlette.testclient import TestClient
    from src.app.main import app

    return TestClient(app)


def _load_initial_cards() -> dict:
    client = get_api_client()
    response = client.post("/api/v1/phase2/cards", json={"user_id": DEMO_USER})
    response.raise_for_status()
    return response.json()


def _escape_script(js: str) -> str:
    return js.replace("</script>", "<\\/script>")


def _asset_version() -> str:
    paths = (FRONTEND / "index.html", FRONTEND / "styles.css", FRONTEND / "app.js")
    return str(tuple(p.stat().st_mtime_ns for p in paths if p.exists()))


@st.cache_data(show_spinner=False)
def build_embed_html(cards_json: str, asset_version: str) -> str:
    """Self-contained HTML shell for components.html (stable across reruns)."""
    index_html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    styles = (FRONTEND / "styles.css").read_text(encoding="utf-8")
    app_js = (FRONTEND / "app.js").read_text(encoding="utf-8")

    body = index_html.split("<body>", 1)[1].rsplit("</body>", 1)[0]
    body = body.replace('<script src="/ui/app.js"></script>', "")
    body = body.replace('<link rel="stylesheet" href="/ui/styles.css" />', "")

    bootstrap = f"""
document.documentElement.classList.add("embed-mode");
window.__STREAMLIT_MODE__ = true;
window.__INITIAL_CARDS__ = {cards_json};
"""

    return f"""<!DOCTYPE html>
<html lang="en" class="embed-mode">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <title>BasketPilot</title>
  <style>{styles}</style>
  <script>{bootstrap}</script>
</head>
<body>
{body}
<script>{_escape_script(app_js)}</script>
</body>
</html>"""


def main() -> None:
    st.set_page_config(
        page_title="BasketPilot — Smart Discovery",
        page_icon="🛒",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown(
        """
        <style>
          header[data-testid="stHeader"] { display: none; }
          #MainMenu { visibility: hidden; }
          footer { visibility: hidden; }
          .stApp { background: #f8fafc; }
          .block-container {
            padding: 0 !important;
            max-width: 100% !important;
            margin: 0 !important;
          }
          iframe[title="BasketPilot"] {
            width: 100vw !important;
            max-width: 100% !important;
            border: 0 !important;
            display: block !important;
            min-height: 100vh;
            min-height: 100dvh;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    try:
        client = get_api_client()
        health = client.get("/health")
        if health.status_code != 200:
            st.error("BasketPilot backend failed to start.")
            st.stop()
        initial_cards = _load_initial_cards()
    except Exception as exc:
        st.error(f"Connection failure: {exc}")
        st.info("Run `python -m pip install -r requirements.txt` and redeploy.")
        st.stop()

    cards_json = json.dumps(initial_cards)
    embed_html = build_embed_html(cards_json, _asset_version())

    components.html(embed_html, height=900, scrolling=False)


if __name__ == "__main__":
    main()
