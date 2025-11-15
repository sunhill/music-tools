import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from app.dependencies import playlist_maker
from spotify.spotify_playlist_maker import SpotifyPlaylistMaker

router = APIRouter(dependencies=[Depends(playlist_maker)])
router.data = {}

logger = logging.getLogger(__name__)


@router.get("/make_random_playlist")
async def make_random_playlist(
    playlist_maker: Annotated[SpotifyPlaylistMaker, Depends(playlist_maker)],
):
    logger.debug("making random playlist")
    playlist_name = "Random Playlist from Liked Stuff"
    number_of_songs = 1000
    from_albums = 0.5
    from_tracks = 0.5
    from_playlists = 0.0
    playlist_maker.create_random_playlist(
        number_of_songs=number_of_songs,
        from_albums=from_albums,
        from_tracks=from_tracks,
        from_playlists=from_playlists,
        playlist_name=playlist_name,
    )
    logger.debug("made random playlist")

    return {
        "message": "Random playlist created",
        "tracks": playlist_maker.playlist_tracks,
    }


@router.get("/make_playlists_between_years")
async def make_playlists_between_years(
        start_year: int,
        end_year: int,
        playlist_maker: Annotated[SpotifyPlaylistMaker, Depends(playlist_maker)],
):
    logger.debug(f"making playlists between {start_year} and {end_year}")
    playlist_maker.create_playlists_by_year(
        tracks=playlist_maker.saved_tracks,
        start_year=start_year,
        end_year=end_year,
        playlist_prefix="Liked",
    )
    logger.debug(f"made playlists between {start_year} and {end_year}")

    return {
        "message": f"Playlists for years {start_year} to {end_year} created"
    }


@router.post("/make_playlist_2010s", response_class=JSONResponse)
async def make_playlist_2010s(
    playlist_maker: Annotated[SpotifyPlaylistMaker, Depends(playlist_maker)],
):
    logger.debug("making playlist 2010s")
    playlist_maker.create_playlists_by_year(
        tracks=playlist_maker.saved_tracks,
        start_year=2010,
        end_year=2019,
        playlist_prefix="Liked",
    )
    logger.debug("made playlist 2010s")

    response = {
        "message": "Playlist 2010s created",
    }
    return JSONResponse(content=response)


@router.post("/make_playlist_2020s", response_class=JSONResponse)
async def make_playlist_2020s(
    playlist_maker: Annotated[SpotifyPlaylistMaker, Depends(playlist_maker)],
):
    logger.debug("making playlist 2020s")
    playlist_maker.create_playlists_by_year(
        tracks=playlist_maker.saved_tracks,
        start_year=2020,
        end_year=2024,
        playlist_prefix="Liked",
    )
    logger.debug("made playlist 2020s")

    response = {
        "message": "Playlist 2020s created",
    }
    return JSONResponse(content=response)


@router.post("/make_playlist_for_year/{year}", response_class=JSONResponse)
async def make_playlist_for_year(
        year: int,
        playlist_maker: Annotated[SpotifyPlaylistMaker, Depends(playlist_maker)],
):
    logger.debug(f"making playlist for year {year}")
    playlist_maker.create_playlists_by_year(
        tracks=playlist_maker.saved_tracks,
        start_year=year,
        end_year=year,
        playlist_prefix="Liked",
    )
    logger.debug("made playlist for {year")

    response = {
        "message": "Playlist created",
    }
    return JSONResponse(content=response)


@router.post("/make_playlist_2025", response_class=JSONResponse)
async def make_playlist_2025(
    playlist_maker: Annotated[SpotifyPlaylistMaker, Depends(playlist_maker)],
):
    logger.debug("making playlist 2025")
    playlist_maker.create_playlists_by_year(
        tracks=playlist_maker.saved_tracks,
        start_year=2025,
        end_year=2025,
        playlist_prefix="Liked",
    )
    logger.debug("made playlist 2025")

    response = {
        "message": "Playlist 2025 created",
    }
    return JSONResponse(content=response)
