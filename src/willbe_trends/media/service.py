from typing import Literal

from willbe_trends.config import Settings, get_settings
from willbe_trends.media.diagnostics import is_image_generation_allowed
from willbe_trends.media.progress import ProgressCallback, report_progress
from willbe_trends.media.registry import (
    create_image_generator,
    create_short_video_generator,
    create_video_generator,
)
from willbe_trends.media.storage import persist_generated_image, persist_generated_video
from willbe_trends.models.briefs import ContentIdea, ImageRecommendation, ShortVideoRecommendation, VideoScene


async def enrich_content_idea_media(
    idea: ContentIdea,
    *,
    settings: Settings | None = None,
    on_progress: ProgressCallback | None = None,
    target_kind: Literal["image", "video"] | None = None,
    target_sequence: int | None = None,
) -> ContentIdea:
    resolved = settings or get_settings()
    if not is_image_generation_allowed(resolved):
        await report_progress(on_progress, "Media generation is not configured", 100)
        return idea

    if target_kind in (None, "image"):
        idea = await _enrich_image_recommendations(
            idea,
            settings=resolved,
            on_progress=on_progress,
            target_sequence=target_sequence if target_kind == "image" else None,
        )
    if target_kind in (None, "video"):
        idea = await _enrich_video_recommendations(
            idea,
            settings=resolved,
            on_progress=on_progress,
            target_sequence=target_sequence if target_kind == "video" else None,
        )

    if target_kind is not None:
        await report_progress(on_progress, "Media ready", 100)
        return idea

    video_generator = create_video_generator(resolved)
    updated_storyboard = idea.video_recommendation
    if updated_storyboard and video_generator:
        updated_scenes: list[VideoScene] = []
        for index, scene in enumerate(updated_storyboard.scenes):
            if index >= resolved.willbe_media_max_video_scenes:
                updated_scenes.append(scene)
                continue
            result = await video_generator.generate_scene_frame(scene=scene)
            stored_frame = persist_generated_image(result.url)
            updated_scenes.append(
                scene.model_copy(
                    update={
                        "generated_frame_url": stored_frame,
                        "generation_status": "generated" if stored_frame else result.status,
                        "generation_provider": result.provider,
                        "generation_model": result.model,
                        "generation_error": result.error,
                    }
                )
            )
        updated_storyboard = updated_storyboard.model_copy(update={"scenes": updated_scenes})
        idea = idea.model_copy(update={"video_recommendation": updated_storyboard})

    await report_progress(on_progress, "Media ready", 100)
    return idea


async def _enrich_image_recommendations(
    idea: ContentIdea,
    *,
    settings: Settings,
    on_progress: ProgressCallback | None = None,
    target_sequence: int | None = None,
) -> ContentIdea:
    image_generator = create_image_generator(settings)
    if image_generator is None or not idea.image_recommendations:
        return idea

    pending = [
        item
        for item in idea.image_recommendations
        if not item.generated_url and item.generation_status == "generating"
        and (target_sequence is None or item.sequence == target_sequence)
    ]
    if not pending:
        return idea

    await report_progress(on_progress, "Generating image…", 15)
    updated_images: list[ImageRecommendation] = []
    new_generations = 0
    for recommendation in idea.image_recommendations:
        if recommendation.generated_url:
            updated_images.append(recommendation)
            continue
        if recommendation.generation_status != "generating":
            updated_images.append(recommendation)
            continue
        if target_sequence is not None and recommendation.sequence != target_sequence:
            updated_images.append(recommendation)
            continue
        if new_generations >= settings.willbe_media_max_images_per_post:
            updated_images.append(recommendation)
            continue
        new_generations += 1
        percent = 20 + int(new_generations / max(len(pending), 1) * 60)
        await report_progress(on_progress, "Generating image…", percent)
        result = await image_generator.generate(
            prompt=recommendation.prompt,
            aspect_ratio=recommendation.aspect_ratio,
        )
        stored_url = persist_generated_image(result.url)
        updated_images.append(
            recommendation.model_copy(
                update={
                    "generated_url": stored_url,
                    "generation_status": "generated" if stored_url else result.status,
                    "generation_provider": result.provider,
                    "generation_model": result.model,
                    "generation_error": result.error,
                }
            )
        )

    return idea.model_copy(update={"image_recommendations": updated_images})


async def _enrich_video_recommendations(
    idea: ContentIdea,
    *,
    settings: Settings,
    on_progress: ProgressCallback | None = None,
    target_sequence: int | None = None,
) -> ContentIdea:
    video_generator = create_short_video_generator(settings)
    if video_generator is None or not idea.video_recommendations:
        return idea

    pending = [
        item
        for item in idea.video_recommendations
        if not item.generated_url and item.generation_status == "generating"
        and (target_sequence is None or item.sequence == target_sequence)
    ]
    if not pending:
        return idea

    await report_progress(on_progress, "Starting video render…", 10)
    updated_videos: list[ShortVideoRecommendation] = []
    new_generations = 0
    for recommendation in idea.video_recommendations:
        if recommendation.generated_url:
            updated_videos.append(recommendation)
            continue
        if recommendation.generation_status != "generating":
            updated_videos.append(recommendation)
            continue
        if target_sequence is not None and recommendation.sequence != target_sequence:
            updated_videos.append(recommendation)
            continue
        if new_generations >= settings.willbe_media_max_videos_per_post:
            updated_videos.append(recommendation)
            continue
        new_generations += 1

        async def video_progress(stage: str, percent: int) -> None:
            mapped = 15 + int(percent * 0.8)
            await report_progress(on_progress, stage, mapped)

        result = await video_generator.generate(
            prompt=recommendation.prompt,
            aspect_ratio=recommendation.aspect_ratio,
            duration_seconds=recommendation.duration_seconds,
            on_progress=video_progress,
        )
        stored_url = persist_generated_video(result.data)
        updated_videos.append(
            recommendation.model_copy(
                update={
                    "generated_url": stored_url,
                    "generation_status": "generated" if stored_url else result.status,
                    "generation_provider": result.provider,
                    "generation_model": result.model,
                    "generation_error": result.error,
                }
            )
        )

    return idea.model_copy(update={"video_recommendations": updated_videos})
