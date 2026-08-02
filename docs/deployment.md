# BasketPilot — Deployment Guide

This guide covers how to run and deploy the **Smart Discovery Assistant** (BasketPilot) demo locally and on **Streamlit Community Cloud**.

| Mode | Command | URL | Best for |
|------|---------|-----|----------|
| **Full Web UI** | `python run.py` | http://localhost:8000 | Local demo, full UX (search, qty controls, bottom nav) |
| **Streamlit** | `streamlit run streamlit_app.py` | http://localhost:8501 | Assignment deployment, Streamlit Cloud |

See [architecture.md §16](architecture.md#16-deployment-architecture) for system topology and design rationale.

---

## 1. Prerequisites

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

python -m pip install -r requirements.txt
copy .env.example .env          # Windows
# cp .env.example .env          # macOS/Linux
```

Optional environment variables (`.env` or Streamlit Secrets):

| Variable | Default | Purpose |
|----------|---------|---------|
| `SURVEY_PDF_PATH` | `data/survey/responses.pdf` | Survey PDF for category priors (falls back to PRD defaults if missing) |
| `GROK_API_KEY` | — | Optional Grok LLM explainability |
| `USE_LLM` | `false` | Enable/disable Grok calls |
| `GROK_MODEL` | `grok-2-latest` | Grok model name |
| `APP_ENV` | `development` | Environment label in `/health` |

---

## 2. Full Web UI (FastAPI + static frontend)

Recommended for local development and stakeholder demos with the complete BasketPilot experience.

```bash
python run.py
```

| Resource | URL |
|----------|-----|
| Demo UI | http://localhost:8000 |
| OpenAPI docs | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

### UI features (web frontend)

- **Bottom tab bar:** Home · Discover · Checkout · Insights (single row, fixed at bottom)
- **Compact usual picks:** scrollable framed grid on Home
- **AI Discovery Pick:** hero card with one-click add
- **Search:** tap results to add directly to cart
- **Checkout flow:** combined habit + AI cart, post-purchase rating
- **No dev links** in the production demo UI (`/ui/test.html` remains available for API testing only)

Frontend assets: `src/phase2/frontend/` (`index.html`, `app.js`, `styles.css`).

---

## 3. Streamlit deployment (Community Cloud compatible)

```bash
streamlit run streamlit_app.py
```

Open http://localhost:8501.

### How it works

`streamlit_app.py` embeds the **same web UI** as `python run.py` (`index.html`, `app.js`, `styles.css`) via `st.components.v1.html`, with:

- **Bottom tab bar**, compact usual-picks frame, search, checkout flow (identical to the FastAPI demo)
- Recommendation data **preloaded in-process** via Starlette `TestClient` → injected as `window.__INITIAL_CARDS__`
- **No browser call to `127.0.0.1:8000`** (avoids Streamlit Cloud connection failures)

| Layer | Implementation |
|-------|----------------|
| UI | Full BasketPilot frontend inlined in Streamlit component iframe |
| API | TestClient loads cards at startup; cart/search/checkout run client-side in JS |
| Feedback API | Skipped in Streamlit embed mode (demo UX unchanged) |
| Secrets | `.streamlit/secrets.toml` locally · Streamlit Cloud dashboard in production |

### Streamlit config

| File | Purpose |
|------|---------|
| `streamlit_app.py` | Entry point — session state, cart, API client |
| `.streamlit/config.toml` | BasketPilot theme, wide layout, minimal toolbar |
| `.streamlit/secrets.toml.example` | Template for local secrets (copy to `secrets.toml`, gitignored) |

Example local secrets (`.streamlit/secrets.toml`):

```toml
GROK_API_KEY = ""
USE_LLM = "false"
GROK_MODEL = "grok-2-latest"
SURVEY_PDF_PATH = "data/survey/responses.pdf"
APP_ENV = "production"
```

---

## 4. Streamlit Community Cloud

| Step | Action |
|------|--------|
| 1 | Push this repository to GitHub |
| 2 | Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo |
| 3 | Set **Main file path** to `streamlit_app.py` |
| 4 | Add secrets (same keys as `.streamlit/secrets.toml.example`) |
| 5 | Deploy — no separate FastAPI host required for the MVP |

**Note:** For the Cloud MVP, you do **not** need `API_BASE_URL` or a background Uvicorn process. The engine runs in-process.

For the **full web UI** with search and bottom navigation, run `python run.py` on a host that exposes port 8000 (local machine, VM, or container).

---

## 5. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| **Connection failure** on Streamlit Cloud | Old iframe → `localhost:8000` pattern | Use current `streamlit_app.py` (in-process TestClient) |
| `ModuleNotFoundError: joblib` | Dependencies not installed | `python -m pip install -r requirements.txt` |
| No recommendation card | Backend error | Check `/health`; ensure sample data loads (`user_001`) |
| Survey PDF missing | File not present | Add PDF or rely on built-in PRD defaults |
| Port 8000 in use | Another process | Stop conflicting service or change port in `run.py` |

---

## 6. Optional production scale-out

Phase 4 includes Kubernetes manifests and Docker scaffolding (`src/phase4/deployment/`, `Dockerfile`) for split FastAPI + observability deployments. This path is **optional** and not required for the Streamlit MVP assignment demo.

| Service | Suggested host | Port |
|---------|----------------|------|
| FastAPI (full web UI) | Render / Railway / Fly.io / EC2 | 8000 |
| Streamlit | Streamlit Community Cloud | 8501 |

When splitting services, host FastAPI publicly and point any external API clients at that URL. The current Streamlit MVP does not require this split.

---

## 7. Verify deployment

```bash
# Health check
curl http://localhost:8000/health

# Recommendation card
curl -X POST http://localhost:8000/api/v1/phase2/cards \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"user_001\"}"

# Run tests
pytest tests/ -q
```

---

*Last updated: August 2026 — aligns with BasketPilot web UI (bottom nav, compact picks) and Streamlit Cloud in-process deployment.*
