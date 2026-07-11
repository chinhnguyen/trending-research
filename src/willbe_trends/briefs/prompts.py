from willbe_trends.models.social import SocialPlatform

_IMAGE_JSON_SHAPE = """
  "platform_review": {
    "content_format": "instagram_reel | instagram_feed | tiktok_video",
    "strengths": ["what works for this platform"],
    "improvements": ["what to tweak before posting"],
    "hook": "opening line or first-frame hook",
    "caption": "platform-ready caption",
    "hashtags": ["#tag"],
    "posting_checklist": ["checklist item"],
    "sound_strategy": "optional string or null",
    "cover_tip": "optional string or null"
  },
  "image_recommendations": [
    {
      "label": "Feed hero | Reel cover | Carousel slide",
      "aspect_ratio": "1:1 | 4:5 | 9:16",
      "prompt": "detailed AI image prompt grounded in the trend",
      "hook": "opening line for this specific post variant",
      "caption": "platform-ready caption for this specific post variant",
      "hashtags": ["#tag"]
    }
  ],
  "video_recommendations": [],
  "video_recommendation": null"""

_VIDEO_JSON_SHAPE = """
  "platform_review": {
    "content_format": "instagram_reel | tiktok_video",
    "strengths": ["what works for this platform"],
    "improvements": ["what to tweak before posting"],
    "hook": "opening line or first-frame hook",
    "caption": "platform-ready caption",
    "hashtags": ["#tag"],
    "posting_checklist": ["checklist item"],
    "sound_strategy": "optional string or null",
    "cover_tip": "optional string or null"
  },
  "image_recommendations": [],
  "video_recommendations": [
    {
      "label": "Reel clip | TikTok clip",
      "aspect_ratio": "9:16",
      "prompt": "detailed AI short-video prompt grounded in the trend",
      "duration_seconds": 8,
      "hook": "opening line for this specific post variant",
      "caption": "platform-ready caption for this specific post variant",
      "hashtags": ["#tag"],
      "scenes": [
        {
          "scene_number": 1,
          "duration_seconds": 3,
          "visual_prompt": "shot description for the clip",
          "on_screen_text": "optional overlay text",
          "voiceover": "optional spoken line"
        }
      ]
    }
  ],
  "video_recommendation": {
    "hook": "first 3 seconds hook",
    "total_duration_seconds": 8,
    "music_mood": "optional trending sound mood",
    "scenes": []
  }"""


_INSTAGRAM_IMAGE_RULES = """
Platform: Instagram
- Optimize for feed (1:1 or 4:5), Reels (9:16), or carousel.
- Lead with a scroll-stopping first line; keep captions scannable with line breaks.
- Use 5-10 hashtags: mix broad nail tags, niche trend tags, and 1-2 local tags.
- Return exactly ONE image_recommendation object with its own hook, caption, hashtags, and prompt.
- Set video_recommendations to [] and video_recommendation to null.
- cover_tip should describe the Reel thumbnail frame when relevant.
- sound_strategy may suggest trending Reels audio style."""

_INSTAGRAM_VIDEO_RULES = """
Platform: Instagram Reels
- Optimize for vertical 9:16 short-form video (4-12 seconds).
- Hook must land in the first 1-3 seconds; write punchy on-screen text.
- Use 5-10 hashtags: mix broad nail tags, niche trend tags, and 1-2 local tags.
- Return exactly ONE video_recommendations object with hook, caption, hashtags, prompt, and 2-4 scenes.
- Set image_recommendations to [].
- platform_review.content_format must be instagram_reel.
- sound_strategy should suggest trending Reels audio style."""

_TIKTOK_IMAGE_RULES = """
Platform: TikTok
- Optimize for vertical 9:16 short-form video discovery copy even when generating a still.
- Hook must land in the first 1-3 seconds; write punchy on-screen text.
- Use 3-5 hashtags focused on discovery (#nailtok, trend tags).
- Return exactly ONE image_recommendation object (9:16) with its own hook, caption, hashtags, and prompt.
- Set video_recommendations to []."""

