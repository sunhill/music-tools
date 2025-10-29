import asyncio
import json
import logging
import os
from typing import List

import asyncpg

from spotify.spotify_utils import setup_app_logging

logger = logging.getLogger(__name__)


class SpotifyFromPostgres:

    def __init__(self) -> None:
        super().__init__()

    async def get_pool(self):
        pool = await asyncpg.create_pool(
            database=os.environ.get("POSTGRES_DATABASE", "spotify"),
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=os.environ.get("POSTGRES_PORT", 5432),
            # user=os.environ.get("POSTGRES_USER", "postgres"),
            user=os.environ.get("POSTGRES_USER", "simon"),
            password=os.environ.get("POSTGRES_PASSWORD"),
        )
        return pool

    async def get_liked_artists(self) -> list[dict]:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            artists: List[asyncpg.Record] = await conn.fetch("SELECT * FROM artists;")
            artists_out: List[dict] = []
            # TODO change messy
            for artist in artists:
                artist_out = dict(artist)
                for key, value in artist_out.items():
                    if key == "images":
                        value = json.loads(value)
                        artist_out[key] = value
                    print(f"{key} = {value}, type = {type(value)}")
                artists_out.append(artist_out)

            return artists_out


async def main():
    setup_app_logging(logger, logging.DEBUG)
    spotify_from_postgres: SpotifyFromPostgres = SpotifyFromPostgres()
    liked_artists = await spotify_from_postgres.get_liked_artists()


if __name__ == "__main__":
    asyncio.run(main())
