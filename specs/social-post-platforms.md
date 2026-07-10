# Social post platforms (Instagram & TikTok)

Product behavior for platform-specific post briefs and AI media recommendations.

## Supported platforms

| Platform | Formats | Media |
|----------|---------|-------|
| **Instagram** | Feed, carousel, Reels | 1:1 / 4:5 images or 9:16 short video |
| **TikTok** | Short-form vertical video | 9:16 short video clips |

## Flow

1. User picks a trend on a saved report.
2. User selects **Instagram** or **TikTok** on the create-post page.
3. User selects **Image post** or **Short video**.
4. `POST /api/briefs/generate` with `{ report_id, trend_name, platform, post_format }`.
4. LLM returns:
   - **Platform review** — hook, caption, strengths, improvements, checklist
   - **Image recommendations** — labeled prompts with aspect ratio
   - **Video recommendation** — scenes with visual prompts (required for TikTok)
5. Media service optionally calls OpenAI image API for recommended prompts (see config).

## API

| Field | Values |
|-------|--------|
| `platform` | `instagram` \| `tiktok` |
| `post_format` | `image` \| `video` |

Applies to `POST /api/briefs/generate` and `POST /api/ideas/generate`.

## Media generation

| Setting | Default | Purpose |
|---------|---------|---------|
| `WILLBE_MEDIA_GENERATION_ENABLED` | `true` | Master switch |
| `WILLBE_IMAGE_GENERATION_PROVIDER` | `openai` | DALL-E 3 images |
| `WILLBE_VIDEO_GENERATION_PROVIDER` | `openai` | Storyboard key frames via image API |
| `WILLBE_MEDIA_MAX_IMAGES_PER_POST` | `1` | Cost cap per image post |
| `WILLBE_MEDIA_MAX_VIDEOS_PER_POST` | `1` | Cost cap per video post |
| `WILLBE_MEDIA_MAX_VIDEO_SCENES` | `2` | Key frames per storyboard |
| `OPENAI_IMAGE_MODEL` | `gpt-image-1-mini` | Image model |
| `OPENAI_VIDEO_MODEL` | `sora-2` | Short video model (`sora-2` or `sora-2-pro`) |

Without `OPENAI_API_KEY`, prompts are returned with `generation_status: prompt_only`.

## Instagram posting (browser)

Instagram does not let third-party sites open a pre-filled post composer in the browser (unlike X/Twitter intent URLs). There is no supported way to pass caption + image into instagram.com without Meta's Graph API and a developer app.

The UI **Post on Instagram** button instead:

1. Copies the full caption (hook + body + hashtags) to the clipboard
2. Downloads the generated image when available
3. Opens [instagram.com/create/select/](https://www.instagram.com/create/select/) in a new tab

On mobile, it uses the native **Share** sheet when the browser supports sharing image + text, so the user can pick Instagram directly.

The user still taps **Share** in Instagram — but they skip manual copy/paste and file hunting.

TikTok posts still use copy-to-clipboard.

**Before enabling:** run `willbe-trends test-image-gen --enable` (see [image generation](image-generation.md)). DALL-E models were removed from the OpenAI API in May 2026; use GPT Image models (`gpt-image-1-mini`, etc.).

Full video synthesis uses the OpenAI **Sora** API (`POST /v1/videos`) when `post_format=video` and media generation is enabled. Clips are generated at 9:16 (720×1280) for 4–12 seconds by default. Storyboard key frames still render for image posts when a `video_recommendation` is present.

## Background media jobs

Caption/copy generation returns immediately. Image and video rendering run in a **background job** stored in SQLite (`media_generation_jobs`). The API exposes:

- `active_media_jobs` on `GET /api/briefs/{id}` while work is in progress
- `active_media_job` on `POST /api/ideas/generate` after regenerate
- `GET /api/media-jobs/{id}` for polling status, stage text, and `progress_percent`

Jobs survive page reloads and server restarts (pending jobs resume on API startup). Sora poll progress is forwarded when the OpenAI job reports a percentage.

## Authenticity note

Salon owners should prefer **their own client work photos** when available. AI images are **inspiration and layout references**, not replacements for real salon portfolio shots. See market validation H5 in `projects/spa-market-validation/`.
