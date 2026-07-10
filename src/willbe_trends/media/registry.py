from willbe_trends.config import Settings
from willbe_trends.media.base import ImageGenerator, ShortVideoGenerator, VideoGenerator
from willbe_trends.media.diagnostics import is_image_generation_allowed
from willbe_trends.media.openai_images import OpenAIImageGenerator
from willbe_trends.media.openai_sora import OpenAISoraGenerator
from willbe_trends.media.openai_video import OpenAIVideoStoryboardGenerator


def create_image_generator(settings: Settings) -> ImageGenerator | None:
    if not is_image_generation_allowed(settings):
        return None
    if settings.willbe_image_generation_provider != "openai":
        return None
    if settings.openai_api_key:
        return OpenAIImageGenerator(settings)
    return None


def create_short_video_generator(settings: Settings) -> ShortVideoGenerator | None:
    if not is_image_generation_allowed(settings):
        return None
    if settings.willbe_video_generation_provider != "openai":
        return None
    if settings.openai_api_key:
        return OpenAISoraGenerator(settings)
    return None


def create_video_generator(settings: Settings) -> VideoGenerator | None:
    if not is_image_generation_allowed(settings):
        return None
    if settings.willbe_video_generation_provider != "openai":
        return None
    if settings.openai_api_key:
        return OpenAIVideoStoryboardGenerator(settings)
    return None
