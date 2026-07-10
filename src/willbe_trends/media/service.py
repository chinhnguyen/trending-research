from willbe_trends.config import Settings, get_settings
from willbe_trends.media.diagnostics import is_image_generation_allowed
from willbe_trends.media.registry import create_image_generator, create_video_generator
from willbe_trends.media.storage import persist_generated_image
from willbe_trends.models.briefs import ContentIdea, ImageRecommendation, VideoScene


async def enrich_content_idea_media(
    idea: ContentIdea,
    *,
    settings: Settings | None = None,
) -> ContentIdea:
    resolved = settings or get_settings()
    if not is_image_generation_allowed(resolved):
        return idea

    image_generator = create_image_generator(resolved)
    video_generator = create_video_generator(resolved)
    if image_generator is None and video_generator is None:
        return idea

    updated_images: list[ImageRecommendation] = []
    new_generations = 0
    for recommendation in idea.image_recommendations:
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

    return idea.model_copy(
        update={
            "image_recommendations": updated_images,
            "video_recommendation": updated_video,
        }
    )
