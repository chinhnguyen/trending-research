from abc import ABC, abstractmethod
from dataclasses import dataclass

from willbe_trends.models.briefs import ImageRecommendation, VideoScene


@dataclass(frozen=True)
class ImageGenerationResult:
    url: str | None
    provider: str
    model: str
    status: str
    error: str | None = None


class ImageGenerator(ABC):
    name: str

    @abstractmethod
    async def generate(self, *, prompt: str, aspect_ratio: str) -> ImageGenerationResult:
        """Generate a single image from a text prompt."""


class VideoGenerator(ABC):
    name: str

    @abstractmethod
    async def generate_scene_frame(
        self, *, scene: VideoScene, aspect_ratio: str = "9:16"
    ) -> ImageGenerationResult:
        """Generate a key frame for a video storyboard scene."""
