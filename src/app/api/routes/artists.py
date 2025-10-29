import logging
from typing import List, Annotated

from fastapi import APIRouter, Depends
from starlette.responses import HTMLResponse

from app.config import generate_table, app
from app.model.model import Artist
from app.dependencies import get_artists

router = APIRouter()
router.data = {}

logger = logging.getLogger(__name__)

@router.get("/artists")
async def list_artists(
    page: int = 1,
    limit: int = 12,
    sort: str = None,
    artists: Annotated[List[Artist], Depends(get_artists)] = None
):
    logger.info(f"Getting artists page {page}")
    total = len(app.artists)  # Get total count of all artists
    total_filtered = len(artists)

    # Pagination logic
    start = (page - 1) * limit
    end = start + limit
    paginated_artists = artists[start:end]

    # Transform the artists data to match the frontend's expected format
    transformed_artists = []
    for artist in paginated_artists:
        # Handle both Pydantic models and dictionaries
        artist_data = artist.model_dump() if hasattr(artist, 'model_dump') else artist
        
        transformed_artist = {
            "id": artist_data.get("id", ""),
            "name": artist_data.get("name", ""),
            "images": artist_data.get("images", []),
            "followers": artist_data.get("followers", {"total": 0}),
            "genres": artist_data.get("genres", []),
            "popularity": artist_data.get("popularity", 0),
            "artists_joined": artist_data.get("name", "")  # For consistency with other endpoints
        }
        transformed_artists.append(transformed_artist)
    
    return {
        "artists": transformed_artists,
        "total": total,
        "total_filtered": total_filtered,
        "total_returned": len(transformed_artists),
    }

@router.get("/artists_html", response_class=HTMLResponse)
async def get_artists_html(artists: Annotated[List[Artist], Depends(get_artists)]):
    logger.info("Getting artists HTML")

    artists: List[dict] = [dict(Artist(**(artist))) for artist in artists]
    artists = sorted(artists, key=lambda x: x["name"])

    # keys = list(artists[0].keys())
    keys = [
        "name",
        "image",
        "genres",
    ]
    html_content = generate_table(artists, keys)

    return HTMLResponse(content=html_content)
