import datetime
import logging
import os
from configparser import ConfigParser
from time import sleep
from typing import Optional, Any, Tuple, List, Generator

from spotipy import Spotify, SpotifyException

from spotify.spotify_get_data_common import (
    SPOTIFY_SCOPES,
    LIMIT,
    SLEEP_BETWEEN_CALLS,
    TOO_MANY_REQUESTS,
    READ_TIMEOUT,
    RATE_LIMITED_SLEEPING,
)
from spotify.spotify_utils import (
    SAVED_ARTISTS,
    SAVED_ALBUMS,
    UNIQUE_PLAYLIST_ARTISTS,
    UNIQUE_PLAYLIST_TRACKS,
    PLAYLIST_TRACKS,
    PLAYLISTS,
    OTHER_PLAYLISTS,
    SAVED_TRACKS,
    SAVED_ALBUM_TRACKS,
)
from spotify.spotify_utils import (
    get_spotify_wrapper,
    setup_app_logging,
    zip_data,
    get_config_location,
)
from utils.rate_limiter.rate_limiter_interface import RateLimiterInterface, RateLimiterConfig
from utils.rate_limiter.redis_rate_limiter import RedisRateLimiter

logger = logging.getLogger(__name__)
# Turn off logging for spotipy.client
logging.getLogger('spotipy.client').setLevel(logging.CRITICAL)


