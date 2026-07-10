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
) -> ContentIdea:
    resolved = settings or get_settings()
    if not is_image_generation_allowed(resolved):
        await report_progress(on_progress, "Media generation is not configured", 100)
        return idea

    if idea.post_format == "video":
        return await _enrich_video_options(idea, settings=resolved, on_progress=on_progress)

    image_generator = create_image_generator(resolved)
    video_generator = create_video_generator(resolved)
    if image_generator is None and video_generator is None:
        await report_progress(on_progress, "No media generator available", 100)
        return idea

    await report_progress(on_progress, "Generating images…", 15)
    updated_images: list[ImageRecommendation] = []
    new_generations = 0
    pending = [
        recommendation
        for recommendation in idea.image_recommendations
        if not recommendation.generated_url
    ]
    for index, recommendation in enumerate(idea.image_recommendations):
        if recommendation.generated_url:
            updated_images.append(recommendation)
            continue
        if (
            image_generator is None
            or new_generations >= resolved.willbe_media_max_images_per_post
        ):
            updated_images.append(recommendation)
            continue
        new_generations += 1
        if pending:
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

    updated_video = idea.video_recommendation
    if updated_video and video_generator:
        updated_scenes: list[VideoScene] = []
        for index, scene in enumerate(updated_video.scenes):
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
        updated_video = updated_video.model_copy(update={"scenes": updated_scenes})

    await report_progress(on_progress, "Images ready", 100)
    return idea.model_copy(
        update={
            "image_recommendations": updated_images,
            "video_recommendation": updated_video,
        }
    )


async def _enrich_video_options(
    idea: ContentIdea,
    *,
    settings: Settings,
    on_progress: ProgressCallback | None = None,
) -> ContentIdea:
    video_generator = create_short_video_generator(settings)
    if video_generator is None:
        await report_progress(on_progress, "No video generator available", 100)
        return idea

    await report_progress(on_progress, "Starting video render…", 10)
    updated_videos: list[ShortVideoRecommendation] = []
    new_generations = 0
    for recommendation in idea.video_recommendations:
        if recommendation.generated_url:
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

    await report_progress(on_progress, "Video ready", 100)
    return idea.model_copy(update={"video_recommendations": updated_videos})
