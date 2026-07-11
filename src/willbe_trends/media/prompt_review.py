import json
from typing import Literal

from willbe_trends.briefs.locales import resolve_preferred_locale
from willbe_trends.briefs.prompts import media_copy_regenerate_system_prompt, media_prompt_regenerate_system_prompt
from willbe_trends.llm.base import LLMProvider
from willbe_trends.models.briefs import ContentIdea, ImageRecommendation, ShortVideoRecommendation

MediaOptionKind = Literal["image", "video"]
CopyFieldKind = Literal["hook", "caption", "hashtags"]
RegenerateFieldKind = Literal["prompt", "hook", "caption", "hashtags"]


def _find_image(idea: ContentIdea, sequence: int) -> ImageRecommendation | None:
    for item in idea.image_recommendations:
        if item.sequence == sequence:
            return item
    return None


def _find_video(idea: ContentIdea, sequence: int) -> ShortVideoRecommendation | None:
    for item in idea.video_recommendations:
        if item.sequence == sequence:
            return item
    return None


def _replace_image(idea: ContentIdea, sequence: int, updated: ImageRecommendation) -> ContentIdea:
    images = [
        updated if item.sequence == sequence else item for item in idea.image_recommendations
    ]
    return idea.model_copy(update={"image_recommendations": images})


def _replace_video(idea: ContentIdea, sequence: int, updated: ShortVideoRecommendation) -> ContentIdea:
    videos = [
        updated if item.sequence == sequence else item for item in idea.video_recommendations
    ]
    return idea.model_copy(update={"video_recommendations": videos})


def adjust_media_prompt(
    idea: ContentIdea,
    *,
    kind: MediaOptionKind,
    sequence: int,
    prompt: str,
    hook: str | None = None,
    caption: str | None = None,
    hashtags: list[str] | None = None,
) -> ContentIdea:
    cleaned = prompt.strip()
    if not cleaned:
        raise ValueError("Prompt cannot be empty")

    updates: dict = {"prompt": cleaned, "generation_status": "prompt_only"}
    if hook is not None:
        updates["hook"] = hook.strip() or None
    if caption is not None:
        cleaned_caption = caption.strip()
        if not cleaned_caption:
            raise ValueError("Caption cannot be empty")
        updates["caption"] = cleaned_caption
    if hashtags is not None:
        updates["hashtags"] = hashtags[:10]

    if kind == "image":
        current = _find_image(idea, sequence)
        if current is None:
            raise ValueError("Image option not found")
        if current.generation_status not in {"prompt_only", "cancelled", "failed", "generated"}:
            raise ValueError("This option is not awaiting prompt review")
        return _replace_image(idea, sequence, current.model_copy(update=updates))

    current = _find_video(idea, sequence)
    if current is None:
        raise ValueError("Video option not found")
    if current.generation_status not in {"prompt_only", "cancelled", "failed", "generated"}:
        raise ValueError("This option is not awaiting prompt review")
    return _replace_video(idea, sequence, current.model_copy(update=updates))


def cancel_media_prompt(
    idea: ContentIdea,
    *,
    kind: MediaOptionKind,
    sequence: int,
) -> ContentIdea:
    if kind == "image":
        current = _find_image(idea, sequence)
        if current is None:
            raise ValueError("Image option not found")
        return _replace_image(
            idea,
            sequence,
            current.model_copy(update={"generation_status": "cancelled"}),
        )

    current = _find_video(idea, sequence)
    if current is None:
        raise ValueError("Video option not found")
    return _replace_video(
        idea,
        sequence,
        current.model_copy(update={"generation_status": "cancelled"}),
    )


