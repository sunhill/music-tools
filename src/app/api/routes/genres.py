import threading
from fastapi import APIRouter
from starlette.responses import JSONResponse
from app.config import app

router = APIRouter()
_genres_cache = None
_cache_lock = threading.Lock()

@router.get("/genres", response_class=JSONResponse)
async def list_genres():
    global _genres_cache
    if _genres_cache is None:
        with _cache_lock:
            if _genres_cache is None:  # Double-checked locking
                genres_set = set()
                for artist in app.artists:
                    artist_data = artist.model_dump() if hasattr(artist, 'model_dump') else artist
                    for genre in artist_data.get("genres", []):
                        genres_set.add(genre)
                _genres_cache = sorted(genres_set)
    return {"genres": _genres_cache}