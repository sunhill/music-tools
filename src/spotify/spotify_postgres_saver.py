import asyncio
import json
import logging
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

import asyncpg
import sys
import time

from spotify.spotify_utils import (
    SAVED_ARTISTS,
    SAVED_ALBUMS,
    PLAYLIST_TRACKS,
    PLAYLISTS,
    SAVED_TRACKS,
    get_latest_zip,
    unzip_data_from_zip,
    get_data_location,
)
from src.spotify.spotify_get_data import AsyncSpotifyDataGetter
from src.spotify.spotify_models import (
    SpotifyArtist,
    SpotifyAlbum,
    SpotifyTrack,
    SpotifyPlaylist,
    SpotifyImage,
)

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def to_jsonb(value: Any) -> str:
    """Convert a Python value to a JSON string for PostgreSQL JSONB."""
    return json.dumps(value)


def get_largest_image(images: List[SpotifyImage]) -> Optional[SpotifyImage]:
    """Get the largest image from a list of SpotifyImage instances based on height."""
    if not images:
        logger.debug("No images provided")
        return None

    try:
        largest = max(images, key=lambda img: img.height)
        logger.debug(f"Largest image found: {largest}")
        return largest.url
    except Exception as e:
        logger.error(f"Error finding largest image: {e}", exc_info=True)
        return None


