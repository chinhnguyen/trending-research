from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from willbe_trends.media.storage import resolve_media_file

router = APIRouter(tags=["media"])

_MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".mp4": "video/mp4",
}


@router.get("/media/{filename}")
def get_generated_media(filename: str):
    path = resolve_media_file(filename)
    if path is None:
        raise HTTPException(status_code=404, detail="Media file not found")
    media_type = _MEDIA_TYPES.get(path.suffix.lower())
    return FileResponse(path, media_type=media_type)
