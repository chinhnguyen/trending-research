# Willbe Trending Research

AI-powered trending research for beauty categories, starting with nails.

## Features

- **Neutral trending** — broad, category-wide trend signals without user bias
- **Personalized trending** — "You may like it" recommendations from user preferences
- **Switchable LLM** — OpenAI, Anthropic, or local Ollama via config or CLI flag
- **Web-backed research** — DuckDuckGo or Tavily search with pluggable preferred sources

## Quick start

```bash
cd /Users/chinhnguyen/Documents/Willbe/trending-research
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Add your API key, then:
```

### Neutral nails trends

```bash
willbe-trends neutral nails
willbe-trends neutral nails --provider anthropic
willbe-trends neutral nails --no-web-search
willbe-trends search-providers
```

### Personalized "you may like it"

```bash
willbe-trends personalized nails --preferences samples/user_preferences.json
willbe-trends personalized nails --provider ollama
```

### List providers

```bash
willbe-trends providers
```

## Market validation

Customer discovery for nail salon owners (Vietnam, Finland, international) lives in [`projects/spa-market-validation/`](projects/spa-market-validation/README.md) — interview guides, recruitment tracker, and synthesis outcomes.

## Project layout

```
projects/               Market validation programs and task tracking
specs/                  Product and research specs
samples/                Sample user preference inputs
src/willbe_trends/      Python package
  llm/                  Switchable LLM providers
  search/               Web search + preferred sources ranking
  research/             Neutral and personalized research
config/
  preferred_sources.yaml  Trusted domains (empty until configured)
.cursor/rules/          Cursor agent rules
.cursor/skills/         Domain skills for trend research
```

## Configuration

Set `WILLBE_LLM_PROVIDER` in `.env` or pass `--provider` on the CLI. Provider-specific keys and models are documented in `.env.example`.

See `specs/nails-trending.md` for the nails vertical spec.

## Web app

### Backend API

```bash
source .venv/bin/activate
willbe-api
# API at http://127.0.0.1:8000
```

### React frontend

```bash
cd web
npm install
npm run dev
# UI at http://127.0.0.1:5173
```

The Vite dev server proxies `/api` to the FastAPI backend. Research runs are saved to SQLite (`data/willbe.db`) and shown in the UI.

See `specs/database.md` for the persistence schema.

## AWS deployment

A Pulumi AWS deployment lives in `infra/`. It provisions:

- ECR for the image
- ECS Fargate for the app
- ALB for public access
- EFS for persistent SQLite and editable prompt/source config
- CloudWatch Logs and Secrets Manager wiring

See `infra/README.md` for setup and deploy steps.
