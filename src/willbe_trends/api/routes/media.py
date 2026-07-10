from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from willbe_trends.media.storage import resolve_media_file

router = APIRouter(tags=["media"])


@router.get("/media/{filename}")
def get_generated_media(filename: str):
    path = resolve_media_file(filename)
    if path is None:
        raise HTTPException(status_code=404, detail="Media file not found")
    return FileResponse(path)
