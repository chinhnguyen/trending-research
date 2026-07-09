# Nails Trending Research Spec

## Goal

Deliver two complementary trend experiences for the nails vertical:

1. **Neutral trending** — objective, category-wide signals anyone can browse
2. **Personalized trending** — "You may like it" picks shaped by explicit user inputs

Both modes use the same underlying trend schema but different prompts and ranking logic.

## Web research

- Enabled by default (`WILLBE_WEB_SEARCH_ENABLED=true`)
- Search providers: `duckduckgo` (default), `tavily` (requires `TAVILY_API_KEY`), `google_trends` (requires Google Trends API alpha access)
- Google Trends is also listed in preferred sources (`trends.google.com`) and is fetched automatically when `GOOGLE_TRENDS_PROJECT_ID` and `GOOGLE_TRENDS_CREDENTIALS_PATH` are set
- Preferred sources: `config/preferred_sources.yaml` — editorial domains plus Google Trends
- Reports include `web_research` with queries, citations, and preferred-source flags
- Each trend includes a reference `image_url` from image search (DuckDuckGo by default)
- Disable images via `WILLBE_IMAGE_SEARCH_ENABLED=false`
- Disable via `--no-web-search` or `WILLBE_WEB_SEARCH_ENABLED=false`

## Modes

### Neutral trending

- Input: category (`nails`), optional region
- Output: 5–8 trends with popularity, colors, techniques, tags, confidence
- Tone: editorial, unbiased, no brand mentions
- Use case: homepage feed, editorial roundup, salon inspiration board

### Personalized trending

- Required inputs (v1):
  - `favorite_colors`
  - `preferred_shapes`
  - `preferred_finishes`
  - `style_keywords`
- Optional inputs:
  - `avoided_colors`
  - `preferred_lengths`
  - `occasion`
  - `budget`
  - `notes`
- Output: 4–6 tailored trends with fit rationale in summary and descriptions
- Use case: logged-in user home, post-quiz recommendations, push/email digest

## LLM requirements

- Provider must be switchable at runtime via env (`WILLBE_LLM_PROVIDER`) or CLI (`--provider`)
- Supported providers (v1): `openai`, `anthropic`, `ollama`
- Responses must be structured JSON validated against `TrendReport` / `TrendSignal`

## Data model

See `src/willbe_trends/models/trends.py` and `preferences.py`.

## CLI (v1)

```bash
willbe-trends neutral nails
willbe-trends neutral nails --no-web-search
willbe-trends neutral nails --sources config/preferred_sources.yaml
willbe-trends personalized nails --preferences samples/user_preferences.json
willbe-trends search-providers
willbe-trends providers
willbe-trends validate-preferences samples/user_preferences.json
```

## Future extensions

- Populate `config/preferred_sources.yaml` with editorial and social sources
- Web UI with preference quiz
- Trend caching and refresh intervals
- Image reference links per trend
- Additional categories: hair, makeup, skincare
- Multi-provider ensemble or fallback chain
- User feedback loop (thumbs up/down) to refine personalization

## Quality bar

- Trends should feel current and specific (not "try red nails")
- Personalized picks must honor avoided colors and stated constraints
- Fail loudly on invalid JSON or missing API keys
