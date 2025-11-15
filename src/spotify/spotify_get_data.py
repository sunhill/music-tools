import asyncio
import datetime
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from configparser import ConfigParser
from time import sleep
from typing import Optional, Any, Tuple, List, Generator, Dict

from spotipy import Spotify, SpotifyException

from spotify.spotify_get_data_common import (
    LIMIT,
    SLEEP_BETWEEN_CALLS,
    RATE_LIMITED_SLEEPING,
    SPOTIFY_SCOPES,
    TOO_MANY_REQUESTS,
    READ_TIMEOUT,
    MAX_CONCURRENT_REQUESTS,
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
from utils.rate_limiter.rate_limiter_interface import (
    RateLimiterInterface,
    RateLimiterConfig,
)
from utils.rate_limiter.redis_rate_limiter import RedisRateLimiter

logger = logging.getLogger(__name__)
# Turn off logging for spotipy.client
logging.getLogger('spotipy.client').setLevel(logging.CRITICAL)


class BaseSpotifyDataGetter:
    """Base class for Spotify data retrieval with common functionality."""

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
        rate_limit: int = 200,
        burst_size: int = 20,
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

    @staticmethod
    def check_http_status(e):
        return e.http_status == TOO_MANY_REQUESTS or e.http_status == READ_TIMEOUT

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
        unique_tracks_by_isrc: dict = {}
        tracks_with_no_isrc = []
        for track in tracks:
            try:
                isrc = track["external_ids"]["isrc"]
                unique_tracks_by_isrc[isrc] = track
            except KeyError:
                track_name = track["name"]
                logger.debug(f"Track {track_name} has no isrc")
                tracks_with_no_isrc.append(track)

        deduped_tracks = sorted(
            unique_tracks_by_isrc.values(),
            key=lambda x: x["name"],
            reverse=True,
        )
        deduped_tracks.extend(tracks_with_no_isrc)
        logger.debug(f"After dedupe: {len(deduped_tracks)}")
        yield from deduped_tracks

    @staticmethod
    def dedupe_albums(albums) -> Generator:
        logger.debug("Deduping albums")
        logger.debug(f"Before dedupe: {len(albums)}")
        unique_albums_by_upc: dict = {}
        albums_with_no_upc = []
        for album in albums:
            try:
                upc = album["external_ids"]["upc"]
                unique_albums_by_upc[upc] = album
                logger.debug(f"Album {album['name']} has upc {upc}")
            except KeyError:
                album_name = album["name"]
                logger.debug(f"Album {album_name} has no upc")
                albums_with_no_upc.append(album)

        deduped_albums = sorted(
            unique_albums_by_upc.values(),
            key=lambda x: x["name"],
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
                        track_uri = track["uri"]
                        all_tracks[track_uri] = track
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
                    artists: list = track["artists"]
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
            yield from album["tracks"]["items"]


class AsyncSpotifyDataGetter(BaseSpotifyDataGetter):
    """Async version of SpotifyDataGetter with parallel processing capabilities."""

    async def _process_batch(
            self, batch: List[Dict[str, Any]], process_func: callable
    ) -> List[Dict[str, Any]]:
        """Process a batch of items in parallel using ThreadPoolExecutor."""
        logger.debug(f"Processing batch of {len(batch)} items")
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            tasks = [
                loop.run_in_executor(executor, process_func, item) for item in batch
            ]
            return await asyncio.gather(*tasks)

    async def _wait_for_token_async(self):
        """Asynchronously wait for a token without blocking the event loop."""
        loop = asyncio.get_event_loop()

        logger.debug("Waiting for token asynchronously")
        # Use run_in_executor to run the synchronous wait_for_token method
        while True:
            try:
                await loop.run_in_executor(None, self.rate_limiter.wait_for_token)
                break
            except Exception as e:
                logger.error(f"Error waiting for token: {e}")
                # Optionally, you could add a small sleep here to avoid tight looping
                await asyncio.sleep(0.1)

    async def _make_rate_limited_request_async(self, request_func, *args, **kwargs):
        """Make a rate-limited request to Spotify API in an async context without blocking."""
        while True:
            try:
                logger.debug("Waiting for token")
                await self._wait_for_token_async()

                # Run the synchronous request in a thread pool
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, lambda: request_func(*args, **kwargs)
                )

                # Small sleep to prevent overwhelming the API
                await asyncio.sleep(SLEEP_BETWEEN_CALLS)
                return response
            except SpotifyException as e:
                if self.check_http_status(e):
                    logger.info(RATE_LIMITED_SLEEPING)
                    await asyncio.sleep(self.rate_limiter.get_retry_after())
                    continue
                else:
                    raise e
            except Exception as e:
                logger.error(f"Request exception: {e}")
                raise e

    async def _get_all_items_parallel(
        self,
        get_func: callable,
        process_func: callable,
        batch_size: int = 50,
        max_concurrent_requests: int = MAX_CONCURRENT_REQUESTS,
    ) -> List[Dict[str, Any]]:
        """Get all items using true parallel processing with batching.

        Args:
            get_func: Function to get items from Spotify API
            process_func: Function to process each item
            batch_size: Number of items to retrieve per request
            max_concurrent_requests: Maximum number of concurrent API requests
        """
        logger.info(
            f"Starting parallel retrieval with batch size {batch_size} and max {max_concurrent_requests} concurrent requests"
        )

        # First, get the total count with a single request
        initial_response = await self._make_rate_limited_request_async(
            get_func, limit=1, offset=0
        )
        total = initial_response['total']
        logger.info(f"Total items to retrieve: {total}")

        # Calculate the number of batches needed
        num_batches = (total + batch_size - 1) // batch_size
        logger.info(f"Will retrieve in {num_batches} batches")

        # Create a semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent_requests)

        async def fetch_batch(batch_index):
            offset = batch_index * batch_size
            async with semaphore:
                logger.debug(
                    f"Fetching batch {batch_index + 1}/{num_batches} at offset {offset}"
                )
                batch = await self._make_rate_limited_request_async(
                    get_func, limit=batch_size, offset=offset
                )
                items = batch['items']
                logger.debug(f"Retrieved {len(items)} items in batch {batch_index + 1}")
                processed_items = await self._process_batch(items, process_func)
                return processed_items

        # Create tasks for all batches
        tasks = [fetch_batch(i) for i in range(num_batches)]

        # Execute all tasks concurrently and gather results
        all_batches = await asyncio.gather(*tasks)

        # Flatten the results
        all_items = [item for batch in all_batches for item in batch]

        logger.info(f"Completed parallel retrieval. Total items: {len(all_items)}")
        return all_items

    async def get_all_saved_tracks_parallel(self) -> List[Dict[str, Any]]:
        """Get all saved tracks using parallel processing."""
        logger.info("Starting parallel retrieval of saved tracks")
        return await self._get_all_items_parallel(
            self.spotify.current_user_saved_tracks, lambda item: item['track']
        )

    async def get_all_saved_albums_parallel(self) -> List[Dict[str, Any]]:
        """Get all saved albums using parallel processing."""
        logger.info("Starting parallel retrieval of saved albums")
        return await self._get_all_items_parallel(self.spotify.current_user_saved_albums, lambda item: item['album'])

    async def get_all_playlists_parallel(self) -> List[Dict[str, Any]]:
        """Get all playlists using parallel processing."""
        logger.info("Starting parallel retrieval of playlists")
        return await self._get_all_items_parallel(
            self.spotify.current_user_playlists, lambda item: item
        )

    async def get_playlist_tracks_parallel(self, playlist_id: str) -> List[Dict[str, Any]]:
        """Get all tracks from a playlist using parallel processing."""
        logger.info(f"Starting parallel retrieval of tracks for playlist {playlist_id}")
        return await self._get_all_items_parallel(
            lambda limit, offset: self.spotify.playlist_items(
                playlist_id, limit=limit, offset=offset, additional_types=("track")
            ),
            lambda item: item['track'],
        )

    async def get_all_saved_artists_parallel(self) -> List[Dict[str, Any]]:
        """Get all saved artists using parallel processing."""
        logger.info("Starting parallel retrieval of saved artists")

        # The Spotify API for followed artists uses a different pagination mechanism (after parameter)
        # We need to implement a custom parallel retrieval for this endpoint

        async def get_artists_batch(after_id=None):
            """Get a batch of artists using the after parameter."""
            try:
                logger.debug(f"Fetching artists batch after ID: {after_id}")
                response = await self._make_rate_limited_request_async(
                    self.spotify.current_user_followed_artists,
                    limit=LIMIT,
                    after=after_id,
                )
                return response["artists"]["items"]
            except Exception as e:
                logger.error(f"Error fetching artists batch: {e}")
                return []

        async def get_all_artists_parallel():
            """Get all artists using parallel processing with the after parameter."""
            all_artists = []

            # First, get the initial batch to determine the total
            initial_batch = await get_artists_batch()
            if not initial_batch:
                logger.info("No saved artists found")
                return []

            all_artists.extend(initial_batch)
            last_artist_id = initial_batch[-1]["id"] if initial_batch else None

            # Continue fetching batches until we get an empty response
            while last_artist_id:
                batch = await get_artists_batch(last_artist_id)
                if not batch:
                    break

                all_artists.extend(batch)
                last_artist_id = batch[-1]["id"] if batch else None
                logger.debug(f"Retrieved {len(all_artists)} artists so far")

            logger.info(f"Completed parallel retrieval of {len(all_artists)} artists")
            return all_artists

        return await get_all_artists_parallel()

    async def get_all_data_parallel(self):
        """Get all Spotify data using parallel processing and zip the results."""
        logger.info("Starting parallel retrieval of all Spotify data")

        # Get saved albums
        logger.info("Retrieving saved albums")
        albums = await self.get_all_saved_albums_parallel()
        # remove available_markets from album data and from the tracks in the albums
        # This is to reduce the size of the data and avoid unnecessary fields
        for album in albums:
            album.pop("available_markets", None)
            for track in album.get("tracks", {}).get("items", []):
                track.pop("available_markets", None)
        albums = list(self.dedupe_albums(albums))
        zip_data(
            albums,
            data_type=SAVED_ALBUMS,
            data_location=self.raw_data_location,
        )
        logger.info(f"Saved {len(albums)} albums")

        # album_tracks = list(self.get_library_saved_album_tracks(albums))
        # zip_data(
        #     album_tracks,
        #     data_type=SAVED_ALBUM_TRACKS,
        #     data_location=self.raw_data_location,
        # )

        # Get saved artists
        logger.info("Retrieving saved artists")
        artists = await self.get_all_saved_artists_parallel()
        zip_data(
            artists,
            data_type=SAVED_ARTISTS,
            data_location=self.raw_data_location,
        )
        logger.info(f"Saved {len(artists)} artists")

        # Get saved tracks
        logger.info("Retrieving saved tracks")
        tracks = await self.get_all_saved_tracks_parallel()
        tracks = list(self.dedupe_tracks(tracks))
        zip_data(
            tracks,
            data_type=SAVED_TRACKS,
            data_location=self.raw_data_location,
        )
        logger.info(f"Saved {len(tracks)} tracks")

        # Get playlists
        logger.info("Retrieving playlists")
        playlists = await self.get_all_playlists_parallel()

        # Filter playlists by owner
        display_name = self.me["display_name"]
        my_playlists = [
            x for x in playlists if x["owner"]["display_name"] == display_name
        ]
        # Filter out generated playlists with *generated in comments
        # TODO commenting this out for now, as it results in duplicate playlists
        # my_playlists = [
        #     x
        #     for x in my_playlists
        #     if "*generated" not in x.get("description", "").lower()
        # ]

        other_playlists = [
            x for x in playlists if x["owner"]["display_name"] != display_name
        ]

        zip_data(
            my_playlists,
            data_type=PLAYLISTS,
            data_location=self.raw_data_location,
        )
        zip_data(
            other_playlists,
            data_type=OTHER_PLAYLISTS,
            data_location=self.raw_data_location,
        )
        logger.info(
            f"Saved {len(my_playlists)} of my playlists and {len(other_playlists)} other playlists"
        )

        # TODO commenting this out for now, as it takes a long time to process
        # await self.process_playlist_tracks(my_playlists)

        logger.info("All data retrieved and zipped successfully")

    async def process_playlist_tracks(self, my_playlists):
        # Get playlist tracks
        logger.info("Retrieving playlist tracks")
        playlist_tracks = {}
        for playlist in my_playlists:
            playlist_id = playlist["id"]
            playlist_name = playlist["name"]
            logger.info(f"Retrieving tracks for playlist: {playlist_name}")
            tracks = await self.get_playlist_tracks_parallel(playlist_id)
            playlist_tracks[playlist_id] = tracks
            logger.info(f"Retrieved {len(tracks)} tracks for playlist {playlist_name}")
        zip_data(
            playlist_tracks,
            data_type=PLAYLIST_TRACKS,
            data_location=self.raw_data_location,
        )
        # Get unique tracks and artists in playlists
        logger.info("Processing unique tracks and artists in playlists")
        unique_playlist_tracks = self.get_all_unique_tracks_in_playlists(
            my_playlists, playlist_tracks
        )
        unique_playlist_artists = self.get_all_unique_artists_in_playlists(
            my_playlists, playlist_tracks
        )
        zip_data(
            unique_playlist_tracks,
            data_type=UNIQUE_PLAYLIST_TRACKS,
            data_location=self.raw_data_location,
        )
        zip_data(
            unique_playlist_artists,
            data_type=UNIQUE_PLAYLIST_ARTISTS,
            data_location=self.raw_data_location,
        )


async def main():
    """Test the parallel processing implementation with data zipping."""
    import time

    # Set up logging
    setup_app_logging(logger, logging.DEBUG)

    # Initialize the AsyncSpotifyDataGetter with proper parameters
    spotify_data_getter = AsyncSpotifyDataGetter(
        config_parser=None,  # Will use default ConfigParser
        scopes=SPOTIFY_SCOPES,  # Use the predefined scopes
        rate_limit=60,  # Default rate limit
        burst_size=10,  # Default burst size
        retry_after=10,  # Default retry after
    )

    # Get all data using parallel processing and zip the results
    start_time = time.time()
    await spotify_data_getter.get_all_data_parallel()
    end_time = time.time()

    print(f"\nAll data retrieved and zipped in {end_time - start_time:.2f} seconds")
    print(f"Data saved to: {spotify_data_getter.raw_data_location}")


if __name__ == "__main__":
    asyncio.run(main())
