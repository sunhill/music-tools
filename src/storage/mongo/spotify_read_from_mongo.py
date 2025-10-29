import logging

from pymongo import MongoClient
from pymongo.cursor import Cursor
from pymongo.database import Database

from spotify.spotify_utils import setup_app_logging

logger = logging.getLogger(__name__)


class SpotifyFromMongo:
    client: MongoClient
    db: Database

    def __init__(self, mongodb_server="mongodb://localhost:27017/") -> None:
        super().__init__()
        self.client = MongoClient(mongodb_server)
        self.db = self.client.spotify_db

    def get_liked_artists(self) -> list[dict]:
        cursor: Cursor = self.db["spotify_saved_artist"].find()
        artists = []
        for doc in cursor:
            artists.append(
                {
                    "id": doc["id"],
                    "name": doc["name"],
                }
            )
        return artists

    def get_liked_albums(self) -> list[dict]:
        cursor: Cursor = self.db["spotify_saved_album"].find()
        albums = []
        for doc in cursor:
            albums.append(
                {
                    "id": doc["id"],
                    "name": doc["name"],
                    "artists": doc["artists"][0]["name"],
                }
            )
        return albums

    def get_liked_tracks(self) -> list[dict]:
        cursor: Cursor = self.db["spotify_saved_track"].find()
        tracks = []
        for doc in cursor:
            tracks.append(
                {
                    "id": doc["id"],
                    "name": doc["name"],
                    "artists": doc["artists"][0]["name"],
                }
            )
        return tracks

    def get_unique_playlist_tracks(self) -> list[dict]:
        cursor: Cursor = self.db["spotify_playlist_unique_track"].find()
        tracks = []
        for doc in cursor:
            tracks.append(
                {
                    "id": doc["id"],
                    "playlist_id": doc["playlist_id"],
                    "name": doc["name"],
                    "artists": doc["artists"][0]["name"],
                }
            )

        return tracks

    def get_playlists(self) -> list[dict]:
        cursor: Cursor = self.db["spotify_playlist"].find()
        playlists = []
        for doc in cursor:
            playlists.append(
                {
                    "id": doc["id"],
                    "name": doc["name"],
                    "owner": doc["owner"]["display_name"],
                }
            )

        return playlists

    def get_playlist_tracks(self) -> list[dict]:
        cursor: Cursor = self.db["spotify_playlist_track"].find()
        tracks = []
        for doc in cursor:
            tracks.append(
                {
                    "id": doc["id"],
                    "playlist_id": doc["playlist_id"],
                    "name": doc["name"],
                    "artists": doc["artist"],
                }
            )

        return tracks

    def get_playlist_unique_artists(self) -> list[dict]:
        cursor: Cursor = self.db["spotify_playlist_unique_artist"].find()
        artists = []
        for doc in cursor:
            artists.append(
                {
                    "id": doc["id"],
                    "name": doc["name"],
                }
            )

        return artists

    def get_liked_album_tracks(self) -> list[dict]:
        cursor: Cursor = self.db["spotify_saved_album_track"].find()
        tracks = []
        for doc in cursor:
            tracks.append(
                {"id": doc["id"], "name": doc["name"], "artists": doc["artist"]}
            )

        return tracks


def dict2obj(d: dict) -> object:
    # checking whether object d is an
    # instance of class list
    if isinstance(d, list):
        d = [dict2obj(x) for x in d]

        # if d is not an instance of dict then
    # directly object is returned
    if not isinstance(d, dict):
        return d

    # declaring a class
    class C:
        pass

    # constructor of the class passed to obj
    obj = C()

    for k in d:
        obj.__dict__[k] = dict2obj(d[k])

    return obj


def main():
    setup_app_logging(logger, logging.DEBUG)
    spotify_from_mongo: SpotifyFromMongo = SpotifyFromMongo()
    # spotify_from_mongo.show_followed_artists()
    spotify_from_mongo.get_playlist_tracks()
    # spotify_from_mongo.show_liked_tracks()
    #
    # spotify_from_mongo.show_playlists()
    # spotify_from_mongo.show_playlist_tracks()
    # spotify_from_mongo.show_unique_playlist_tracks()


if __name__ == "__main__":
    main()
