from willbe_trends.config import Settings
from willbe_trends.media.base import ImageGenerationResult, VideoGenerator
from willbe_trends.media.openai_images import OpenAIImageGenerator
from willbe_trends.models.briefs import VideoScene


class OpenAIVideoStoryboardGenerator(VideoGenerator):
    """Video synthesis via storyboard key frames until full video APIs are available."""

    name = "openai_storyboard"

    def __init__(self, settings: Settings) -> None:
        self._image_generator = OpenAIImageGenerator(settings)

    async def generate_scene_frame(
        self, *, scene: VideoScene, aspect_ratio: str = "9:16"
    ) -> ImageGenerationResult:
        prompt = scene.visual_prompt
        if scene.on_screen_text:
            prompt = f"{prompt}. On-screen text concept: {scene.on_screen_text}"
        return await self._image_generator.generate(prompt=prompt, aspect_ratio=aspect_ratio)
