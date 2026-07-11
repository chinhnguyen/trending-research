"""Locale resolution for brief copy and generation."""

from __future__ import annotations

from willbe_trends.models.briefs import BriefCaption

SUPPORTED_LOCALES = frozenset({"en", "vi", "fi"})

LOCALE_NAMES = {
    "en": "English",
    "vi": "Vietnamese",
    "fi": "Finnish",
}

FALLBACK_CAPTIONS = {
    "en": "Show the trend with your latest salon work.",
    "vi": "Chia sẻ xu hướng này với bộ móng mới nhất của salon bạn.",
    "fi": "Näytä trendi uusimmalla salonkityölläsi.",
}


def normalize_locale(locale: str | None) -> str | None:
    if not locale:
        return None
    cleaned = locale.strip().lower().replace("_", "-").split("-")[0]
    return cleaned if cleaned in SUPPORTED_LOCALES else None


def locale_candidates(region: str, preferred_locale: str | None = None) -> list[str]:
    preferred = normalize_locale(preferred_locale)
    region_lower = region.lower()
    if preferred == "vi" or any(
        token in region_lower
        for token in ("viet", "vietnam", "hcm", "hanoi", "saigon", "ho chi minh")
    ) or region_lower in {"vn", "vi"}:
        locales = ["vi", "en"]
    elif preferred == "fi" or "fin" in region_lower:
        locales = ["fi", "en"]
    elif preferred == "en":
        locales = ["en"]
    else:
        locales = ["en"]
    if preferred and preferred not in locales:
        locales.insert(0, preferred)
    seen: set[str] = set()
    ordered: list[str] = []
    for item in locales:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def resolve_preferred_locale(region: str, preferred_locale: str | None = None) -> str:
    preferred = normalize_locale(preferred_locale)
    if preferred:
        return preferred
    candidates = locale_candidates(region)
    return candidates[0]


def caption_for_locale(captions: list[BriefCaption], preferred_locale: str) -> BriefCaption | None:
    preferred = normalize_locale(preferred_locale) or "en"
    for caption in captions:
        if normalize_locale(caption.locale) == preferred:
            return caption
    for caption in captions:
        if normalize_locale(caption.locale) == "en":
            return caption
    return captions[0] if captions else None


def fallback_caption(preferred_locale: str) -> BriefCaption:
    preferred = resolve_preferred_locale("", preferred_locale)
    return BriefCaption(
        locale=preferred,
        caption=FALLBACK_CAPTIONS.get(preferred, FALLBACK_CAPTIONS["en"]),
    )


SHELL_WHY_NOW = {
    "en": "Pick a platform and post type below, then generate your first option.",
    "vi": "Chọn nền tảng và loại bài đăng bên dưới, sau đó tạo lựa chọn đầu tiên.",
    "fi": "Valitse alusta ja julkaisutyyppi alta, sitten luo ensimmäinen vaihtoehto.",
}


def shell_why_now(preferred_locale: str) -> str:
    preferred = resolve_preferred_locale("", preferred_locale)
    return SHELL_WHY_NOW.get(preferred, SHELL_WHY_NOW["en"])


def research_locale_rules(preferred_locale: str) -> str:
    preferred = resolve_preferred_locale("", preferred_locale)
    if preferred != "vi":
        return ""
    return """Language rules (Vietnamese):
- Write summary and every trend name and description in Vietnamese.
- Keep JSON keys in English; all string values in Vietnamese.
- Use natural Vietnamese phrasing for salon owners in Vietnam — avoid literal translation from English.
- Color names and technique terms may stay in common international usage when natural (e.g. chrome, jelly)."""


def research_system_locale_rules(preferred_locale: str) -> str:
    preferred = resolve_preferred_locale("", preferred_locale)
    if preferred != "vi":
        return ""
    return """Output language: Vietnamese (vi).
- Write summary, trend names, descriptions, colors, techniques, and tags in Vietnamese.
- Keep JSON keys in English; string values in Vietnamese.
- Sound natural to Vietnamese salon owners — not word-for-word English translation."""


def media_prompt_language_rule(preferred_locale: str) -> str:
    preferred = resolve_preferred_locale("", preferred_locale)
    if preferred == "en":
        return ""
    preferred_name = LOCALE_NAMES.get(preferred, preferred)
    return (
        f"- Write the generation prompt in {preferred_name} ({preferred}). "
        "Describe nail art, hands, salon lighting, and composition clearly."
    )


def locale_rules(preferred_locale: str, locales: list[str]) -> str:
    preferred = resolve_preferred_locale("", preferred_locale)
    preferred_name = LOCALE_NAMES.get(preferred, preferred)
    locale_list = ", ".join(f"{code} ({LOCALE_NAMES.get(code, code)})" for code in locales)
    media_prompt_rule = (
        f"- Write image and video generation prompts in {preferred_name} ({preferred})."
        if preferred != "en"
        else "- Keep image/video generation prompts in English (visual description for the model)."
    )
    return f"""Language rules:
- Required locales for captions[]: {locale_list}. Return one captions[] entry per locale.
- Primary copy language: {preferred_name} ({preferred}).
- Write hook, caption, hashtags, platform_review, and per-option hook/caption/hashtags in {preferred_name}.
- For video scenes, write on_screen_text and voiceover in {preferred_name}.
{media_prompt_rule}
- Vietnamese copy must sound natural to salon owners in Vietnam — not literal translation."""
