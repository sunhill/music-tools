import logging
import os
from configparser import ConfigParser

from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from spotify.spotify_save import SpotifySave
from spotify.spotify_utils import setup_app_logging, unzip_data, get_config_location

logger = logging.getLogger(__name__)


class SpotifyToMongo(SpotifySave):
    client: MongoClient
    db: Database

    def __init__(self, mongodb_server="mongodb://localhost:27017/") -> None:
        super().__init__()
        self.client = MongoClient(mongodb_server)
        self.db = self.client.get_database("spotify_db")
        config_parser = ConfigParser()
        config_parser.read(get_config_location())

        self.save_location = config_parser["spotify"]["save_location"]
        self.raw_data_location = (
            self.save_location + config_parser["spotify"]["raw_data_location"]
        )

    def save_individual_playlists(self, playlists: list, playlist_tracks: dict):
        # not implemented
        pass

    def save_unique_tracks_in_playlists(self, unique_tracks_in_playlists: dict):
        logger.info("save_unique_tracks_in_playlists_to_mongo")

        collection_name = "spotify_playlist_unique_track"
        self.db.drop_collection(collection_name)
        playlist_unique_track_collection: Collection = self.db.create_collection(
            collection_name
        )

        playlist_unique_track_collection.drop_indexes()
        playlist_unique_track_collection.create_index(
            name="unique_playlist_track_index",
            keys=[("id", ASCENDING), ("url", ASCENDING)],
            unique=True,
        )
        for value in unique_tracks_in_playlists.values():
            artists: list = value["artists"]
            value["artist"] = self.get_artist_from_artists(artists)
            try:
                playlist_unique_track_collection.insert_one(value)
            except DuplicateKeyError as e:
                logger.debug(value)
                logger.debug(e)

        # playlist_unique_track_collection.insert_many(unique_tracks_in_playlists.values())

    @staticmethod
    def get_artist_from_artists(artists):

        return " & ".join(artist["name"] for artist in artists)

    def save_unique_artists_in_playlists(self, unique_artists_in_playlists: dict):
        logger.info("save_unique_artists_in_playlists_to_mongo")

        collection_name = "spotify_playlist_unique_artist"
        self.db.drop_collection(collection_name)
        playlist_unique_artist_collection: Collection = self.db.create_collection(
            collection_name
        )

        playlist_unique_artist_collection.drop_indexes()
        playlist_unique_artist_collection.create_index(
            name="unique_playlist_artist_index", keys=[("id", ASCENDING)], unique=True
        )
        for value in unique_artists_in_playlists.values():
            try:
                playlist_unique_artist_collection.insert_one(value)
            except DuplicateKeyError as e:
                logger.debug(value)
                logger.debug(e)

        # playlist_unique_track_collection.insert_many(unique_tracks_in_playlists.values())

    def save_playlist_tracks(self, playlists: list, playlist_tracks: dict):
        logger.info("save_playlist_tracks_to_mongo")

        collection_name = "spotify_playlist_track"
        self.db.drop_collection(collection_name)
        playlist_track_collection: Collection = self.db.create_collection(
            collection_name
        )

        playlist_track_collection.drop_indexes()
        playlist_track_collection.create_index(
            name="playlist_track_index",
            keys=[("playlist_id", ASCENDING), ("id", ASCENDING), ("url", ASCENDING)],
            unique=True,
        )

        for playlist_id in playlist_tracks.keys():
            tracks: list = playlist_tracks[playlist_id]

            for track in tracks:
                mongo_track = track["track"]
                mongo_track["playlist_id"] = playlist_id
                mongo_track["added_at"] = track["added_at"]
                mongo_track["is_local"] = track["is_local"]
                mongo_track["artist"] = self.get_artist_from_artists(
                    track["track"]["artists"]
                )
                try:
                    playlist_track_collection.insert_one(mongo_track)
                except Exception as e:
                    logger.debug(e)
                    logger.debug(mongo_track)

        # playlist_track_collection.insert_many(mongo_tracks)

    def save_playlist_details(self, playlists: list, playlist_tracks: dict):
        logger.info("save_playlist_details_to_mongo")

        collection_name = "spotify_playlist"
        self.db.drop_collection(collection_name)
        playlist_collection: Collection = self.db.create_collection(collection_name)

        playlist_collection.drop_indexes()
        playlist_collection.create_index(
            name="playlist_index", keys=[("id", ASCENDING)], unique=True
        )

        playlist_collection.insert_many(playlists)

    def save_albums(self, albums: list):
        logger.info("save_albums_to_mongo")

        collection_name = "spotify_saved_album"
        self.db.drop_collection(collection_name)
        album_collection: Collection = self.db.create_collection(collection_name)

        album_collection.drop_indexes()
        album_collection.create_index(
            name="spotify_saved_album_index", keys=[("id", ASCENDING)], unique=True
        )

        mongo_albums: list = list()
        for album in albums:
            try:
                mongo_album = album["album"]
                mongo_album["added_at"] = album["added_at"]
                mongo_album["artist"] = self.get_artist_from_artists(
                    album["album"]["artists"]
                )

                mongo_albums.append(mongo_album)
            except KeyError:
                logger.info("KeyError for album")
                break

        if mongo_albums:
            album_collection.insert_many(mongo_albums)

    def save_album_tracks(self, tracks: list):
        logger.info("save_album_tracks_to_mongo")
        db: Database = self.client.get_database("spotify_db")

        collection_name = "spotify_saved_album_track"
        db.drop_collection(collection_name)
        album_track_collection: Collection = db.create_collection(collection_name)

        album_track_collection.drop_indexes()
        album_track_collection.create_index(
            name="album_track_index",
            keys=[("id", ASCENDING), ("url", ASCENDING)],
            unique=True,
        )

        mongo_tracks: list = list()
        for track in tracks:
            mongo_track = track
            mongo_track["artist"] = self.get_artist_from_artists(track["artists"])

            mongo_tracks.append(mongo_track)

        album_track_collection.insert_many(tracks)

    def save_tracks(self, tracks: list):
        logger.info("save_tracks_to_mongo")
        db: Database = self.client.get_database("spotify_db")

        collection_name = "spotify_saved_track"
        db.drop_collection(collection_name)
        track_collection: Collection = db.create_collection(collection_name)

        track_collection.drop_indexes()
        track_collection.create_index(
            name="track_index",
            keys=[("id", ASCENDING), ("url", ASCENDING)],
            unique=True,
        )

        mongo_tracks: list = list()
        for track in tracks:
            mongo_track = track["track"]
            mongo_track["added_at"] = track["added_at"]
            mongo_track["artist"] = self.get_artist_from_artists(
                track["track"]["artists"]
            )

            mongo_tracks.append(mongo_track)

        track_collection.insert_many(mongo_tracks)

    def save_artists(self, artists: list):
        logger.info("save_artists_to_mongo")

        collection_name = "spotify_saved_artist"
        self.db.drop_collection(collection_name)
        artist_collection: Collection = self.db.create_collection(collection_name)

        artist_collection.drop_indexes()
        artist_collection.create_index(
            name="spotify_artist_index", keys=[("id", ASCENDING)], unique=True
        )

        artist_collection.insert_many(artists)


def main():
    setup_app_logging(logger, logging.DEBUG)

    spotify_to_mongodb: SpotifyToMongo = SpotifyToMongo()

    all_data = unzip_data(spotify_to_mongodb.raw_data_location)

    spotify_to_mongodb.save_all_data(all_data)


if __name__ == "__main__":
    main()
