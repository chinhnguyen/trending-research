---
name: nails-trend-research
description: Researches neutral and personalized nail trends using Willbe's switchable LLM pipeline. Use when working on nails trending, you-may-like-it recommendations, trend prompts, UserPreferences, or the willbe-trends CLI.
---

# Nails Trend Research

## When to use

Apply when implementing or extending nail trend research, personalization inputs, or LLM prompts for the Willbe trending project.

## Workflow

1. Read `specs/nails-trending.md` for product behavior
2. Update models in `src/willbe_trends/models/` if inputs/outputs change
3. Adjust prompts in `research/neutral.py` or `research/personalized.py`
4. Validate sample preferences: `willbe-trends validate-preferences samples/user_preferences.json`
5. Run a smoke test with the configured provider

## Neutral vs personalized

| Mode | Module | Prompt constant |
|------|--------|-----------------|
| Neutral | `research/neutral.py` | `NEUTRAL_SYSTEM_PROMPT` |
| Personalized | `research/personalized.py` | `PERSONALIZED_SYSTEM_PROMPT` |

Personalized mode must respect `avoided_colors` and optional constraints from `UserPreferences`.

## Required personalized inputs (v1)

- `favorite_colors`
- `preferred_shapes`
- `preferred_finishes`
- `style_keywords`

## Output schema

Both modes return JSON parsed into `TrendReport` with `TrendSignal` items. Do not change field names without updating Pydantic models and the spec.

## Testing changes

```bash
willbe-trends neutral nails --provider openai -o output/neutral.json
willbe-trends personalized nails -f samples/user_preferences.json -o output/personalized.json
```

Use `--provider ollama` for local iteration when API keys are unavailable.
