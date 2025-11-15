import logging
import os
from configparser import ConfigParser

from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, BulkWriteError

from spotify.spotify_save import SpotifySave
from spotify.spotify_utils import setup_app_logging, unzip_data, get_config_location, most_recent_directory, \
    unzip_data_from_zip

logger = logging.getLogger(__name__)


class SpotifyToMongo(SpotifySave):
    client: MongoClient
    db: Database
    user_id = ""
    save_location = ""
    playlist_location = ""
    individual_playlist_location = ""


    def __init__(self, mongodb_server="mongodb://localhost:27017/",user_id:str = "") -> None:
        super().__init__()
        self.client = MongoClient(mongodb_server)
        self.db = self.client.get_database("spotify_db")
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
        try:
            playlist_collection.insert_many(playlists)
        except BulkWriteError as e:
            logger.debug("Bulk write error, some duplicates skipped")
            logger.debug(e.details)

    def save_albums(self, albums: list):
        logger.info("save_albums_to_mongo")

        collection_name = "spotify_saved_album"
        self.db.drop_collection(collection_name)
        album_collection: Collection = self.db.create_collection(collection_name)

        album_collection.drop_indexes()
        album_collection.create_index(
            name="spotify_saved_album_index", keys=[("id", ASCENDING)], unique=True
        )

        mongo_albums: list = []
        for album in albums:
            try:
                mongo_album = album
                mongo_album["artist"] = self.get_artist_from_artists(
                    album["artists"]
                )

                mongo_albums.append(mongo_album)
            except KeyError:
                logger.info(f"KeyError for album {album}")
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

        mongo_tracks: list = []
        for track in tracks:
            mongo_track = track
            # print(f"mongo_track is {mongo_track}")
            # mongo_track["added_at"] = track["added_at"]
            mongo_track["artist"] = self.get_artist_from_artists(
                track["artists"]
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

    def save_all_data(self, all_data: dict):
        most_recent = most_recent_directory(self.raw_data_location)
        logger.debug(f"Most recent directory: {most_recent}")
        zip_folder = f"{self.raw_data_location}/{most_recent}"
        self.save_artists(
            unzip_data_from_zip(f"{zip_folder}/saved_artists.gz")
        )
        self.save_albums(
            unzip_data_from_zip(f"{zip_folder}/saved_albums.gz")
        )
        # self.save_album_tracks(
        #     unzip_data_from_zip(f"{zip_folder}/saved_album_tracks.gz")
        # )
        self.save_tracks(
            unzip_data_from_zip(f"{zip_folder}/saved_tracks.gz")
        )
        # self.save_playlist_tracks(
        #     unzip_data_from_zip(f"{zip_folder}/playlists.gz"),
        #     unzip_data_from_zip(f"{zip_folder}/playlist_tracks.gz"),
        # )
        self.save_playlist_details(
            unzip_data_from_zip(f"{zip_folder}/playlists.gz"),
            None
            # unzip_data_from_zip(f"{zip_folder}/playlist_tracks.gz"),
        )
        # self.save_individual_playlists(
        #     unzip_data_from_zip(f"{zip_folder}/playlists.gz"),
        #     None
        #     unzip_data_from_zip(f"{zip_folder}/playlist_tracks.gz"),
        # )
        # self.save_unique_tracks_in_playlists(
        #     unzip_data_from_zip(f"{zip_folder}/unique_playlist_tracks.gz")
        # )
        # self.save_unique_artists_in_playlists(
        #     unzip_data_from_zip(f"{zip_folder}/unique_playlist_artists.gz")
        # )



def main():
    setup_app_logging(logger, logging.DEBUG)

    spotify_to_mongodb: SpotifyToMongo = SpotifyToMongo()

    # all_data = unzip_data(spotify_to_mongodb.raw_data_location)

    spotify_to_mongodb.save_all_data({})


if __name__ == "__main__":
    main()
