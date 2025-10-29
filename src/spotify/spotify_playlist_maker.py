import logging
import os
import random
from configparser import ConfigParser
from typing import Optional, Any, List, Generator, Set

from spotipy import Spotify

from spotify.spotify_get_data_non_async import (
    SpotifyDataGetter,
)
from spotify.spotify_utils import (
    get_spotify_wrapper,
    setup_app_logging,
    unzip_data_from_zip,
    SAVED_ALBUM_TRACKS,
    SAVED_ARTISTS,
    SAVED_ALBUMS,
    SAVED_TRACKS,
    PLAYLISTS,
    get_config_location,
    get_memory_usage,
    PLAYLIST_TRACKS,
    UNIQUE_PLAYLIST_TRACKS, get_latest_zip, )

TOP = "Top"

LIKED = "Liked "

OLD = "old"

BATCH_SIZE_PLAYLIST_ADD = 100
MAX_PLAYLIST_TRACKS = 3000

USER_ID = "user_id"

logger = logging.getLogger(__name__)


class SpotifyPlaylistMaker:
    me: Optional[Any]
    spotify_username: str
    spotify: Spotify

    saved_albums = None
    saved_tracks = None
    saved_artists = None
    unique_playlist_tracks = None
    playlist_tracks = None
    playlists = None
    saved_album_tracks = None
    unique_playlist_albums = None

    def __init__(self, use_zip=True, spotify=None, spotify_data=None) -> None:
        super().__init__()
        setup_app_logging(logger, logging.DEBUG)
        get_memory_usage()
        logger.debug(f"Starting SpotifyPlaylistMaker with use_zip={use_zip} ")
        config_parser: ConfigParser = ConfigParser()
        config_parser.read(get_config_location())

        self.save_location = config_parser["spotify"]["save_location"]

        self.spotify_username = config_parser["spotify"]["spotify_user"]
        logger.info(f"Using user name {self.spotify_username}")
        self.save_location = os.path.join(self.save_location, self.spotify_username + "/")
        logger.info(f"Using save location {self.save_location}")

        self.raw_data_location = (
                self.save_location + config_parser["spotify"]["raw_data_location"]
        )
        self.user = config_parser["spotify"]["spotify_user"]

        if not spotify:
            self.spotify = get_spotify_wrapper(
                scope="user-library-read,user-follow-read,playlist-read-private,"
                      "user-top-read,playlist-modify-public,playlist-read-collaborative,playlist-modify-private"
            )
        else:
            self.spotify = spotify
        get_memory_usage()

        self.spotify_data_getter: SpotifyDataGetter = SpotifyDataGetter(
            spotify=self.spotify
        )
        get_memory_usage()

        if use_zip:
            self.get_data_from_zips(self.raw_data_location)
            self.setup_data_collections()
            get_memory_usage()

        if spotify_data:
            logger.debug("Getting data from parameter")
            get_memory_usage()
            self.get_data_from_parameter(spotify_data)
            self.setup_data_collections()
            get_memory_usage()

    def get_data_from_parameter(self, spotify_data):
        self.saved_albums = spotify_data.get(SAVED_ALBUMS)
        logger.debug(f"Number of saved albums: {len(self.saved_albums)}")
        self.saved_album_tracks = spotify_data.get(SAVED_ALBUM_TRACKS)
        self.saved_tracks = spotify_data.get(SAVED_TRACKS)
        self.saved_artists = spotify_data.get(SAVED_ARTISTS)
        self.playlists = spotify_data.get(PLAYLISTS)
        self.playlist_tracks = spotify_data.get(PLAYLIST_TRACKS)
        self.unique_playlist_tracks = spotify_data.get(UNIQUE_PLAYLIST_TRACKS)

    def setup_data_collections(self):
        logger.debug("Setting up data collections")
        for album in self.saved_albums:
            logger.debug(f"Album: {album['name']}, Type: {album['album_type']}")
            break
        self.album_types: Set = set(
            [album["album_type"] for album in self.saved_albums]
        )
        self.compilations = [
            album
            for album in self.saved_albums
            if album["album_type"] == "compilation"
        ]
        self.va_compilations: List = [
            album
            for album in self.saved_albums
            if album["album_type"] == "compilation"
               and album["artists"][0]["name"] == "Various Artists"
        ]
        self.sa_compilations: List = [
            album
            for album in self.saved_albums
            if album["album_type"] == "compilation"
               and album["artists"][0]["name"] != "Various Artists"
        ]
        self.albums: List = [
            album
            for album in self.saved_albums
            if album["album_type"] == "album"
        ]
        self.singles: List = [
            album
            for album in self.saved_albums
            if album["album_type"] == "single"
        ]
        self.not_compilations: List = [
            album
            for album in self.saved_albums
            if album["album_type"] != "compilation"
        ]
        logger.debug("Data collections set up")

    def get_data_from_zips(self, raw_data_location):
        logger.debug(f"Getting data from zips in {raw_data_location}")
        # get most recent zip file
        get_latest_zip(raw_data_location, file_name=SAVED_TRACKS)
        self.saved_tracks = unzip_data_from_zip(
            get_latest_zip(raw_data_location, file_name=SAVED_TRACKS)
        )
        # self.saved_album_tracks = unzip_data_from_zip(
        #     get_latest_zip(raw_data_location, file_name=SAVED_ALBUM_TRACKS)
        # )
        self.saved_artists = unzip_data_from_zip(
            get_latest_zip(raw_data_location, file_name=SAVED_ARTISTS)
        )
        self.playlists = unzip_data_from_zip(
            get_latest_zip(raw_data_location, file_name=PLAYLISTS)
        )
        self.saved_albums = unzip_data_from_zip(
            get_latest_zip(raw_data_location, file_name=SAVED_ALBUMS)
        )
        # self.playlist_tracks = unzip_data_from_zip(
        # get_latest_zip(raw_data_location, file_name=PLAYLIST_TRACKS)
        # )
        self.playlist_tracks = {}
        # self.unique_playlist_tracks = unzip_data_from_zip(
        # get_latest_zip(raw_data_location, file_name=UNIQUE_PLAYLIST_TRACKS)
        # )
        self.unique_playlist_tracks = {}
        # self.unique_playlist_artists = unzip_data_from_zip(
        # get_latest_zip(raw_data_location, file_name=UNIQUE_PLAYLIST_ARTISTS)
        # )

    def make_playlists_private(self, playlists: list):
        logger.debug("Making playlists private")
        for playlist in playlists:
            playlist_id = playlist["id"]
            playlist_name = playlist["name"]
            public = playlist["public"]
            print(f"Playlist id {playlist_id}, name {playlist_name}, public {public}")
            self.spotify.playlist_change_details(playlist_id, public=False)

    def create_playlist(self, name: str):
        logger.debug(f"Creating playlist {name}")
        playlist = self.spotify.user_playlist_create(
            name=name, user=self.user, public=False
        )
        if playlist is not None:
            playlist = self.mark_as_generated(playlist)
        return playlist

    def mark_as_generated(self, playlist):
        playlist_description = playlist["description"]
        if "*generated" not in playlist_description:
            self.spotify.playlist_change_details(
                playlist["id"], description=f"{playlist_description} *generated"
            )
        return playlist

    def create_playlists_from_liked_albums(self):
        logger.debug("Creating playlists from liked albums")

        self.create_playlist_with_tracks(
            track_ids=self.get_one_track_from_albums(self.saved_albums),
            playlist_name="Recordings (1 track)",
        )
        self.create_playlist_with_tracks(
            track_ids=self.get_one_track_from_albums(self.sa_compilations),
            playlist_name="Single Artist Compilations (1 track)",
        )
        self.create_playlist_with_tracks(
            track_ids=self.get_one_track_from_albums(self.va_compilations),
            playlist_name="Various Artist Compilations (1 track)",
        )
        self.create_playlist_with_tracks(
            track_ids=self.get_one_track_from_albums(self.singles),
            playlist_name="Singles and EPs (1 track)",
        )
        self.create_playlist_with_tracks(
            track_ids=self.get_one_track_from_albums(self.albums),
            playlist_name="Albums (1 track)",
        )
        self.create_playlist_with_tracks(
            track_ids=self.get_one_track_from_albums(self.not_compilations),
            playlist_name="Albums, EPs and Singles (1 track)",
        )

        self.create_year_playlist_from_albums(
            albums=self.not_compilations, search_year="2024"
        )
        self.create_year_playlist_from_albums(
            albums=self.not_compilations, search_year="2023"
        )
        self.create_year_playlist_from_albums(
            albums=self.not_compilations, search_year="2022"
        )
        self.create_year_playlist_from_albums(
            albums=self.not_compilations, search_year="2021"
        )
        self.create_year_playlist_from_albums(
            albums=self.not_compilations, search_year="2020"
        )
        self.create_year_playlist_from_albums(
            albums=self.not_compilations, search_year="202"
        )
        self.create_year_playlist_from_albums(
            albums=self.not_compilations, search_year="201"
        )
        self.create_year_playlist_from_albums(
            albums=self.not_compilations, search_year="200"
        )
        self.create_year_playlist_from_albums(
            albums=self.not_compilations, search_year="199"
        )
        self.create_year_playlist_from_albums(
            albums=self.not_compilations, search_year="198"
        )
        self.create_year_playlist_from_albums(
            albums=self.not_compilations, search_year="197"
        )
        self.create_year_playlist_from_albums(
            albums=self.not_compilations, search_year="196"
        )
        self.create_year_playlist_from_albums(
            albums=self.not_compilations, search_year="195"
        )
        self.create_year_playlist_from_albums(
            albums=self.not_compilations, search_year="old"
        )

    def create_year_playlist_from_albums(self, albums, search_year="2022"):
        logger.debug(f"Creating playlist for {search_year} albums")
        if search_year == OLD:
            playlist_name = "1940s and before Albums (1 track)"
        elif len(search_year) == 3:
            playlist_name = f"{search_year}0s Albums (1 track)"
        else:
            playlist_name = f"{search_year} Albums (1 track)"
        albums_by_year = self.get_albums_by_year(albums, search_year)
        self.create_playlist_with_tracks(
            track_ids=self.get_one_track_from_albums(albums_by_year),
            playlist_name=f"{playlist_name}",
        )

    def create_year_album_playlist(self, albums, year="2022", name="2022"):
        logger.debug(f"Creating playlist for {year} albums")
        filtered_albums = self.get_albums_by_year(albums, year)
        self.create_playlist_with_tracks(
            track_ids=(self.get_one_track_from_albums(filtered_albums)),
            playlist_name=f"Saved {name} Albums (1 track)",
        )

    @staticmethod
    def get_albums_by_year(albums, year):
        if year.lower() == OLD:
            filtered_albums: List = list(
                filter(
                    lambda album: int(str(album["release_date"])[0:3]) <= 193,
                    albums,
                )
            )
            return filtered_albums

        else:
            filtered_albums: List = list(
                filter(
                    lambda album: str(album["release_date"]).startswith(year),
                    albums,
                )
            )
        return filtered_albums

    def create_album_playlist(self, track_ids, playlist_name):
        self.create_playlist_with_tracks(
            track_ids=track_ids, playlist_name=playlist_name
        )

    @staticmethod
    def get_one_track_from_albums(saved_albums):
        logger.debug("Getting one track from albums")
        track_ids = []
        for album in saved_albums:
            tracks = album["tracks"]["items"]
            random_track = random.choice(tracks)
            track_ids.append(random_track["id"])
        return track_ids

    @staticmethod
    def get_all_tracks_from_albums(saved_albums):
        logger.debug("Getting all tracks from albums")
        track_ids = []
        for album in saved_albums:
            tracks = album["tracks"]["items"]
            for track in tracks:
                track_ids.append(track["id"])
        return track_ids

    @staticmethod
    def get_random_track_selections(track_ids, num_tracks):
        track_ids = random.sample(track_ids, num_tracks)
        return track_ids

    def create_playlist_from_liked_tracks_and_albums(
        self,
        from_tracks=100,
        from_albums=100,
        playlist_name="Random Playlist from Saved Tracks and Albums",
    ):
        logger.debug("Creating playlist from saved tracks and albums")
        # saved_albums = self.spotify_data_getter.get_library_saved_albums()
        # saved_album_tracks = self.spotify_data_getter.get_library_saved_album_tracks(saved_albums)
        # album_track_ids = [track["id"] for track in saved_album_tracks]
        #
        # saved_tracks = self.spotify_data_getter.get_library_saved_tracks()
        # track_ids: List = [track["id"] for track in saved_tracks]

        album_track_ids = self.get_one_track_from_albums(self.saved_albums)
        track_ids: List = [track["id"] for track in self.saved_tracks]

        random_album_track_ids: List = self.get_random_track_selections(
            album_track_ids, from_tracks
        )
        random_track_ids: List = self.get_random_track_selections(
            track_ids, from_albums
        )
        playlist_track_ids: List = random_album_track_ids + list(
            set(random_track_ids) - set(random_album_track_ids)
        )
        playlist = self.get_or_create_playlist(playlist_name)
        self.remove_tracks_from_playlist(playlist)
        self.add_tracks_to_playlist(playlist=playlist, track_ids=playlist_track_ids)

    """
    Create a playlist from all liked albums, with one track from each album
    """

    def create_playlist_from_liked_albums(
        self,
    ):
        logger.debug("Creating playlist from liked albums")
        library_saved_albums = self.spotify_data_getter.get_library_saved_albums()
        album_track_ids = self.get_one_track_from_albums(library_saved_albums)
        playlist = self.get_or_create_playlist("Liked Albums - one track from each")
        self.remove_tracks_from_playlist(playlist)
        self.add_tracks_to_playlist(playlist, album_track_ids)

    def create_random_playlist(
        self,
        number_of_songs: int = 50,
        from_albums: float = 0.5,
        from_tracks: float = 0.5,
        from_playlists: float = 0.3,
        playlist_name="Random Playlist",
    ):
        logger.debug("Creating random playlist")
        album_track_ids = self.get_one_track_from_albums(self.saved_albums)
        # album_track_ids = self.get_all_tracks_from_albums(self.saved_albums)
        random_album_track_ids: List = self.get_random_track_selections(
            album_track_ids, int(number_of_songs * from_albums)
        )

        playlist_track_ids: List = [
            track["id"] for track in self.unique_playlist_tracks.values()
        ]
        playlist_track_ids = list(
            filter(lambda track: track is not None, playlist_track_ids)
        )
        random_playlist_track_ids: List = self.get_random_track_selections(
            playlist_track_ids, int(number_of_songs * from_playlists)
        )

        track_ids: List = [track["id"] for track in self.saved_tracks]
        random_track_ids: List = self.get_random_track_selections(
            track_ids, int(number_of_songs * from_tracks)
        )

        playlist_track_ids: List = list(
            set(random_track_ids + random_album_track_ids + random_playlist_track_ids)
        )

        self.create_playlist_with_tracks(
            playlist_track_ids,
            playlist_name,
        )

    def create_random_playlist_for_year(
        self,
        number_of_songs: int = 50,
        from_albums: float = 0.5,
        from_tracks: float = 0.5,
        year="2022",
    ):
        logger.debug("Creating random playlist for year")
        album_track_ids = self.get_one_track_from_albums(
            self.get_albums_by_year(self.saved_albums, year)
        )
        random_album_track_ids: List = self.get_random_track_selections(
            album_track_ids, int(number_of_songs * from_albums)
        )

        track_ids: List = [
            track["id"]
            for track in self.filter_tracks_by_year(self.saved_tracks, year)
        ]
        random_track_ids: List = self.get_random_track_selections(
            track_ids, int(number_of_songs * from_tracks)
        )

        playlist_track_ids: List = random_album_track_ids + list(
            set(random_track_ids) - set(random_album_track_ids)
        )
        self.create_playlist_with_tracks(
            playlist_track_ids, f"Random Playlist from {year}"
        )

    def create_multiple_playlists_from_tracks(
            self, tracks, playlist_prefix=LIKED, sort_by="artist"
    ):
        logger.debug(
            f"Creating multiple playlists from {len(tracks)} tracks sorting by {sort_by}"
        )
        self.split_into_multiple_playlists(
            sort_by=sort_by, tracks=tracks, playlist_prefix=playlist_prefix
        )

    def create_playlists_by_year(
        self, tracks, start_year, end_year, playlist_prefix=LIKED
    ):
        logger.debug(f"Creating playlists by year from {start_year} to {end_year}")
        for year in range(start_year, end_year + 1):
            self.create_playlist_for_year(
                str(year), f"{playlist_prefix} {year}", tracks
            )

    def create_playlists_by_decade(
        self, tracks, start_year, end_year, playlist_prefix="Liked"
    ):
        logger.debug(f"Creating playlists by decade from {start_year} to {end_year}")
        for year in range(start_year, end_year + 1):
            self.create_playlist_for_year(
                str(year), f"{playlist_prefix} {year}0s", tracks
            )

    def create_playlist_for_year(self, year, playlist_name, tracks: list = None):
        logger.debug(f"Creating playlist {playlist_name} for year {year}")
        filtered_tracks = self.filter_tracks_by_year(tracks, year)
        track_ids: List = [track["id"] for track in filtered_tracks]
        self.create_playlist_with_tracks(
            track_ids=track_ids, playlist_name=playlist_name
        )


    def create_playlist_for_search_term(
            self, search_term, playlist_name, tracks: list = None
    ):
        logger.debug(f"Creating playlist {playlist_name} for search term {search_term}")
        filtered_tracks = self.filter_tracks_by_search_term_any(tracks, [search_term])
        track_ids: List = [track["id"] for track in filtered_tracks]
        self.create_playlist_with_tracks(
            track_ids=track_ids, playlist_name=playlist_name
        )

    def create_playlist_for_search_terms(
            self, search_terms: list, playlist_name: str, tracks: list = None
    ):
        logger.debug(f"Creating playlist {playlist_name} for search terms {search_terms}")
        filtered_tracks = self.filter_tracks_by_search_term_any(tracks, search_terms)
        track_ids: List = [track["id"] for track in filtered_tracks]
        self.create_playlist_with_tracks(
            track_ids=track_ids, playlist_name=playlist_name
        )

    def create_playlist_for_artist(
            self, artist: str, playlist_name: str, tracks: list = None
    ):
        logger.debug(f"Creating playlist {playlist_name} for artist {artist}")
        filtered_tracks = self.filter_tracks_by_artist(tracks, [artist])
        track_ids: List = [track["id"] for track in filtered_tracks]
        self.create_playlist_with_tracks(
            track_ids=track_ids, playlist_name=playlist_name
        )

    def create_playlist_for_artists(
            self, artists: list, playlist_name: str, tracks: list = None
    ):
        logger.debug(f"Creating playlist {playlist_name} for artists {artists}")
        filtered_tracks = self.filter_tracks_by_artist(tracks, artists)
        track_ids: List = [track["id"] for track in filtered_tracks]
        self.create_playlist_with_tracks(
            track_ids=track_ids, playlist_name=playlist_name
        )



    @staticmethod
    def filter_tracks_by_year(tracks, year):
        logger.debug(f"Filtering {len(tracks)} tracks by year {year}")
        filtered_tracks: List = list(
            filter(
                lambda track: str(track["album"]["release_date"]).startswith(
                    year
                ),
                tracks,
            )
        )
        return filtered_tracks

    '''
    Filter tracks by search term, where the search term matches any word in the track name.'''
    @staticmethod
    def filter_tracks_by_search_term_any(tracks, search_terms: list):
        logger.debug(f"Filtering {len(tracks)} tracks by search term {search_terms}")
        filtered_tracks: List = list(
            filter(
                lambda track: any(
                    search_term.lower() == word.lower()
                    for search_term in search_terms
                    for word in track["name"].lower().split()
                ),
                tracks,
            )
        )

        return filtered_tracks

    @staticmethod
    def filter_tracks_by_search_term_all(tracks, search_terms: list):
        logger.debug(f"Filtering {len(tracks)} tracks by search term {search_terms}")
        filtered_tracks: List = list(
            filter(
                lambda track: all(
                    search_term.lower() in track["name"].lower()
                    for search_term in search_terms
                ),
                tracks,
            )
        )

        return filtered_tracks

    @staticmethod
    def filter_tracks_by_artist(tracks, artists: list):
        logger.debug(f"Filtering {len(tracks)} tracks by artists {artists}")
        filtered_tracks: List = list(
            filter(
                # make this filter contains instead of equals e.g. "Beatles" should match "The Beatles"
                # should match if any artist in the list is in the track's artists or name
                # look in all of the artists in the track, not just the first one

                # lambda track: any(
                #     artist.lower() in track["artists"][0]["name"].lower()
                #     or artist.lower() in track["name"].lower()
                #     for artist in artists
                lambda track: any(
                    artist.lower() in track["name"].lower() or
                    artist.lower() in artist_obj["name"].lower()
                    for artist_obj in track["artists"]
                    for artist in artists
                ),
                tracks,
            )
        )
        return filtered_tracks

    def create_playlist_with_tracks(self, track_ids, playlist_name):
        logger.debug(f"Creating playlist {playlist_name} with {len(track_ids)} tracks")
        playlist = self.get_or_create_playlist(playlist_name)
        self.remove_tracks_from_playlist(playlist)
        self.add_tracks_to_playlist(playlist, track_ids)

    def add_tracks_to_playlist(self, playlist: dict, track_ids: list):
        logger.debug(f"Adding {len(track_ids)} tracks to playlist {playlist['name']}")
        playlist_id = playlist["id"]
        playlist_name = playlist["name"]
        existing_tracks = self.spotify_data_getter.get_tracks_for_playlist(
            playlist_id, playlist_name
        )
        existing_track_ids: list = [
            item["track"]["id"]
            for item in existing_tracks
            if item["track"]["is_local"] is False
        ]

        track_ids_to_add = list(set(track_ids) - set(existing_track_ids))
        batch_list: Generator[List] = self.batch_list(
            track_ids_to_add, BATCH_SIZE_PLAYLIST_ADD
        )
        for batch in batch_list:
            if batch is not None and len(batch) > 0:
                try:
                    self.spotify.playlist_add_items(playlist_id, batch)
                except Exception as e:
                    print(
                        f"Error adding batch {batch} to playlist {playlist_name} exception {e}"
                    )
                    self.handle_individual_error(batch, playlist_id, playlist_name)
                    continue

    def handle_individual_error(self, batch, playlist_id, playlist_name):
        for batch_id in batch:
            try:
                self.spotify.playlist_add_items(playlist_id, [batch_id])
            except Exception as e:
                print(e)
                print(f"Error adding {batch_id} to playlist {playlist_name}")

    def split_into_multiple_playlists(
        self,
        tracks,
        playlist_prefix=LIKED,
        sort_by="artist",
        tracks_per_playlist=MAX_PLAYLIST_TRACKS,
    ):
        logger.debug("Splitting into multiple playlists")
        sorted_tracks = []
        if sort_by == "artist":
            sorted_tracks: List = sorted(
                tracks, key=lambda x: x["track"]["artists"][0]["name"]
            )
        if sort_by == "length":
            sorted_tracks: List = sorted(
                tracks, key=lambda x: x["track"]["duration_ms"]
            )

        track_ids: List = [track["id"] for track in sorted_tracks]

        batch_list: Generator[List] = self.batch_list(
            track_ids, BATCH_SIZE_PLAYLIST_ADD
        )
        playlist_num = 1
        playlist = self.create_playlist(
            f"{playlist_prefix} (by {sort_by}) Part {playlist_num}"
        )
        playlist_id = playlist["id"]
        num_tracks_added = 0
        for batch in batch_list:
            self.spotify.playlist_add_items(playlist_id, batch)
            num_tracks_added += len(batch)
            if num_tracks_added >= tracks_per_playlist:
                num_tracks_added = 0
                playlist_num += 1
                playlist = self.create_playlist(
                    f"{playlist_prefix} (by {sort_by}) Part {playlist_num}"
                )
                playlist_id = playlist["id"]

    @staticmethod
    def batch_list(list_to_batch: List, batch_size: int):
        for i in range(0, len(list_to_batch), batch_size):
            yield list_to_batch[i: i + batch_size]

    def combine_all_top_playlists(self):
        logger.debug("Combining all top playlists")
        top_playlists = filter(lambda pl: str(pl["name"]).endswith(TOP), self.playlists)
        top_playlist_ids = []
        for top_playlist in top_playlists:
            top_playlist_ids.append(top_playlist["id"])
        logger.debug(f"number of top playlists: {len(top_playlist_ids)}")
        playlist_tracks: dict = self.playlist_tracks
        all_top_playlist_track_ids = set()
        for top_playlist_id in top_playlist_ids:
            for track in playlist_tracks[top_playlist_id]:
                all_top_playlist_track_ids.add(track["id"])
        logger.debug(
            f"Number of top playlist tracks: {len(all_top_playlist_track_ids)}"
        )

        playlist = self.get_or_create_playlist("All Top Songs")
        self.remove_tracks_from_playlist(playlist)
        self.add_tracks_to_playlist(
            playlist=playlist, track_ids=list(all_top_playlist_track_ids)
        )

    def remove_tracks_from_playlist(self, playlist):
        playlist_name = playlist["name"]
        logger.debug(f"Removing tracks from playlist {playlist_name}")
        playlist_id = playlist["id"]

        playlist_items = self.spotify_data_getter.get_tracks_for_playlist(
            playlist_id, playlist_name
        )
        playlist_item_ids: list = [
            item["track"]["id"]
            for item in playlist_items
            if "is_local" in item["track"]
            if item["track"]["is_local"] is False
        ]
        logger.debug(f"Removing {len(playlist_item_ids)} tracks from playlist")
        chunks = self.batch_list(playlist_item_ids, 100)
        for chunk in chunks:
            logger.debug(f"Removing {len(chunk)} tracks from playlist")
            self.spotify.playlist_remove_all_occurrences_of_items(
                playlist_id=playlist_id, items=chunk
            )

    def make_decade_playlists(self):
        logger.debug("Making decade playlists")
        top_playlists = list(
            filter(lambda x: str(x["name"]).endswith(TOP), self.playlists)
        )
        decades: list = [
            "2020s",
            "2010s",
            "2000s",
            "1990s",
            "1980s",
            "1970s",
            "1960s",
            "1950s",
            "1940s",
            "1930s",
            "1920s",
            "1910s",
            "1900s",
        ]

        playlist_ids: dict = {}
        for decade in decades:
            playlist_ids[decade] = []
        for top_playlist in top_playlists:
            for decade in decades:
                if str(top_playlist["name"]).startswith(decade[0:3]):
                    playlist_ids[decade].append(top_playlist["id"])

        playlist_track_ids: dict = {}
        for decade in decades:
            print(f"Number of {decade} playlists: {len(playlist_ids[decade])}")
            playlist_track_ids[decade] = set()
            for playlist_id in playlist_ids[decade]:
                for track in self.playlist_tracks[playlist_id]:
                    playlist_track_ids[decade].add(track["id"])

            if len(playlist_track_ids[decade]) > 0:
                print(f"Number of {decade} tracks: {len(playlist_track_ids[decade])}")
                playlist = self.get_or_create_playlist(f"{decade} Top Songs")
                self.remove_tracks_from_playlist(playlist)
                self.add_tracks_to_playlist(playlist, list(playlist_track_ids[decade]))

    def get_or_create_playlist(self, playlist_name: str) -> dict:
        logger.debug(f"Getting or creating playlist {playlist_name}")
        match_playlist: dict = self.find_playlist_by_name(playlist_name)
        if match_playlist is None:
            return self.create_playlist(playlist_name)
        else:
            match_playlist = self.mark_as_generated(match_playlist)
            return match_playlist

    def create_playlists_by_search_term(self, queries, playlist_name):
        logger.debug(f"Creating playlists by search term {queries}")
        tracks = []
        for search_term in queries:
            search_results = self.spotify_data_getter.get_tracks_for_search(
                query=search_term, num_tracks=200
            )

            tracks.extend(search_results)

        track_ids = [track["id"] for track in tracks]

        playlist = self.get_or_create_playlist(f"{playlist_name}")
        self.remove_tracks_from_playlist(playlist)
        self.add_tracks_to_playlist(playlist, track_ids)

    def find_playlist_by_name(self, playlist_name: str):
        logger.debug(f"Finding playlist by name {playlist_name}")
        logger.debug(f"Number of playlists: {len(self.playlists)}")
        if len(self.playlists) == 0:
            logger.debug("Fetching playlists from Spotify")
            self.playlists, _ = self.spotify_data_getter.get_playlists()
        else:
            logger.debug("Using cached playlists")
        for playlist in self.playlists:
            if playlist["name"] == playlist_name:
                logger.debug(f"Found playlist {playlist_name}")
                return playlist

        logger.debug(f"Playlist {playlist_name} not found")
        return None