class SpotifyDataGetter:
    me: Optional[Any]
    spotify_username: str
    spotify: Spotify
    rate_limiter: RateLimiterInterface

    def __init__(
        self,
        spotify: Optional[Spotify] = None,
        config_parser: Optional[ConfigParser] = None,
        scopes: Optional[List[str]] = None,
        redis_url: Optional[str] = None,
        rate_limit: int = 60,
        burst_size: int = 10,
        retry_after: int = 10,
    ) -> None:
        super().__init__()

        self.config_parser = config_parser or ConfigParser()
        self._load_config()

        self._init_rate_limiter(redis_url, rate_limit, burst_size, retry_after)
        self._init_spotify_client(spotify, scopes)
        self._init_user_info()

    def _load_config(self) -> None:
        self.config_location = get_config_location()
        self.config_parser.read(self.config_location)
        self.running_in_docker = os.getenv("RUNNING_IN_DOCKER", "False")
        if self.running_in_docker == "True":
            self.save_location = "/src/data/"
        else:
            self.save_location = self.config_parser["spotify"]["save_location"]

        self.spotify_username = self.config_parser["spotify"]["spotify_user"]
        logger.info(f"Using user name {self.spotify_username}")
        self.save_location = os.path.join(self.save_location, self.spotify_username)
        logger.info(f"Using save location {self.save_location}")
        self.raw_data_folder_name = self.config_parser["spotify"]["raw_data_location"]
        self.raw_data_location = os.path.join(
            self.save_location, self.raw_data_folder_name
        )
        self.date_folder = str(datetime.date.today())
        self.raw_data_location = os.path.join(self.raw_data_location, self.date_folder)
        logger.info(f"Using raw data location {self.raw_data_location}")

    def _init_rate_limiter(
        self,
        redis_url: Optional[str],
        rate_limit: int,
        burst_size: int,
        retry_after: int,
    ) -> None:
        """Initialize rate limiter.

        Args:
            redis_url: Redis URL for rate limiting
            rate_limit: Rate limit per minute
            burst_size: Number of requests allowed in burst
            retry_after: Seconds to wait after rate limit
        """
        rate_limiter_config = RateLimiterConfig(
            redis_url=redis_url or os.getenv("REDIS_URL", "redis://localhost:6379"),
            default_rate=rate_limit,
            burst_size=burst_size,
            retry_after=retry_after,
        )
        self.rate_limiter = RedisRateLimiter(rate_limiter_config)

    def _init_spotify_client(
        self, spotify: Optional[Spotify], scopes: Optional[List[str]]
    ) -> None:
        """Initialize Spotify client.

        Args:
            spotify: Optional Spotify client instance
            scopes: Optional list of Spotify API scopes
        """
        if spotify:
            self.spotify = spotify
        else:
            scopes_to_use = scopes or SPOTIFY_SCOPES
            self.spotify = get_spotify_wrapper(scope=",".join(scopes_to_use))

    def _init_user_info(self) -> None:
        """Initialize user information."""
        try:
            self.me = self.spotify.me()
            self.spotify_username = self.me["display_name"]
            logger.info(f"Connected as user: {self.spotify_username}")
        except SpotifyException as e:
            logger.error(f"Failed to get user info: {e}")
            raise

    def _make_request(self, request_func, *args, **kwargs):
        """
        Make a rate-limited request to Spotify API.
        """
        while True:
            try:
                logger.debug("Waiting for token")
                self.rate_limiter.wait_for_token()
                response = request_func(*args, **kwargs)
                sleep(SLEEP_BETWEEN_CALLS)
                return response
            except SpotifyException as e:
                if self.check_http_status(e):
                    logger.info(RATE_LIMITED_SLEEPING)
                    sleep(self.rate_limiter.get_retry_after())
                    continue
                else:
                    raise e
            except Exception as e:
                logger.error(f"Request exception: {e}")
                raise e

    def get_all_data(self):
        logger.debug("Getting all data")
        albums = list(self.get_library_saved_albums())
        albums = list(self.dedupe_albums(albums))
        zip_data(
            albums,
            data_type=SAVED_ALBUMS,
            data_location=self.raw_data_location,
        )

        artists = list(self.get_library_saved_artists())
        zip_data(
            artists,
            data_type=SAVED_ARTISTS,
            data_location=self.raw_data_location,
        )

        tracks = list(self.get_library_saved_tracks())
        tracks = list(self.dedupe_tracks(tracks))
        zip_data(
            tracks,
            data_type=SAVED_TRACKS,
            data_location=self.raw_data_location,
        )

        album_tracks = list(self.get_library_saved_album_tracks(albums))
        zip_data(
            album_tracks,
            data_type=SAVED_ALBUM_TRACKS,
            data_location=self.raw_data_location,
        )

        # TODO optimize this
        playlists, other_playlists = [], []
        playlists, other_playlists = self.get_playlists()
        zip_data(
            playlists,
            data_type=PLAYLISTS,
            data_location=self.raw_data_location,
        )
        zip_data(
            other_playlists,
            data_type=OTHER_PLAYLISTS,
            data_location=self.raw_data_location,
        )

        # TODO optimize this
        playlist_tracks = {}
        playlist_tracks = self.get_playlist_tracks(playlists)
        zip_data(
            playlist_tracks,
            data_type=PLAYLIST_TRACKS,
            data_location=self.raw_data_location,
        )
        unique_playlist_tracks = {}
        unique_playlist_tracks = self.get_all_unique_tracks_in_playlists(
            playlists, playlist_tracks
        )
        zip_data(
            unique_playlist_tracks,
            data_type=UNIQUE_PLAYLIST_TRACKS,
            data_location=self.raw_data_location,
        )

        unique_playlist_artists = {}
        unique_playlist_artists = self.get_all_unique_artists_in_playlists(
            playlists, playlist_tracks
        )
        zip_data(
            unique_playlist_artists,
            data_type=UNIQUE_PLAYLIST_ARTISTS,
            data_location=self.raw_data_location,
        )

        logger.debug("All data loaded")

    def get_top_tracks(self) -> list:
        logger.debug("Getting top tracks")
        top_tracks = []
        offset = 0

        while True:
            logger.debug(f"offset {offset}")
            response = self._make_request(
                self.spotify.current_user_top_tracks, limit=LIMIT, offset=offset
            )

            items = response["items"]
            if len(items) == 0:
                break

            top_tracks.extend(items)
            offset += LIMIT

        return top_tracks

    @staticmethod
    def check_http_status(e):
        return e.http_status == TOO_MANY_REQUESTS or e.http_status == READ_TIMEOUT

    def get_library_saved_albums(self) -> Generator:
        logger.debug("Getting library saved albums")
        offset = 0

        while True:
            logger.debug(f"offset {offset}")
            response = self._make_request(
                self.spotify.current_user_saved_albums, limit=LIMIT, offset=offset
            )

            items = response["items"]
            if len(items) == 0:
                break

            yield from items
            offset += LIMIT

    def get_library_saved_artists(self) -> Generator:
        logger.debug("Getting library saved artists")

        last_artist_id = None

        while True:
            logger.debug(f"last_artist_id {last_artist_id}")
            response = self._make_request(
                self.spotify.current_user_followed_artists,
                limit=LIMIT,
                after=last_artist_id,
            )

            items = response["artists"]["items"]

            if not items:
                break

            yield from items
            last_artist_id = items[-1]["id"]

    def get_playlists(self) -> Tuple[List, List]:
        logger.debug("Getting playlists")

        playlists = []

        offset = 0
        while True:
            logger.debug(f"offset {offset}")
            response = self._make_request(
                self.spotify.current_user_playlists, limit=LIMIT, offset=offset
            )

            items = response["items"]

            if len(items) == 0:
                break

            playlists.extend(items)
            offset += LIMIT

        display_name = self.me["display_name"]

        my_playlists = [
            x for x in playlists if x["owner"]["display_name"] == display_name
        ]
        # filter out generated playlists with *generated in comments
        my_playlists = [
            x for x in my_playlists if "*generated" not in x["description"].lower()
        ]

        other_playlists = [
            x for x in playlists if x["owner"]["display_name"] != display_name
        ]
        return (
            my_playlists,
            other_playlists,
        )

    def get_playlist_tracks(self, playlists: list) -> dict:
        logger.debug("Getting playlist tracks")
        playlist_tracks: dict = {}
        for playlist in playlists:
            name = str(playlist["name"])
            tracks_total = playlist["tracks"]["total"]

            logger.debug(f"Loading playlist: {name} {tracks_total} songs")
            playlist_tracks[playlist["id"]] = list(
                self.get_tracks_for_playlist(playlist["id"], name)
            )

        return playlist_tracks

    def get_tracks_for_playlist(self, playlist_id, playlist_name) -> Generator:
        logger.debug(
            f"Getting tracks for playlist {playlist_name} and id {playlist_id}"
        )

        offset = 0
        while True:
            logger.debug(f"offset {offset}")
            response = self._make_request(
                self.spotify.playlist_items,
                playlist_id=playlist_id,
                limit=LIMIT,
                offset=offset,
            )
            items = response["items"]

            if len(items) == 0:
                break

            yield from items
            offset += LIMIT

    def get_library_saved_tracks(self) -> Generator:
        logger.debug("Getting library saved tracks")
        offset = 0
        while True:
            logger.debug(f"offset {offset}")
            response = self._make_request(
                self.spotify.current_user_saved_tracks, limit=LIMIT, offset=offset
            )
            items = response["items"]

            if len(items) == 0:
                break
            yield from items
            offset += LIMIT

    @staticmethod
    def dedupe_tracks(tracks) -> Generator:
        logger.debug("Deduping tracks")
        logger.debug(f"Before dedupe: {len(tracks)}")
        unique_tracks_by_isrc: dict = dict()
        tracks_with_no_isrc = []
        for track in tracks:
            try:
                isrc = track["track"]["external_ids"]["isrc"]
                unique_tracks_by_isrc[isrc] = track
            except KeyError:
                logger.debug(f"Track {track} has no isrc")
                tracks_with_no_isrc.append(track)

        deduped_tracks = sorted(
            list(unique_tracks_by_isrc.values()),
            key=lambda x: x["added_at"],
            reverse=True,
        )
        deduped_tracks.extend(tracks_with_no_isrc)
        logger.debug(f"After dedupe: {len(deduped_tracks)}")
        yield from deduped_tracks

    @staticmethod
    def dedupe_albums(albums) -> Generator:
        logger.debug("Deduping albums")
        logger.debug(f"Before dedupe: {len(albums)}")
        unique_albums_by_upc: dict = dict()
        albums_with_no_upc = []
        for album in albums:
            try:
                upc = album["album"]["external_ids"]["upc"]
                unique_albums_by_upc[upc] = album
            except KeyError:
                logger.debug(f"Track {album} has no upc")
                albums_with_no_upc.append(album)

        deduped_albums = sorted(
            list(unique_albums_by_upc.values()),
            key=lambda x: x["added_at"],
            reverse=True,
        )
        deduped_albums.extend(albums_with_no_upc)
        logger.debug(f"After dedupe: {len(deduped_albums)}")
        yield from deduped_albums

    def get_tracks_for_search(self, query, num_tracks):
        logger.debug("Getting tracks for search")
        saved_tracks = []

        for offset in range(0, num_tracks, LIMIT):
            response = self.spotify.search(
                q=f"{query}", type="track", limit=LIMIT, offset=offset
            )
            sleep(SLEEP_BETWEEN_CALLS)

            items = response["tracks"]["items"]

            if len(items) == 0:
                break

            saved_tracks.extend(items)

        return saved_tracks

    @staticmethod
    def get_all_unique_tracks_in_playlists(
        playlists: list, playlist_tracks: dict
    ) -> dict:
        logger.debug("Getting all unique tracks in playlists")

        all_tracks = {}
        for playlist in playlists:
            tracks = playlist_tracks.get(playlist["id"], [])
            for track in tracks:
                if "track" in track:
                    try:
                        track_uri = track["track"]["uri"]
                        all_tracks[track_uri] = track["track"]
                    except KeyError as e:
                        logger.debug(f"KeyError, skipping track: {e}")
                        continue
                    except TypeError as e:
                        logger.debug(f"TypeError, skipping track: {e}")
                        continue

        logger.debug(f"Number of unique tracks is {len(all_tracks)}")
        return all_tracks

    @staticmethod
    def get_all_unique_artists_in_playlists(
        playlists: list, playlist_tracks: dict
    ) -> dict:
        logger.debug("Getting all unique artists in playlists")
        all_artists = {}
        for playlist in playlists:
            tracks: list = playlist_tracks.get(playlist["id"], [])
            for track in tracks:
                try:
                    artists: list = track["track"]["artists"]
                    for artist in artists:
                        all_artists[artist["id"]] = artist
                except KeyError as e:
                    logger.debug(f"KeyError, skipping artist: {e}")
                    continue
                except TypeError as e:
                    logger.debug(f"TypeError, skipping artist: {e}")
                    continue

        logger.debug("Number of unique artists is " + str(len(all_artists.values())))
        return all_artists

    @staticmethod
    def get_library_saved_album_tracks(albums: List) -> Generator:
        logger.debug("Getting library saved album tracks")
        for album in albums:
            yield from album["album"]["tracks"]["items"]


def main():
    setup_app_logging(logger, logging.DEBUG)

    spotify_data_getter: SpotifyDataGetter = SpotifyDataGetter()

    spotify_data_getter.get_all_data()


if __name__ == "__main__":
    main()
