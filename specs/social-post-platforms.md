# Social post platforms (Instagram & TikTok)

Product behavior for platform-specific post briefs and AI media recommendations.

## Supported platforms

| Platform | Formats | Media |
|----------|---------|-------|
| **Instagram** | Feed, carousel, Reels | 1:1 / 4:5 images; optional Reel storyboard |
| **TikTok** | Short-form vertical video | 9:16 storyboard scenes + key-frame images |

## Flow

1. User picks a trend on a saved report.
2. User selects **Instagram** or **TikTok** on the create-post page.
3. `POST /api/briefs/generate` with `{ report_id, trend_name, platform }`.
4. LLM returns:
   - **Platform review** — hook, caption, strengths, improvements, checklist
   - **Image recommendations** — labeled prompts with aspect ratio
   - **Video recommendation** — scenes with visual prompts (required for TikTok)
5. Media service optionally calls OpenAI image API for recommended prompts (see config).

## API

| Field | Values |
|-------|--------|
| `platform` | `instagram` \| `tiktok` |

Applies to `POST /api/briefs/generate` and `POST /api/ideas/generate`.

## Media generation

| Setting | Default | Purpose |
|---------|---------|---------|
| `WILLBE_MEDIA_GENERATION_ENABLED` | `true` | Master switch |
| `WILLBE_IMAGE_GENERATION_PROVIDER` | `openai` | DALL-E 3 images |
| `WILLBE_VIDEO_GENERATION_PROVIDER` | `openai` | Storyboard key frames via image API |
| `WILLBE_MEDIA_MAX_IMAGES_PER_POST` | `2` | Cost cap per post |
| `WILLBE_MEDIA_MAX_VIDEO_SCENES` | `2` | Key frames per video brief |
| `OPENAI_IMAGE_MODEL` | `dall-e-2` | Image model (`dall-e-2` or `dall-e-3`; auto-falls back to `dall-e-2`) |

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

Full video synthesis (not just key frames) is deferred until a video API is wired; TikTok briefs always include a scene-by-scene storyboard.

## Authenticity note

Salon owners should prefer **their own client work photos** when available. AI images are **inspiration and layout references**, not replacements for real salon portfolio shots. See market validation H5 in `projects/spa-market-validation/`.
