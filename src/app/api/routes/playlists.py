import logging
from typing import List, Annotated

from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse, HTMLResponse

from app.config import generate_table, app
from app.dependencies import get_playlists
from app.model.model import Playlist

router = APIRouter()
router.data = {}

logger = logging.getLogger(__name__)

@router.get("/playlists", response_class=JSONResponse)
async def list_playlists(
    page: int = 1,
    limit: int = 12,
    sort: str = None,
    playlists: Annotated[List[dict], Depends(get_playlists)] = None
):
    logger.info(f"Getting playlists page {page}")
    total = len(app.playlists)
    total_filtered = len(playlists)
    
    return {
        "playlists": playlists,
        "total": total,
        "total_filtered": total_filtered,
    }

@router.get("/playlists_html", response_class=HTMLResponse)
async def get_playlists_html(
        playlists: Annotated[List[dict], Depends(get_playlists)]
):
    logger.info("Getting playlists html")

    playlists: List[dict] = [dict(Playlist(**(playlist))) for playlist in playlists]
    playlists = sorted(playlists, key=lambda x: x["name"])

    keys = list(playlists[0].keys())
    html_content = generate_table(playlists, keys)

    return HTMLResponse(content=html_content)

