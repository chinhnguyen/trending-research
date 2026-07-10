# Image generation probe

Run this **before** enabling AI images in post briefs:

```bash
# 1. Set OPENAI_API_KEY in .env
# 2. Probe the GPT Image API (DALL-E was removed May 2026)
willbe-trends test-image-gen --enable

# 3. Enable in .env
WILLBE_MEDIA_GENERATION_ENABLED=true
WILLBE_MEDIA_REQUIRE_PROBE=true   # blocks brief images until probe passes
OPENAI_IMAGE_MODEL=gpt-image-1-mini
```

## Automated integration test

```bash
OPENAI_API_KEY=sk-... pytest -m integration tests/test_media_integration.py -q
```

## Models

| Model | Notes |
|-------|-------|
| `gpt-image-1-mini` | Default — cheapest |
| `gpt-image-1` | Higher quality |
| `gpt-image-1.5` | Previous flagship |
| `gpt-image-2` | Latest flagship |

The generator tries your configured model, then falls back through the GPT Image lineup.

GPT Image models return **base64 PNG** (shown as `data:image/png;base64,...` in the UI), not hosted URLs.

## Post brief behavior

- `WILLBE_MEDIA_GENERATION_ENABLED=false` — prompts only, no API calls (default)
- `WILLBE_MEDIA_GENERATION_ENABLED=true` + probe passed — generates images in create-post flow
- Failed generation never blocks the brief; prompts remain for owner photos