def accept_media_prompt(
    idea: ContentIdea,
    *,
    kind: MediaOptionKind,
    sequence: int,
) -> ContentIdea:
    if kind == "image":
        current = _find_image(idea, sequence)
        if current is None:
            raise ValueError("Image option not found")
        if current.generation_status not in {"prompt_only", "failed", "generated"}:
            raise ValueError("This option is not ready to generate")
        if not current.prompt.strip():
            raise ValueError("Prompt cannot be empty")
        return _replace_image(
            idea,
            sequence,
            current.model_copy(
                update={
                    "generation_status": "generating",
                    "generated_url": None,
                    "generation_error": None,
                }
            ),
        )

    current = _find_video(idea, sequence)
    if current is None:
        raise ValueError("Video option not found")
    if current.generation_status not in {"prompt_only", "failed", "generated"}:
        raise ValueError("This option is not ready to generate")
    if not current.prompt.strip():
        raise ValueError("Prompt cannot be empty")
    return _replace_video(
        idea,
        sequence,
        current.model_copy(
            update={
                "generation_status": "generating",
                "generated_url": None,
                "generation_error": None,
            }
        ),
    )


def reopen_media_prompt(
    idea: ContentIdea,
    *,
    kind: MediaOptionKind,
    sequence: int,
) -> ContentIdea:
    if kind == "image":
        current = _find_image(idea, sequence)
        if current is None:
            raise ValueError("Image option not found")
        return _replace_image(
            idea,
            sequence,
            current.model_copy(update={"generation_status": "prompt_only", "generation_error": None}),
        )

    current = _find_video(idea, sequence)
    if current is None:
        raise ValueError("Video option not found")
    return _replace_video(
        idea,
        sequence,
        current.model_copy(update={"generation_status": "prompt_only", "generation_error": None}),
    )


