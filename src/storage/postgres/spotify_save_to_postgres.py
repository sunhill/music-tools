import asyncio
import json
import logging
import os
from configparser import ConfigParser

import asyncpg

from spotify.spotify_save import SpotifySave
from spotify.spotify_utils import (
    setup_app_logging,
    unzip_data_from_zip,
    most_recent_directory, get_config_location,
)

BATCH_SIZE = 500

logger = logging.getLogger(__name__)


class SpotifyToPostgres(SpotifySave):

    def __init__(self, user_id="") -> None:
        super().__init__()
        self.user_id = user_id
        self.config_location = get_config_location()
        self.config_parser = ConfigParser()
        self.config_parser.read(self.config_location)
        running_in_docker = os.getenv("RUNNING_IN_DOCKER", "False")
        logger.info(f"Running in docker: {running_in_docker}")
        if running_in_docker == "True":
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
        logger.info(f"Using raw data location {self.raw_data_location}")
        self.playlist_folder = self.config_parser["spotify"]["playlist_location"]
        self.playlist_location = os.path.join(self.save_location, self.playlist_folder)
        logger.debug("Playlist Location: " + self.playlist_location)
        if not os.path.exists(self.playlist_location):
            os.makedirs(self.playlist_location)
            logger.debug("Created Playlist Location: " + self.playlist_location)

        self.individual_playlist_folder = self.config_parser["spotify"]["individual_playlist_location"]
        self.individual_playlist_location = os.path.join(self.save_location, self.individual_playlist_folder)
        logger.debug("Individual Playlist Location: " + self.individual_playlist_location)
        if not os.path.exists(self.individual_playlist_location):
            os.makedirs(self.individual_playlist_location)
            logger.debug(
                "Created Individual Playlist Location: "
                + self.individual_playlist_location
            )

    async def save_all_data(self, all_data: dict):
        most_recent = most_recent_directory(self.raw_data_location)
        await self.save_artists(
            unzip_data_from_zip(
                f"{self.raw_data_location}/{most_recent}/saved_artists.gz"
            )
        )
        await self.save_albums(
            unzip_data_from_zip(
                f"{self.raw_data_location}/{most_recent}/saved_albums.gz"
            )
        )
        # await self.save_album_tracks(
        #     unzip_data_from_zip(
        #         f"{self.raw_data_location}/{most_recent}/saved_album_tracks.gz"
        #     )
        # )
        await self.save_tracks(
            unzip_data_from_zip(
                f"{self.raw_data_location}/{most_recent}/saved_tracks.gz"
            )
        )
        # await self.save_playlist_tracks(unzip_data_from_zip(f"{self.raw_data_location}/{most_recent}/playlists.gz"), unzip_data_from_zip(f"{self.raw_data_location}/{most_recent}/playlist_tracks.gz"))
        # await self.save_playlist_details(unzip_data_from_zip(f"{self.raw_data_location}/{most_recent}/playlists.gz"), unzip_data_from_zip(f"{self.raw_data_location}/{most_recent}/playlist_tracks.gz"))
        # await self.save_individual_playlists(unzip_data_from_zip(f"{self.raw_data_location}/{most_recent}/playlists.gz"), unzip_data_from_zip(f"{self.raw_data_location}/{most_recent}/playlist_tracks.gz"))
        # await self.save_unique_tracks_in_playlists(unzip_data_from_zip(f"{self.raw_data_location}/{most_recent}/unique_playlist_tracks.gz"))
        # await self.save_unique_artists_in_playlists(unzip_data_from_zip(f"{self.raw_data_location}/{most_recent}/unique_playlist_artists.gz"))
        #

    def save_unique_artists_in_playlists(self, unique_artists_in_playlists: dict):
        pass

    def save_playlist_tracks(self, playlists: list, playlist_tracks: dict):
        pass

    def save_playlist_details(self, playlists: list, playlist_tracks: dict):
        pass

    async def save_album_tracks(self, tracks: list):
        pass

    async def create_artist(
            self,
            pool,
            name,
            external_urls,
            followers,
            genres,
            href,
            images,
            popularity,
            type,
            uri,
    ):
        async with pool.acquire() as conn:
            artist_id = await conn.execute(
                "INSERT INTO artists (name, external_urls, followers, genres, href, images, popularity, type, uri) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) "
                "ON CONFLICT (uri) DO UPDATE SET name=EXCLUDED.name RETURNING "
                "id;",
                name,
                external_urls,
                followers,
                genres,
                href,
                images,
                popularity,
                type,
                uri,
            )
            print(artist_id)
            return artist_id

    async def save_artists(self, artists: list):
        logger.info("save_artists_to_postgres")
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                for batch in self._artist_batches(artists):
                    await conn.executemany(
                        "INSERT INTO artists (name, external_urls, followers, genres, href, images, popularity, type, uri) "
                        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) "
                        "ON CONFLICT (uri) DO NOTHING;",
                        [
                            (
                                artist["name"],
                                json.dumps(artist["external_urls"]),
                                json.dumps(artist["followers"]),
                                artist["genres"],
                                artist["href"],
                                json.dumps(artist["images"]),
                                artist["popularity"],
                                artist["type"],
                                artist["uri"],
                            )
                            for artist in batch
                        ],
                    )
                    print(f"Inserted {len(batch)} artists")

        await pool.close()

    async def save_albums(self, albums: list):
        logger.info("save_albums_to_postgres")
        pool = await self.get_pool()
        logger.debug(f"first albums is {albums[0]}")

        async with pool.acquire() as conn:
            async with conn.transaction():
                for batch in self._album_batches(albums):
                    await conn.executemany(
                        "INSERT INTO albums (album_type, artists, external_urls, href, "
                        "images, name, release_date, release_date_precision, total_tracks, uri) "
                        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) "
                        "ON CONFLICT (uri) DO NOTHING;",
                        [
                            (
                                album["album_type"],
                                json.dumps(album["artists"]),
                                json.dumps(album["external_urls"]),
                                album["href"],
                                json.dumps(album["images"]),
                                album["name"],
                                album["release_date"],
                                album["release_date_precision"],
                                album["total_tracks"],
                                album["uri"],
                            )
                            for album in batch
                        ],
                    )
                    print(f"Inserted {len(batch)} albums")

        await pool.close()

    async def save_tracks(self, tracks: list):
        logger.info("save_tracks_to_postgres")
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                for batch in self._track_batches(tracks):
                    await conn.executemany(
                        "INSERT INTO tracks (album, artists, available_markets, disc_number, duration_ms, explicit, "
                        "external_urls, href, name, popularity, preview_url, track_number, type, uri) "
                        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14) "
                        "ON CONFLICT (uri) DO NOTHING;",
                        [
                            (
                                json.dumps(track["album"]),
                                json.dumps(track["artists"]),
                                track["available_markets"],
                                track["disc_number"],
                                track["duration_ms"],
                                track["explicit"],
                                json.dumps(track["external_urls"]),
                                track["href"],
                                track["name"],
                                track["popularity"],
                                track["preview_url"],
                                track["track_number"],
                                track["type"],
                                track["uri"],
                            )
                            for track in batch
                        ],
                    )
                    print(f"Inserted {len(batch)} tracks")

    def _album_batches(self, albums):
        for i in range(0, len(albums), BATCH_SIZE):
            yield [album for album in albums[i: i + BATCH_SIZE]]

    def _artist_batches(self, artists):
        for i in range(0, len(artists), BATCH_SIZE):
            yield artists[i: i + BATCH_SIZE]

    def _track_batches(self, tracks):
        logger.debug(f"track first is {tracks[0]}")
        for i in range(0, len(tracks), BATCH_SIZE):
            yield [track for track in tracks[i: i + BATCH_SIZE]]

    async def get_pool(self):
        pool = await asyncpg.create_pool(
            database=os.environ.get("POSTGRES_DATABASE", "spotify"),
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=os.environ.get("POSTGRES_PORT", 5432),
            # user=os.environ.get("POSTGRES_USER", "postgres"),
            # TODO fix this
            user=os.environ.get("POSTGRES_USER", "simon"),
            password=os.environ.get("POSTGRES_PASSWORD"),
        )
        return pool

    def save_individual_playlists(self, playlists: list, playlist_tracks: dict):
        # not implemented
        pass

    def save_unique_tracks_in_playlists(self, unique_tracks_in_playlists: dict):
        # not implemented
        pass


def main():
    setup_app_logging(logger, logging.DEBUG)
    logger.info("Starting save to postgres")

    spotify_to_postgres: SpotifyToPostgres = SpotifyToPostgres()

    asyncio.run(spotify_to_postgres.save_all_data({}))


if __name__ == "__main__":
    main()
