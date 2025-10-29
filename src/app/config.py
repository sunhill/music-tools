import logging
from typing import List

from fastapi import FastAPI
from starlette import status
from starlette.responses import JSONResponse

from app.utils import lifespan

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("fastapi_app")


async def not_found(request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": [{"msg": "Not Found."}]},
    )


exception_handlers = {404: not_found}


class MyFastAPI(FastAPI):
    all_data: dict | None = None
    albums: dict | None = None
    artists: dict | None = None
    tracks: dict | None = None
    playlists: dict | None = None
    album_tracks: dict | None = None
    playlist_tracks: dict | None = None
    unique_playlist_tracks: dict | None = None
    spotify_playlist_maker: object | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = {}


app: MyFastAPI = MyFastAPI(
    exception_handlers=exception_handlers, openapi_url="", lifespan=lifespan
)


def generate_table(data: List[dict], keys: List[str]) -> str:
    table = "<table>"
    table += "<tr>" + "".join(f"<th>{key}</th>" for key in keys) + "</tr>"
    for item in data:
        table += "<tr>" + "".join(f"<td>{item[key]}</td>" for key in keys) + "</tr>"
    table += "</table>"
    return table