class SpotifyPostgresSaver:
    """Class to save Spotify data to PostgreSQL database."""

    def __init__(
        self,
        db_host: str = "localhost",
        db_port: int = 5432,
        db_name: str = "spotify",
        db_user: str = "postgres",
        db_password: str = "postgres",
        schema: str = "public",
    ):
        """Initialize the PostgreSQL saver.

        Args:
            db_host: Database host
            db_port: Database port
            db_name: Database name
            db_user: Database user
            db_password: Database password
            schema: Database schema
        """
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.schema = schema
        self.pool = None

    async def connect(self):
        """Connect to the PostgreSQL database."""
        try:
            logger.info(
                f"Connecting to PostgreSQL database {self.db_name} on {self.db_host}:{self.db_port} as {self.db_user}"
            )

            # Test connection parameters
            logger.debug(
                f"Connection parameters: host={self.db_host}, port={self.db_port}, database={self.db_name}, user={self.db_user}"
            )

            # Create connection pool
            logger.debug("Creating connection pool...")
            self.pool = await asyncpg.create_pool(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
            )

            if not self.pool:
                logger.error("Failed to create connection pool")
                raise Exception("Failed to create connection pool")

            logger.info(
                f"Connected to PostgreSQL database {self.db_name} on {self.db_host}:{self.db_port}"
            )

            # Set the schema after connection
            logger.debug(f"Setting schema to {self.schema}...")
            async with self.pool.acquire() as conn:
                await conn.execute(f'SET search_path TO {self.schema}')
                logger.info(f"Set schema to {self.schema}")

            # Create tables if they don't exist
            logger.debug("Creating tables if they don't exist...")
            await self._create_tables()
            logger.info("Tables created or verified")

        except asyncpg.exceptions.InvalidAuthorizationSpecificationError as e:
            logger.error(f"Authentication error: {str(e)}")
            logger.error(
                "Please check your database credentials and make sure the user exists."
            )
            logger.error(
                "You can run ./setup_postgres.sh to set up the database and user."
            )
            raise
        except asyncpg.exceptions.ConnectionDoesNotExistError as e:
            logger.error(f"Connection error: {str(e)}")
            logger.error("Please check if PostgreSQL is running and accessible.")
            logger.error("You can run ./setup_postgres.sh to set up PostgreSQL.")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}", exc_info=True)
            raise

    async def disconnect(self):
        """Disconnect from the PostgreSQL database."""
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from PostgreSQL database")

    async def _create_tables(self):
        """Create the necessary tables if they don't exist."""
        # Read the SQL script from the file
        script_path = os.path.join(
            os.path.dirname(__file__), "schema", "create_tables.sql"
        )
        with open(script_path, "r") as f:
            create_tables_sql = f.read()

        async with self.pool.acquire() as conn:
            await conn.execute(create_tables_sql)
            logger.info("Created or verified all necessary tables")

    async def save_artists(self, artists: List[Dict[str, Any]]):
        """Save artists to the database.

        Args:
            artists: List of artist dictionaries
        """
        if not artists:
            logger.info("No artists to save")
            return

        logger.info(f"Saving {len(artists)} artists to database")

        # Convert to Pydantic models
        artist_models = [SpotifyArtist(**artist) for artist in artists]

        async with self.pool.acquire() as conn:
            # Use a transaction to ensure all artists are saved or none
            async with conn.transaction():
                for artist in artist_models:
                    # Check if artist already exists
                    existing = await conn.fetchval(
                        "SELECT id FROM spot_artists WHERE id = $1", artist.id
                    )

                    if not existing:
                        # Insert artist
                        await conn.execute(
                            """
                            INSERT INTO spot_artists (
                                id, name, uri, href, external_urls, image, genres, 
                                popularity, followers, spotify_url, created_at
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        """,
                            artist.id,
                            artist.name,
                            artist.uri,
                            artist.href,
                            to_jsonb(artist.external_urls),
                            get_largest_image(artist.images),
                            to_jsonb(artist.genres),
                            artist.popularity,
                            artist.followers.total,
                            artist.spotify_url,
                            artist.created_at,
                        )

        logger.info(f"Saved {len(artists)} artists to database")

    async def save_albums(self, albums: List[Dict[str, Any]]):
        """Save albums to the database.

        Args:
            albums: List of album dictionaries
        """
        if not albums:
            logger.info("No albums to save")
            return

        logger.info(f"Saving {len(albums)} albums to database")

        # Convert to Pydantic models
        album_models = [SpotifyAlbum(**album["album"]) for album in albums]

        async with self.pool.acquire() as conn:
            # Use a transaction to ensure all albums are saved or none
            async with conn.transaction():
                for album in album_models:
                    # Check if album already exists
                    existing = await conn.fetchval(
                        "SELECT id FROM spot_albums WHERE id = $1", album.id
                    )

                    if not existing:
                        # Insert album
                        await conn.execute(
                            """
                            INSERT INTO spot_albums (
                                id, name, uri, href, external_urls, image, 
                                release_date, release_date_precision, total_tracks, 
                                album_type, available_markets, spotify_url, created_at
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        """,
                            album.id,
                            album.name,
                            album.uri,
                            album.href,
                            to_jsonb(album.external_urls),
                            get_largest_image(album.images),
                            album.release_date,
                            album.release_date_precision,
                            album.total_tracks,
                            album.album_type,
                            to_jsonb(album.available_markets),
                            album.spotify_url,
                            album.created_at,
                        )

                        # Insert album-artist relationships
                        for artist in album.artists:
                            # Check if artist exists, if not, insert it
                            artist_exists = await conn.fetchval(
                                "SELECT id FROM spot_artists WHERE id = $1", artist.id
                            )

                            if not artist_exists:
                                await conn.execute(
                                    """
                                    INSERT INTO spot_artists (
                                        id, name, uri, href, external_urls, image, 
                                        genres, popularity, followers, spotify_url, created_at
                                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                                """,
                                    artist.id,
                                    artist.name,
                                    artist.uri,
                                    artist.href,
                                    to_jsonb(artist.external_urls),
                                    get_largest_image(artist.images),
                                    to_jsonb(artist.genres),
                                    artist.popularity,
                                    artist.followers.total,
                                    artist.spotify_url,
                                    artist.created_at,
                                )

                            # Insert album-artist relationship
                            await conn.execute(
                                """
                                INSERT INTO spot_album_artists (album_id, artist_id)
                                VALUES ($1, $2)
                                ON CONFLICT (album_id, artist_id) DO NOTHING
                            """,
                                album.id,
                                artist.id,
                            )

        logger.info(f"Saved {len(albums)} albums to database")

    async def save_tracks(self, tracks: List[Dict[str, Any]]):
        """Save tracks to the database.

        Args:
            tracks: List of track dictionaries
        """
        if not tracks:
            logger.info("No tracks to save")
            return

        logger.info(f"Saving {len(tracks)} tracks to database")

        # Convert to Pydantic models
        track_models = [SpotifyTrack(**track["track"]) for track in tracks]

        async with self.pool.acquire() as conn:
            # Use a transaction to ensure all tracks are saved or none
            async with conn.transaction():
                for track in track_models:
                    # Check if track already exists
                    existing = await conn.fetchval(
                        "SELECT id FROM spot_tracks WHERE id = $1", track.id
                    )

                    if not existing:
                        # Insert track
                        await conn.execute(
                            """
                            INSERT INTO spot_tracks (
                                id, name, uri, href, external_urls, duration_ms, 
                                preview_url, album_id, isrc, 
                                spotify_url, created_at
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        """,
                            track.id,
                            track.name,
                            track.uri,
                            track.href,
                            to_jsonb(track.external_urls),
                            track.duration_ms,
                            track.preview_url,
                            track.album.id,
                            track.external_ids.isrc,
                            track.spotify_url,
                            track.created_at,
                        )

                        # Insert track-artist relationships
                        for artist in track.artists:
                            # Check if artist exists, if not, insert it
                            artist_exists = await conn.fetchval(
                                "SELECT id FROM spot_artists WHERE id = $1", artist.id
                            )

                            if not artist_exists:
                                await conn.execute(
                                    """
                                    INSERT INTO spot_artists (
                                        id, name, uri, href, external_urls, image, 
                                        genres, popularity, followers, spotify_url, created_at
                                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                                """,
                                    artist.id,
                                    artist.name,
                                    artist.uri,
                                    artist.href,
                                    to_jsonb(artist.external_urls),
                                    get_largest_image(artist.images),
                                    to_jsonb(artist.genres),
                                    artist.popularity,
                                    artist.followers.total,
                                    artist.spotify_url,
                                    artist.created_at,
                                )

                            # Insert track-artist relationship
                            await conn.execute(
                                """
                                INSERT INTO spot_track_artists (track_id, artist_id)
                                VALUES ($1, $2)
                                ON CONFLICT (track_id, artist_id) DO NOTHING
                            """,
                                track.id,
                                artist.id,
                            )

        logger.info(f"Saved {len(tracks)} tracks to database")

    async def save_playlists(self, playlists: List[Dict[str, Any]]):
        """Save playlists to the database.

        Args:
            playlists: List of playlist dictionaries
        """
        if not playlists:
            logger.info("No playlists to save")
            return

        logger.info(f"Saving {len(playlists)} playlists to database")

        # Convert to Pydantic models
        playlist_models = [SpotifyPlaylist(**playlist) for playlist in playlists]

        async with self.pool.acquire() as conn:
            # Use a transaction to ensure all playlists are saved or none
            async with conn.transaction():
                for playlist in playlist_models:
                    # Check if playlist already exists
                    existing = await conn.fetchval(
                        "SELECT id FROM spot_playlists WHERE id = $1", playlist.id
                    )

                    if not existing:
                        # Insert playlist
                        await conn.execute(
                            """
                            INSERT INTO spot_playlists (
                                id, name, uri, href, external_urls, description, 
                                owner, public, tracks_count, spotify_url, created_at
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        """,
                            playlist.id,
                            playlist.name,
                            playlist.uri,
                            playlist.href,
                            to_jsonb(playlist.external_urls),
                            playlist.description,
                            # get_largest_image(playlist.images),
                            playlist.owner.display_name,
                            playlist.public,
                            playlist.tracks.total,
                            playlist.spotify_url,
                            playlist.created_at,
                        )

        logger.info(f"Saved {len(playlists)} playlists to database")

    async def save_playlist_tracks(
        self, playlist_tracks: Dict[str, List[Dict[str, Any]]]
    ):
        """Save playlist tracks to the database.

        Args:
            playlist_tracks: Dictionary mapping playlist IDs to lists of track dictionaries
        """
        if not playlist_tracks:
            logger.info("No playlist tracks to save")
            return

        logger.info(f"Saving tracks for {len(playlist_tracks)} playlists to database")

        async with self.pool.acquire() as conn:
            # Use a transaction to ensure all playlist tracks are saved or none
            async with conn.transaction():
                for playlist_id, tracks in playlist_tracks.items():
                    for track in tracks:
                        # Check if track exists in the database
                        track_exists = await conn.fetchval(
                            "SELECT id FROM spot_tracks WHERE id = $1",
                            track["track"]["id"],
                        )

                        if not track_exists:
                            # Insert track
                            await conn.execute(
                                """
                                INSERT INTO spot_tracks (
                                id, name, uri, href, external_urls, duration_ms, 
                                preview_url, album_id, isrc, 
                                spotify_url, created_at
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                            """,
                                track["track"]["id"],
                                track["track"]["name"],
                                track["track"]["uri"],
                                track["track"]["href"],
                                to_jsonb(track["track"]["external_urls"]),
                                track["track"]["duration_ms"],
                                track["track"].get("preview_url"),
                                track["track"]["album"]["id"],
                                track["track"].get("external_ids", {}).get("isrc"),
                                track["track"].get("external_urls", {}).get("spotify"),
                                datetime.now(),
                            )

                            # Insert track-artist relationships
                            for artist in track["track"]["artists"]:
                                # Check if artist exists, if not, insert it
                                artist_exists = await conn.fetchval(
                                    "SELECT id FROM spot_artists WHERE id = $1",
                                    artist["id"],
                                )

                                if not artist_exists:
                                    if "followers" in artist:
                                        followers_total = artist.get("followers").get("total",0)
                                    else:
                                        followers_total = 0
                                    await conn.execute(
                                        """
                                        INSERT INTO spot_artists (
                                            id, name, uri, href, external_urls, image, 
                                            genres, popularity, followers, spotify_url, created_at
                                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                                    """,
                                        artist["id"],
                                        artist["name"],
                                        artist["uri"],
                                        artist["href"],
                                        to_jsonb(artist["external_urls"]),
                                        get_largest_image(artist.get("images", [])),
                                        to_jsonb(artist.get("genres")),
                                        artist.get("popularity"),
                                        followers_total,
                                        artist.get("external_urls", {}).get("spotify"),
                                        datetime.now(),
                                    )

                                # Insert track-artist relationship
                                await conn.execute(
                                    """
                                    INSERT INTO spot_track_artists (track_id, artist_id)
                                    VALUES ($1, $2)
                                    ON CONFLICT (track_id, artist_id) DO NOTHING
                                """,
                                    track["track"]["id"],
                                    artist["id"],
                                )

                        # Insert playlist-track relationship
                        added_at = datetime.fromisoformat(
                            track["added_at"].replace("Z", ".000")
                        )

                        created_at = datetime.now()
                        logger.debug(f"added_at: {added_at}, created_at: {created_at}")
                        await conn.execute(
                            """
                            INSERT INTO spot_playlist_tracks (playlist_id, track_id, added_at, created_at)
                            VALUES ($1, $2, $3, $4)
                            ON CONFLICT (playlist_id, track_id) DO NOTHING
                        """,
                            playlist_id,
                            track["track"]["id"],
                            added_at,
                            created_at,
                        )

        logger.info(f"Saved tracks for {len(playlist_tracks)} playlists to database")

    async def save_all_data(self, data: Dict[str, Any]):
        """Save all Spotify data to the database.

        Args:
            data: Dictionary containing all Spotify data
        """
        logger.info("Saving all Spotify data to database")

        # Connect to the database
        await self.connect()

        try:
            # Save artists
            if SAVED_ARTISTS in data:
                await self.save_artists(data[SAVED_ARTISTS])

            # Save albums
            if SAVED_ALBUMS in data:
                await self.save_albums(data[SAVED_ALBUMS])

            # Save tracks
            if SAVED_TRACKS in data:
                await self.save_tracks(data[SAVED_TRACKS])

            # Save playlists
            if PLAYLISTS in data:
                await self.save_playlists(data[PLAYLISTS])

            # Save playlist tracks
            if PLAYLIST_TRACKS in data:
                await self.save_playlist_tracks(data[PLAYLIST_TRACKS])

            logger.info("All Spotify data saved to database")
        finally:
            # Disconnect from the database
            await self.disconnect()


