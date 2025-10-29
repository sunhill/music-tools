import logging
from typing import List

from app.config import app
from app.model.model import Artist, Album, Track
from spotify.spotify_playlist_maker import SpotifyPlaylistMaker
from spotify.spotify_utils import (
    SAVED_ARTISTS,
    PLAYLISTS,
    SAVED_TRACKS,
    SAVED_ALBUMS,
    SAVED_ALBUM_TRACKS,
    PLAYLIST_TRACKS,
    UNIQUE_PLAYLIST_TRACKS,
)

logger = logging.getLogger(__name__)


def get_loaded_data():
    app.all_data = {}
    app.all_data[SAVED_ARTISTS] = app.artists
    app.all_data[SAVED_ALBUMS] = app.albums
    app.all_data[SAVED_TRACKS] = app.tracks
    app.all_data[PLAYLISTS] = app.playlists
    app.all_data[SAVED_ALBUM_TRACKS] = app.album_tracks
    app.all_data[PLAYLIST_TRACKS] = app.playlist_tracks
    app.all_data[UNIQUE_PLAYLIST_TRACKS] = app.unique_playlist_tracks

    return app.all_data


def get_album_tracks():
    return app.album_tracks


async def playlist_maker():
    logger.info("Getting SpotifyPlaylistMaker")
    if not app.spotify_playlist_maker:
        logger.info("Creating SpotifyPlaylistMaker")
        spotify_data = get_loaded_data()
        logger.info(f"type spotify_data: {type(spotify_data)}")
        app.spotify_playlist_maker = SpotifyPlaylistMaker(
            use_zip=False, spotify=None, spotify_data=spotify_data
        )
    else:
        logger.info("SpotifyPlaylistMaker already created")
    return app.spotify_playlist_maker


async def get_artists(
    page: int = 1,
    limit: int = 12,
    sort: str = None,
    search: str = None,
    genre: str = None,
) -> List[Artist]:
    # Get all artists
    artists = app.artists

    # Apply search filter if provided
    if search:
        search = search.lower()
        artists = [
            artist for artist in artists if search in artist.get('name', '').lower()
        ]

    # Apply genre filter if provided
    if genre:
        artists = [artist for artist in artists if genre in artist.get('genres', [])]

    # Sort if requested - apply to full dataset before pagination
    if sort:
        # Convert to list of dicts for sorting
        artists_dicts = [
            artist.model_dump() if hasattr(artist, 'model_dump') else artist
            for artist in artists
        ]
        artists_dicts = sorted(
            artists_dicts,
            key=lambda x: x.get('name', '').lower(),
            reverse=(sort == 'desc'),
        )
        # Convert back to Artist objects
        artists = [Artist(**artist) for artist in artists_dicts]

    # # Apply pagination after sorting
    # start_idx = (page - 1) * limit
    # end_idx = start_idx + limit
    # return artists[start_idx:end_idx]
    return artists


async def get_albums(
    page: int = 1,
    limit: int = 12,
    sort: str = None,
    field: str = 'name',
    search: str = None,
    type: str = None,
) -> List[Album]:
    # Get all albums
    albums = app.albums

    # Apply search filter if provided
    if search:
        search = search.lower()
        albums = [
            album
            for album in albums
            if search in album.get('name', '').lower()
            or any(
                search in artist.get('name', '').lower()
                for artist in album.get('artists', [])
            )
        ]

    if type:
        albums = [album for album in albums if type == album["album_type"]]

    # Sort if requested - apply to full dataset before pagination
    if sort:
        if field == 'artist':
            albums = sorted(
                albums,
                key=lambda x: ", ".join(
                    [artist.get("name", "") for artist in x.get('artists', [])]
                ).lower(),
                reverse=(sort == 'desc'),
            )
        else:
            albums = sorted(
                albums,
                key=lambda x: x.get('name', '').lower(),
                reverse=(sort == 'desc'),
            )

    return albums  # Return all albums without pagination for now
    # # Apply pagination after sorting
    #
    # start_idx = (page - 1) * limit
    # end_idx = start_idx + limit
    # return albums[start_idx:end_idx]


async def get_tracks(
    page: int = 1,
    limit: int = 12,
    sort: str = None,
    field: str = 'name',
    search: str = None,
) -> List[Track]:
    # Get all tracks
    tracks = app.tracks

    # Apply search filter if provided
    if search:
        search = search.lower()
        tracks = [
            track
            for track in tracks
            if search in track.get('name', '').lower()
            or any(
                search in artist.get('name', '').lower()
                for artist in track.get('artists', [])
            )
            or search in track.get('album', {}).get('name', '').lower()
        ]

    # Sort if requested - apply to full dataset before pagination
    logger.info(f"Sorting tracks by field: {field}, order: {sort}")
    if sort:
        if field == 'duration':
            tracks = sorted(
                tracks, key=lambda x: x.get('duration_ms', 0), reverse=(sort == 'desc')
            )
        else:
            tracks = sorted(
                tracks,
                key=lambda x: x.get('name', '').lower(),
                reverse=(sort == 'desc'),
            )

    # Apply pagination after sorting
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    return tracks[start_idx:end_idx]


async def get_playlists(
    page: int = 1, limit: int = 12, sort: str = None, search: str = None
) -> List[dict]:
    # Get all playlists
    playlists = app.playlists

    # Apply search filter if provided
    if search:
        search = search.lower()
        playlists = [
            playlist
            for playlist in playlists
            if search in playlist.get('name', '').lower()
            or search in playlist.get('description', '').lower()
        ]

    # Sort if requested
    if sort:
        # Convert to list of dicts for sorting
        playlists_dicts = [
            playlist.model_dump() if hasattr(playlist, 'model_dump') else playlist
            for playlist in playlists
        ]
        playlists_dicts = sorted(
            playlists_dicts,
            key=lambda x: x.get('name', '').lower(),
            reverse=(sort == 'desc'),
        )
        # Convert back to dict objects
        playlists = playlists_dicts

    # Apply pagination
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    return playlists[start_idx:end_idx]
