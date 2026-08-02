# Smart Discovery Assistant

AI-powered **Cross Category Discovery** for Swiggy Instamart — increases cross-category penetration by recommending one highly relevant new category per session.

## Quick Start

```bash
# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env — set SURVEY_PDF_PATH to your survey PDF

# 4. Run the server
python run.py
```

Open **http://localhost:8000** for the recommendation card UI.  
API docs: **http://localhost:8000/docs**

## Survey PDF Setup

Store your 10-respondent survey PDF and point to it in `.env`:

```env
SURVEY_PDF_PATH=C:/path/to/your/survey_responses.pdf
```

Or place it at `data/survey/responses.pdf` (default).

## Grok LLM (Phase 2 — Optional)

Enable AI-generated explainability copy on recommendation cards:

```env
GROK_API_KEY=your_key_here
USE_LLM=true
GROK_MODEL=grok-2-latest
```

If `USE_LLM=false` or no key is set, rule-based templates are used automatically.

## Phase-wise Structure

| Phase | Timeline | Components |
|-------|----------|------------|
| **Phase 1** | Weeks 1–2 | Purchase history analyzer, recommendation engine, ML trainer |
| **Phase 2** | Weeks 3–4 | FastAPI, recommendation cards, explainability, frontend |
| **Phase 3** | Weeks 5–6 | A/B testing, analytics dashboard, feedback loop |
| **Phase 4** | Ongoing | K8s deployment, KPI monitoring, continuous learning |

See [docs/architecture.md](docs/architecture.md) for the full system diagram.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/survey/summary` | Survey insights from PDF |
| POST | `/api/v1/phase2/cards` | Full recommendation card (Phase 2) |
| POST | `/api/v1/recommendations` | Card + A/B split (legacy) |
| POST | `/api/v1/feedback` | Submit rating / purchase feedback |
| GET | `/api/v1/phase3/analytics/dashboard` | Full experiment dashboard |
| GET | `/api/v1/phase4/monitoring/status` | KPI alerts + SLA status |
| POST | `/api/v1/phase4/learning/retrain` | Trigger model retrain |
| GET | `/api/v1/analytics/kpis` | Success metrics (legacy) |
| GET | `/api/v1/analytics/ab-test` | A/B test results |
| GET | `/api/v1/phases` | Implementation roadmap status |

## Example Recommendation Request

```bash
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"user_001\"}"
```

## Project Layout

```
├── config/settings.py          # Env-based configuration
├── data/sample/                # Sample purchase history
├── docs/architecture.md        # Phase architecture
├── src/
│   ├── app/                    # FastAPI bootstrap
│   ├── phase1/                 # Recommendation engine
│   ├── phase2/                 # Cards, explainability, Grok LLM, frontend
│   ├── phase3/                 # A/B test + analytics
│   ├── phase4/                 # Production monitoring
│   └── shared/                 # Domain models + survey PDF parser
├── problemStatement.md         # PRD
└── run.py                      # Entry point
```

## KPI Targets (PRD)

- **Primary:** +15% Cross Category Purchase Rate
- **North Star:** % MAU buying ≥1 new category/month
