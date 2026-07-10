import base64
import re
import uuid
from pathlib import Path

MEDIA_DIR = Path("data/media")
_FILENAME_PATTERN = re.compile(r"^[a-f0-9-]+\.(png|jpg|jpeg|webp|mp4)$", re.IGNORECASE)


def media_dir() -> Path:
    path = MEDIA_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def media_public_url(filename: str) -> str:
    return f"/api/media/{filename}"


def is_safe_media_filename(filename: str) -> bool:
    return bool(_FILENAME_PATTERN.match(filename))


def persist_generated_image(image_url: str | None) -> str | None:
    if not image_url:
        return None
    if image_url.startswith("https://") or image_url.startswith("http://"):
        return image_url
    if not image_url.startswith("data:image"):
        return image_url

    header, encoded = image_url.split(",", 1)
    extension = "png"
    if "jpeg" in header or "jpg" in header:
        extension = "jpg"
    elif "webp" in header:
        extension = "webp"

    filename = f"{uuid.uuid4()}.{extension}"
    (media_dir() / filename).write_bytes(base64.b64decode(encoded))
    return media_public_url(filename)


def persist_generated_video(data: bytes | None, *, extension: str = "mp4") -> str | None:
    if not data:
        return None
    filename = f"{uuid.uuid4()}.{extension}"
    (media_dir() / filename).write_bytes(data)
    return media_public_url(filename)


def resolve_media_file(filename: str) -> Path | None:
    if not is_safe_media_filename(filename):
        return None
    path = media_dir() / filename
    return path if path.is_file() else None
