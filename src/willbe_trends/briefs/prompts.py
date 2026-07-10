from willbe_trends.models.social import SocialPlatform

_PLATFORM_JSON_SHAPE = """
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
  "video_recommendation": {
    "hook": "first 3 seconds hook",
    "total_duration_seconds": 15,
    "music_mood": "optional trending sound mood",
    "scenes": [
      {
        "scene_number": 1,
        "duration_seconds": 3,
        "visual_prompt": "shot description for AI video/image frame",
        "on_screen_text": "optional overlay text",
        "voiceover": "optional spoken line"
      }
    ]
  }"""


_INSTAGRAM_RULES = """
Platform: Instagram
- Optimize for feed (1:1 or 4:5), Reels (9:16), or carousel.
- Lead with a scroll-stopping first line; keep captions scannable with line breaks.
- Use 5-10 hashtags: mix broad nail tags, niche trend tags, and 1-2 local tags.
- Return exactly ONE image_recommendation object with its own hook, caption, hashtags, and prompt.
- A Reel storyboard is optional when relevant.
- cover_tip should describe the Reel thumbnail frame.
- sound_strategy may suggest trending Reels audio style."""


_TIKTOK_RULES = """
Platform: TikTok
- Optimize for vertical 9:16 short-form video (15-30 seconds).
- Hook must land in the first 1-3 seconds; write punchy on-screen text.
- Use 3-5 hashtags focused on discovery (#nailtok, trend tags).
- Return exactly ONE image_recommendation object (9:16) with its own hook, caption, hashtags, and prompt.
- Always include video_recommendation with 3-5 scenes and duration per scene.
- sound_strategy should suggest trending sound type or original audio approach."""


def platform_brief_system_prompt(platform: SocialPlatform) -> str:
    platform_rules = _INSTAGRAM_RULES if platform == "instagram" else _TIKTOK_RULES
    video_note = (
        "Set video_recommendation to null for instagram_feed-only posts."
        if platform == "instagram"
        else "video_recommendation is required for TikTok."
    )
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
{_PLATFORM_JSON_SHAPE}
}}
{platform_rules}
Rules:
- Ground every claim in the provided report trend and citations.
- Do not invent statistics or unsupported sources.
- Captions should sound warm, concise, and human.
- Image and video prompts must describe salon nail art — never faces without consent.
- {video_note}
- image_recommendations must contain exactly one post variant with unique hook, caption, hashtags, and prompt.
- platform_review should mirror that same variant for strengths, improvements, and checklist."""
