import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from spotify.spotify_utils import get_memory_usage, get_data_location, unzip_data_from_zip, get_latest_zip, \
    SAVED_ALBUMS, SAVED_ARTISTS, SAVED_TRACKS, PLAYLISTS

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("fastapi_app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for the FastAPI application.
    This is called when the application starts up and shuts down.
    """
    logger.info("Starting up FastAPI application")
    try:
        await load_data(app)
        yield  # This is where the app runs
    finally:
        logger.info("Shutting down FastAPI application")
        # Perform any cleanup here if necessary



async def load_data(app: FastAPI):
    logger.info("Loading zipped data at startup")
    try:
        get_memory_usage()
        raw_data_location = await get_data_location()
        app.album_tracks = {}
        # app.album_tracks = unzip_data_from_zip(
        #     get_latest_zip(raw_data_location, SAVED_ALBUM_TRACKS)
        # )
        logger.info("Album tracks loaded")
        app.albums = unzip_data_from_zip(
            get_latest_zip(raw_data_location, SAVED_ALBUMS)
        )
        logger.info("Albums loaded")
        app.artists = unzip_data_from_zip(
            get_latest_zip(raw_data_location, SAVED_ARTISTS)
        )
        logger.info("Artists loaded")
        app.tracks = unzip_data_from_zip(
            get_latest_zip(raw_data_location, SAVED_TRACKS)
        )
        logger.info("Tracks loaded")
        app.playlists = unzip_data_from_zip(
            get_latest_zip(raw_data_location, PLAYLISTS)
        )
        logger.info("Playlists loaded")
        app.playlist_tracks = {}

        app.unique_playlist_tracks = {}
        if not app.playlists:
            logger.error("app.playlists is None!")
        if not app.tracks:
            logger.error("app.tracks is None!")
        if not app.albums:
            logger.error("app.albums is None!")
        if not app.artists:
            logger.error("app.artists is None!")
        if not app.album_tracks:
            logger.error("app.album_tracks is None!")
        # app.playlist_tracks = unzip_data_from_zip(
        #     get_latest_zip(raw_data_location, PLAYLIST_TRACKS)
        # )
        # app.unique_playlist_tracks = unzip_data_from_zip(
        #     get_latest_zip(raw_data_location, UNIQUE_PLAYLIST_TRACKS)
        # )
        app.unique_playlist_tracks = {}
        logger.info("Zipped data loaded")
    except Exception as e:
        logger.error(f"Error loading zipped data: {e}")

