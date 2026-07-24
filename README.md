# ContentForge AI Agent

AI-powered content creation platform that turns prompts, documents, and images into
platform-optimized content packages using **external AI APIs only** (no local model
deployment).

## What it does

1. Choose a target platform (LinkedIn, X/Twitter, Blog, Medium, YouTube Community, Custom)
2. Provide a prompt and optional PDF/DOCX/TXT/Markdown/CSV + JPG/PNG/SVG attachments
3. Run the multi-agent pipeline:

```
User Input → Document/Image Understanding → Planner → Writer
         → Evaluators → Optimization loop → Banner → Final Package
```

### Evaluation gates

- Originality score ≥ 90%
- Relevance score ≥ 90%
- Expertise scored for intermediate–advanced depth

## Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2, PostgreSQL 17, Redis 8, Celery |
| Frontend | TypeScript, React 19, Next.js 16, Tailwind CSS, TanStack Query, Zustand |
| Packaging | Poetry |
| Ops | Docker Compose, Prometheus, Grafana, OpenTelemetry hooks, GitHub Actions CI |

## Quick start

### Prerequisites

- Python 3.12+
- Poetry
- Node.js 22+
- Docker (optional, for Postgres/Redis/MinIO)

```bash
cp .env.example .env
poetry install --with dev
make docker-up   # or run Postgres/Redis yourself
make migrate     # optional if using Alembic; API also auto-creates tables in non-test env
make dev         # API on :8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev      # UI on :3000
```

Default admin (from `.env`):

- Email: `admin@contentforge.local`
- Password: `changeme`

Set `USE_MOCK_AI=true` (default) to exercise the full pipeline without API keys.
Provide `LLM_API_KEY` / related keys and set `USE_MOCK_AI=false` for live external APIs.

## API surface

- `POST /api/v1/auth/register|login`
- `POST /api/v1/assets/documents|images`
- `GET  /api/v1/platforms`
- `POST /api/v1/content/jobs` — generate package
- `POST /api/v1/content/jobs/{id}/improve`
- `GET  /health`, `/metrics`

## Project layout

```
backend/
  agents/       # Planner, Writer, Evaluators, Optimizer, Banner pipeline
  api/          # FastAPI routes + schemas
  core/         # Settings, security, telemetry
  services/     # AI client, docs/images, storage, content orchestration
  workers/      # Celery tasks
frontend/       # Next.js studio UI
infrastructure/ # Docker + Prometheus
```

## Quality

```bash
make quality     # ruff + mypy + pytest + bandit
cd frontend && npm run build
```

## Roadmap

See [`PROJECT_PROGRESS.md`](./PROJECT_PROGRESS.md) for Phases 1–7 including calendar,
A/B testing, publishing integrations, analytics feedback, and enterprise features.

Phase 1–5 foundations implemented in this repo: auth, assets, multi-agent generation,
evaluation loop, banner generation stubs, Docker/CI, and studio UI.
