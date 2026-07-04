# Willbe Trending Research

AI-powered trending research for beauty categories, starting with nails.

## Features

- **Neutral trending** — broad, category-wide trend signals without user bias
- **Personalized trending** — "You may like it" recommendations from user preferences
- **Switchable LLM** — OpenAI, Anthropic, or local Ollama via config or CLI flag

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

## Project layout

```
specs/                  Product and research specs
samples/                Sample user preference inputs
src/willbe_trends/      Python package
  llm/                  Switchable LLM providers
  research/             Neutral and personalized research
.cursor/rules/          Cursor agent rules
.cursor/skills/         Domain skills for trend research
```

## Configuration

Set `WILLBE_LLM_PROVIDER` in `.env` or pass `--provider` on the CLI. Provider-specific keys and models are documented in `.env.example`.

See `specs/nails-trending.md` for the nails vertical spec.