async def save_spotify_data_to_postgres(
    db_host: str = "localhost",
    db_port: int = 5432,
    db_name: str = "spotify",
    db_user: str = "postgres",
    db_password: str = "postgres",
    schema: str = "public",
    zip_first: bool = True,
    use_zip_data: bool = False,
) -> None:
    """
    Save Spotify data to PostgreSQL database.

    Args:
        db_host: Database host
        db_port: Database port
        db_name: Database name
        db_user: Database user
        db_password: Database password
        schema: Database schema
        zip_first: Whether to zip data before saving to database
        use_zip_data: Whether to use the latest saved zip data instead of fetching from Spotify API
    """
    logger.info("Initializing Spotify data export to PostgreSQL")
    start_time = time.time()

    # Initialize database saver
    db_saver = SpotifyPostgresSaver(
        db_host=db_host,
        db_port=db_port,
        db_name=db_name,
        db_user=db_user,
        db_password=db_password,
        schema=schema,
    )
    logger.debug("Database saver initialized")

    try:
        # Connect to database
        logger.info("Connecting to database...")
        await db_saver.connect()
        logger.info("Connected to database successfully")

        if use_zip_data:
            # Load data from zip files
            logger.info("Loading data from zip files...")
            data_location = await get_data_location()
            latest_zip = get_latest_zip(data_location)
            
            if not latest_zip:
                logger.error("No zip files found. Please run the script without --use-zip-data first.")
                return
                
            logger.info(f"Using zip file: {latest_zip}")
            all_data = unzip_data_from_zip(latest_zip)
            
            # Save artists
            if SAVED_ARTISTS in all_data:
                logger.debug("Saving artists from zip data...")
                await db_saver.save_artists(all_data[SAVED_ARTISTS])
                logger.info(f"Saved {len(all_data[SAVED_ARTISTS])} artists")
            
            # Save albums
            if SAVED_ALBUMS in all_data:
                logger.debug("Saving albums from zip data...")
                await db_saver.save_albums(all_data[SAVED_ALBUMS])
                logger.info(f"Saved {len(all_data[SAVED_ALBUMS])} albums")
            
            # Save tracks
            if SAVED_TRACKS in all_data:
                logger.debug("Saving tracks from zip data...")
                await db_saver.save_tracks(all_data[SAVED_TRACKS])
                logger.info(f"Saved {len(all_data[SAVED_TRACKS])} tracks")
            
            # Save playlists
            if PLAYLISTS in all_data:
                logger.debug("Saving playlists from zip data...")
                await db_saver.save_playlists(all_data[PLAYLISTS])
                logger.info(f"Saved {len(all_data[PLAYLISTS])} playlists")
            
            # # Save playlist tracks
            # if PLAYLIST_TRACKS in all_data:
            #     logger.debug("Saving playlist tracks from zip data...")
            #     tracks = all_data[PLAYLIST_TRACKS]
            #     await db_saver.save_playlist_tracks(tracks)
        else:
            # Initialize Spotify data getter
            spotify_data_getter = AsyncSpotifyDataGetter()
            logger.debug("Spotify data getter initialized")

            # Get Spotify data
            logger.info("Fetching Spotify data...")

            # Get saved artists
            logger.debug("Fetching saved artists...")
            saved_artists = await spotify_data_getter.get_all_saved_artists_parallel()
            logger.info(f"Found {len(saved_artists)} saved artists")

            # Save artists
            logger.debug("Saving artists...")
            await db_saver.save_artists(saved_artists)
            logger.info(f"Saved {len(saved_artists)} artists")

            # Get saved albums
            logger.debug("Fetching saved albums...")
            saved_albums = await spotify_data_getter.get_all_saved_albums_parallel()
            logger.info(f"Found {len(saved_albums)} saved albums")

            # Save albums
            logger.debug("Saving albums...")
            await db_saver.save_albums(saved_albums)
            logger.info(f"Saved {len(saved_albums)} albums")

            # Get saved tracks
            logger.debug("Fetching saved tracks...")
            saved_tracks = await spotify_data_getter.get_all_saved_tracks_parallel()
            logger.info(f"Found {len(saved_tracks)} saved tracks")

            # Save tracks
            logger.debug("Saving tracks...")
            await db_saver.save_tracks(saved_tracks)
            logger.info(f"Saved {len(saved_tracks)} tracks")

            # Get playlists
            logger.debug("Fetching playlists...")
            playlists = await spotify_data_getter.get_all_playlists_parallel()
            logger.info(f"Found {len(playlists)} playlists")

            # Save playlists
            logger.debug("Saving playlists...")
            await db_saver.save_playlists(playlists)
            logger.info(f"Saved {len(playlists)} playlists")

            # Get playlist tracks
            logger.debug("Fetching playlist tracks...")
            playlist_tracks = {}
            for playlist in playlists:
                playlist_id = playlist.id
                logger.debug(f"Fetching tracks for playlist {playlist_id}...")
                tracks = await spotify_data_getter.get_playlist_tracks_parallel(playlist_id)
                playlist_tracks[playlist_id] = tracks
                logger.debug(f"Found {len(tracks)} tracks in playlist {playlist_id}")

            # Save playlist tracks
            # logger.debug("Saving playlist tracks...")
            # for playlist_id, tracks in playlist_tracks.items():
            #     logger.debug(f"Saving tracks for playlist {playlist_id}...")
            #     await db_saver.save_playlist_tracks(playlist_id, tracks)
            #     logger.debug(f"Saved {len(tracks)} tracks for playlist {playlist_id}")

        end_time = time.time()
        logger.info(f"Data export completed in {end_time - start_time:.2f} seconds")

    except Exception as e:
        logger.error(f"Error during data export: {str(e)}", exc_info=True)
        raise
    finally:
        # Disconnect from database
        logger.info("Disconnecting from database...")
        await db_saver.disconnect()
        logger.info("Disconnected from database")


