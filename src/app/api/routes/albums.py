import logging
from typing import List, Annotated

from fastapi import APIRouter, Depends
from starlette.responses import HTMLResponse

from app.config import generate_table, app
from app.dependencies import get_albums
from app.model.model import Album

router = APIRouter()
router.data = {}

logger = logging.getLogger(__name__)

@router.get("/albums")
async def list_albums(
    page: int = 1,
    limit: int = 12,
    sort: str = None,
    field: str = 'name',
    albums: Annotated[List[Album], Depends(get_albums)] = None
):
    logger.info(f"Getting albums page {page}")
    total = len(app.albums)
    total_filtered = len(albums)
    logger.info(f"Total albums: {total}, filtered albums: {total_filtered}")
    # Pagination logic
    start = (page - 1) * limit
    end = start + limit
    paginated_albums = albums[start:end]

    # Transform the albums data to match the frontend's expected format
    transformed_albums = []
    for album in paginated_albums:
        # logger.debug(f"Processing album: {album}")
        # Handle both Pydantic models and dictionaries
        album_data = album.model_dump() if hasattr(album, 'model_dump') else album

        # Handle the track data structure
        album_data = album_data.get("album", {}) if "album" in album_data else album_data

        transformed_album = {
            "id": album_data.get("_id", ""),
            "name": album_data.get("name", ""),
            "artists": album_data.get("artists", []),
            "images": album_data.get("images", []),
            "release_date": album_data.get("release_date", ""),
            "artists_joined": ", ".join([artist.get("name", "") for artist in album_data.get("artists", [])]),
            "album_type": album_data.get("album_type", ""),
            "label": album_data.get("label", ""),
            "total_tracks": album_data.get("total_tracks", 0),
            "release_date_precision": album_data.get("release_date_precision", "")
        }
        transformed_albums.append(transformed_album)
    
    return {
        "albums": transformed_albums,
        "total": total,
        "total_filtered": total_filtered,
        "total_returned": len(transformed_albums),
    }

@router.get("/albums_html")
async def get_albums_html(albums: Annotated[List[Album], Depends(get_albums)]):
    logger.info("Getting albums")
    if not albums:
        return HTMLResponse(content="<p>No data available to display.</p>")

    albums: List[Album] = [Album(**(album["album"])) for album in albums]

    albums: List[dict] = [album.model_dump() for album in albums]
    keys = [
        "name",
        "artists_joined",
        "label",
        "image",
        "total_tracks",
        "album_type",
        "release_year",
    ]

    html_content = generate_table(albums, keys)

    return HTMLResponse(content=html_content)