def _extract_json_payload(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


def _option_context(
    current: ImageRecommendation | ShortVideoRecommendation,
    *,
    trend_name: str,
    trend_description: str,
    region: str,
) -> str:
    lines = [
        f"Trend: {trend_name}",
        f"Description: {trend_description}",
        f"Region: {region}",
        f"Platform: {current.platform}",
        f"Aspect ratio: {current.aspect_ratio}",
        f"Hook: {current.hook or ''}",
        f"Caption: {current.caption or ''}",
        f"Hashtags: {', '.join(current.hashtags)}",
        f"Media prompt: {current.prompt}",
    ]
    if isinstance(current, ShortVideoRecommendation):
        lines.append(f"Duration seconds: {current.duration_seconds}")
    return "\n".join(lines)


def _apply_copy_field_update(
    current: ImageRecommendation | ShortVideoRecommendation,
    field: CopyFieldKind,
    payload: dict,
) -> ImageRecommendation | ShortVideoRecommendation:
    if field == "hook":
        hook = str(payload.get("hook", "")).strip()
        if not hook:
            raise ValueError("LLM did not return a hook")
        return current.model_copy(update={"hook": hook, "generation_status": "prompt_only", "generation_error": None})
    if field == "caption":
        caption = str(payload.get("caption", "")).strip()
        if not caption:
            raise ValueError("LLM did not return a caption")
        return current.model_copy(
            update={"caption": caption, "generation_status": "prompt_only", "generation_error": None}
        )
    hashtags = payload.get("hashtags") or []
    cleaned = [str(tag).strip() for tag in hashtags if str(tag).strip()]
    if not cleaned:
        raise ValueError("LLM did not return hashtags")
    return current.model_copy(
        update={"hashtags": cleaned[:10], "generation_status": "prompt_only", "generation_error": None}
    )


async def regenerate_option_field(
    *,
    llm: LLMProvider,
    idea: ContentIdea,
    kind: MediaOptionKind,
    sequence: int,
    field: RegenerateFieldKind,
    trend_name: str,
    trend_description: str,
    region: str,
    preferred_locale: str | None = None,
) -> ContentIdea:
    resolved_locale = resolve_preferred_locale(region, preferred_locale)
    if field == "prompt":
        return await regenerate_media_prompt(
            llm=llm,
            idea=idea,
            kind=kind,
            sequence=sequence,
            trend_name=trend_name,
            trend_description=trend_description,
            region=region,
            preferred_locale=resolved_locale,
        )

    if kind == "image":
        current = _find_image(idea, sequence)
        if current is None:
            raise ValueError("Image option not found")
        response = await llm.complete(
            system=media_copy_regenerate_system_prompt(
                field,
                platform=current.platform,
                preferred_locale=resolved_locale,
            ),
            user=(
                f"{_option_context(current, trend_name=trend_name, trend_description=trend_description, region=region)}\n"
                f"Return a fresh {field} as JSON."
            ),
        )
        payload = _extract_json_payload(response.content)
        updated = _apply_copy_field_update(current, field, payload)
        return _replace_image(idea, sequence, updated)

    current = _find_video(idea, sequence)
    if current is None:
        raise ValueError("Video option not found")
    response = await llm.complete(
        system=media_copy_regenerate_system_prompt(
            field,
            platform=current.platform,
            preferred_locale=resolved_locale,
        ),
        user=(
            f"{_option_context(current, trend_name=trend_name, trend_description=trend_description, region=region)}\n"
            f"Return a fresh {field} as JSON."
        ),
    )
    payload = _extract_json_payload(response.content)
    updated = _apply_copy_field_update(current, field, payload)
    return _replace_video(idea, sequence, updated)


async def regenerate_media_prompt(
    *,
    llm: LLMProvider,
    idea: ContentIdea,
    kind: MediaOptionKind,
    sequence: int,
    trend_name: str,
    trend_description: str,
    region: str,
    preferred_locale: str = "en",
) -> ContentIdea:
    from willbe_trends.briefs.locales import LOCALE_NAMES, resolve_preferred_locale

    resolved_locale = resolve_preferred_locale(region, preferred_locale)
    locale_name = LOCALE_NAMES.get(resolved_locale, resolved_locale)
    locale_hint = (
        f"\nWrite the generation prompt in {locale_name} ({resolved_locale})."
        if resolved_locale != "en"
        else ""
    )
    if kind == "image":
        current = _find_image(idea, sequence)
        if current is None:
            raise ValueError("Image option not found")
        response = await llm.complete(
            system=media_prompt_regenerate_system_prompt("image", preferred_locale=resolved_locale),
            user=(
                f"Trend: {trend_name}\n"
                f"Description: {trend_description}\n"
                f"Region: {region}\n"
                f"Platform: {current.platform}\n"
                f"Aspect ratio: {current.aspect_ratio}\n"
                f"Hook: {current.hook or ''}\n"
                f"Caption: {current.caption or ''}\n"
                f"Current prompt: {current.prompt}\n"
                f"Return a fresh image generation prompt as JSON.{locale_hint}"
            ),
        )
        payload = _extract_json_payload(response.content)
        new_prompt = str(payload.get("prompt", "")).strip()
        if not new_prompt:
            raise ValueError("LLM did not return a prompt")
        return _replace_image(
            idea,
            sequence,
            current.model_copy(
                update={
                    "prompt": new_prompt,
                    "generation_status": "prompt_only",
                    "generation_error": None,
                }
            ),
        )

    current = _find_video(idea, sequence)
    if current is None:
        raise ValueError("Video option not found")
    response = await llm.complete(
        system=media_prompt_regenerate_system_prompt("video", preferred_locale=resolved_locale),
        user=(
            f"Trend: {trend_name}\n"
            f"Description: {trend_description}\n"
            f"Region: {region}\n"
            f"Platform: {current.platform}\n"
            f"Aspect ratio: {current.aspect_ratio}\n"
            f"Duration seconds: {current.duration_seconds}\n"
            f"Hook: {current.hook or ''}\n"
            f"Caption: {current.caption or ''}\n"
            f"Current prompt: {current.prompt}\n"
            f"Return a fresh short-video generation prompt as JSON.{locale_hint}"
        ),
    )
    payload = _extract_json_payload(response.content)
    new_prompt = str(payload.get("prompt", "")).strip()
    if not new_prompt:
        raise ValueError("LLM did not return a prompt")
    return _replace_video(
        idea,
        sequence,
        current.model_copy(
            update={
                "prompt": new_prompt,
                "generation_status": "prompt_only",
                "generation_error": None,
            }
        ),
    )
