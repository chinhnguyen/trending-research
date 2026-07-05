# Research database schema

SQLite database (default `data/willbe.db`) stores normalized research results.

## Tables

### `research_reports`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID string | Primary key |
| `category` | string | e.g. `nails` |
| `mode` | string | `neutral` or `personalized` |
| `summary` | text | LLM overview |
| `region` | string | Request region |
| `research_time` | string | Time period researched, e.g. `July 2026` |
| `generated_at` | datetime | From report |
| `llm_provider` | string | openai / anthropic / ollama |
| `llm_model` | string | Model name |
| `web_search_enabled` | bool | Whether search ran |
| `web_search_provider` | string? | duckduckgo / tavily |
| `web_queries_json` | text? | JSON list of queries |
| `preferences_json` | text? | JSON user profile for personalized runs |
| `created_at` | datetime | Insert timestamp |

### `trend_signals`

One row per trend in a report.

| Column | Type |
|--------|------|
| `report_id` | FK → research_reports |
| `position` | int |
| `name`, `description`, `popularity`, `source_hint` | text |
| `colors_json`, `techniques_json`, `tags_json` | JSON arrays |
| `confidence` | float |
| `image_url` | text? | Reference photo illustrating the trend |
| `image_source_url` | text? | Page where the image was found |
| `image_alt` | text? | Accessible alt text |

### `web_citations`

One row per web source attached to a report.

| Column | Type |
|--------|------|
| `report_id` | FK → research_reports |
| `position` | int |
| `title`, `url`, `snippet`, `query` | text |
| `preferred` | bool |
| `source_name` | string? |

## API

- `GET /api/research` — paginated list
- `GET /api/research/{id}` — full report with trends + citations
- `POST /api/research/neutral` — run + persist
- `POST /api/research/personalized` — run + persist

## Web UI

React app in `web/` reads from these endpoints and renders list + detail views.
