import logging
from typing import List, Annotated

from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse, HTMLResponse

from app.config import generate_table, app
from app.model.model import Track
from app.dependencies import get_tracks, get_album_tracks

router = APIRouter()
router.data = {}

logger = logging.getLogger(__name__)


@router.get("/tracks", response_class=JSONResponse)
async def list_tracks(
    page: int = 1,
    limit: int = 12,
    sort: str = None,
    field: str = 'name',
    tracks: Annotated[List[Track], Depends(get_tracks)] = None
):
    logger.info(f"Getting tracks page {page}")
    total = len(app.tracks)
    total_filtered = len(tracks)
    
    # Transform the tracks data to match the frontend's expected format
    transformed_tracks = []
    for track in tracks:
        # Handle both Pydantic models and dictionaries
        track_data = track.model_dump() if hasattr(track, 'model_dump') else track
        
        # Handle the track data structure
        track_info = track_data.get("track", {}) if "track" in track_data else track_data
        
        # Handle the album data structure
        album_info = track_info.get("album", {})
        if isinstance(album_info, dict):
            album_info = {
                "name": album_info.get("name", ""),
                "images": album_info.get("images", []),
                "release_date": album_info.get("release_date", ""),
                "album_type": album_info.get("album_type", ""),
                "total_tracks": album_info.get("total_tracks", 0)
            }
        
        transformed_track = {
            "id": track_info.get("id", ""),
            "name": track_info.get("name", ""),
            "artists": track_info.get("artists", []),
            "duration_ms": track_info.get("duration_ms", 0),
            "artists_joined": ", ".join([artist.get("name", "") for artist in track_info.get("artists", [])]),
            "_album": album_info,
            "preview_url": track_info.get("preview_url", ""),
            "track_number": track_info.get("track_number", 0),
            "disc_number": track_info.get("disc_number", 0)
        }
        transformed_tracks.append(transformed_track)
    
    return {
        "tracks": transformed_tracks,
        "total": total,
        "total_filtered": total_filtered,
    }


@router.get("/tracks_html", response_class=HTMLResponse)
async def get_tracks_html(tracks: Annotated[List[Track], Depends(get_tracks)]):
    logger.info("Getting tracks")
    tracks: List[Track] = [Track(**(track["track"])) for track in tracks]
    tracks: List[dict] = [track.model_dump() for track in tracks]
    tracks = sorted(tracks, key=lambda x: x["name"])

    keys = [
        "name",
        "artists_joined",
        "duration_ms",
    ]
    html_content = generate_table(tracks, keys)

    return HTMLResponse(content=html_content)


@router.get("/album_tracks", response_class=JSONResponse)
async def get_album_tracks(tracks: Annotated[List[Track], Depends(get_album_tracks)]):
    logger.info("Getting album tracks")
    return {"tracks": tracks}


@router.get("/album_tracks_html", response_class=HTMLResponse)
async def get_album_tracks_html(
    tracks: Annotated[List[Track], Depends(get_album_tracks)],
):
    logger.info("Getting album tracks")

    tracks: List[dict] = [track.model_dump() for track in tracks]

    keys = [
        "name",
        "artists_joined",
        "duration_ms",
    ]

    html_content = generate_table(tracks, keys)

    return HTMLResponse(content=html_content)