_TIKTOK_VIDEO_RULES = """
Platform: TikTok
- Optimize for vertical 9:16 short-form video (4-12 seconds).
- Hook must land in the first 1-3 seconds; write punchy on-screen text.
- Use 3-5 hashtags focused on discovery (#nailtok, trend tags).
- Return exactly ONE video_recommendations object with hook, caption, hashtags, prompt, and 3-5 scenes.
- Set image_recommendations to [].
- platform_review.content_format must be tiktok_video.
- sound_strategy should suggest trending sound type or original audio approach."""


def platform_brief_system_prompt(
    platform: SocialPlatform,
    post_format: str = "image",
    *,
    locale_rules_text: str = "",
) -> str:
    if platform == "instagram":
        platform_rules = _INSTAGRAM_VIDEO_RULES if post_format == "video" else _INSTAGRAM_IMAGE_RULES
    else:
        platform_rules = _TIKTOK_VIDEO_RULES if post_format == "video" else _TIKTOK_IMAGE_RULES

    media_shape = _VIDEO_JSON_SHAPE if post_format == "video" else _IMAGE_JSON_SHAPE
    media_rule = (
        "video_recommendations must contain exactly one short-video variant with unique hook, caption, hashtags, prompt, and scenes."
        if post_format == "video"
        else "image_recommendations must contain exactly one post variant with unique hook, caption, hashtags, and prompt."
    )

    locale_block = f"\n{locale_rules_text}\n" if locale_rules_text else ""

    return f"""You are a beauty trend strategist helping salon owners turn evidence-backed trends into a platform-specific social post brief.
Return ONLY valid JSON with this shape:
{{
  "evidence_summary": "2-3 sentences grounded in the supplied report and citations",
  "why_now": "1-2 sentences explaining timing and relevance",
  "caveats": "optional string or null",
  "angles": ["angle 1", "angle 2", "angle 3"],
  "captions": [
    {{"locale": "en", "caption": "string", "cta": "optional string"}}
  ],
  "hashtags": ["#tag"],
  "posting_tip": "short practical posting suggestion",
  "service_suggestion": "service or offer to promote",
  "product_suggestion": "optional retail or treatment tie-in",
  "rationale": "why the suggestion fits this trend",
{media_shape}
}}
{platform_rules}
{locale_block}Rules:
- Ground every claim in the provided report trend and citations.
- Do not invent statistics or unsupported sources.
- Captions should sound warm, concise, and human.
- Image and video prompts must describe salon nail art — never faces without consent.
- {media_rule}
- platform_review should mirror that same variant for strengths, improvements, and checklist."""


def media_prompt_regenerate_system_prompt(kind: str, *, preferred_locale: str = "en") -> str:
    from willbe_trends.briefs.locales import media_prompt_language_rule

    media_label = "short vertical salon nail video" if kind == "video" else "salon nail still image"
    language_rule = media_prompt_language_rule(preferred_locale)
    return f"""You rewrite AI media prompts for beauty salon social posts.
Return ONLY valid JSON:
{{
  "prompt": "detailed generation prompt for a {media_label}"
}}
Rules:
- Ground the visual in the supplied trend, hook, and caption.
- Describe nail art, hands, salon lighting, and composition — avoid identifiable faces.
- Keep prompts concrete and production-ready for an image or video model.
{language_rule}
- Do not return markdown or commentary."""


def media_copy_regenerate_system_prompt(field: str, *, platform: str, preferred_locale: str = "en") -> str:
    from willbe_trends.briefs.locales import LOCALE_NAMES, resolve_preferred_locale

    shapes = {
        "hook": '{"hook": "opening line or first-frame hook"}',
        "caption": '{"caption": "platform-ready caption"}',
        "hashtags": '{"hashtags": ["#tag"]}',
    }
    shape = shapes[field]
    preferred = resolve_preferred_locale("", preferred_locale)
    language_name = LOCALE_NAMES.get(preferred, preferred)
    language_rule = (
        f"- Write the {field} in {language_name} ({preferred})."
        if preferred != "en"
        else ""
    )
    return f"""You rewrite one part of a salon social post for {platform}.
Return ONLY valid JSON:
{shape}
Rules:
- Ground the copy in the supplied trend and post context.
- Sound warm, concise, and human — like a real salon owner posting.
- For hashtags, return 3-6 discovery-friendly tags with # prefix.
{language_rule}
- Do not return markdown or commentary."""