def main():
    """Main function to run the script."""
    import time
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Save Spotify data to PostgreSQL")
    parser.add_argument("--db-host", default="localhost", help="Database host")
    parser.add_argument("--db-port", type=int, default=5432, help="Database port")
    parser.add_argument("--db-name", default="spotify", help="Database name")
    parser.add_argument("--db-user", default="postgres", help="Database user")
    parser.add_argument("--db-password", default="postgres", help="Database password")
    parser.add_argument("--schema", default="public", help="Database schema")
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="Don't zip data before saving to PostgreSQL",
    )
    parser.add_argument(
        "--use-zip-data",
        action="store_true",
        help="Use the latest saved zip data instead of fetching from Spotify API",
    )

    args = parser.parse_args()

    # Set up logging
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the script
    start_time = time.time()

    try:
        # Simple approach - just try to run the async function
        asyncio.run(
            save_spotify_data_to_postgres(
                db_host=args.db_host,
                db_port=args.db_port,
                db_name=args.db_name,
                db_user=args.db_user,
                db_password=args.db_password,
                schema=args.schema,
                zip_first=False,
                use_zip_data=True,
            )
        )
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e):
            logger.error(
                "Error: Cannot run in an environment with an existing event loop."
            )
            logger.error(
                "Please run this script directly with Python, not from within another async application."
            )
            logger.error("Example: python -m src.spotify.spotify_postgres_saver")
            exit(1)
        else:
            # Re-raise other RuntimeErrors
            raise

    end_time = time.time()
    print(f"\nAll data saved in {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    main()
