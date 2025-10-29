from abc import ABC, abstractmethod

from spotify.spotify_utils import (
    SAVED_ARTISTS,
    SAVED_ALBUMS,
    SAVED_TRACKS,
    PLAYLISTS,
    PLAYLIST_TRACKS,
    UNIQUE_PLAYLIST_ARTISTS,
    UNIQUE_PLAYLIST_TRACKS,
    SAVED_ALBUM_TRACKS,
)


# Interface for saving Spotify data
class SpotifySave(ABC):
    def save_all_data(self, all_data: dict):
        self.save_artists(all_data[SAVED_ARTISTS])
        self.save_albums(all_data[SAVED_ALBUMS])
        self.save_album_tracks(all_data[SAVED_ALBUM_TRACKS])
        self.save_tracks(all_data[SAVED_TRACKS])
        self.save_playlist_tracks(all_data[PLAYLISTS], all_data[PLAYLIST_TRACKS])
        self.save_playlist_details(all_data[PLAYLISTS], all_data[PLAYLIST_TRACKS])
        self.save_individual_playlists(all_data[PLAYLISTS], all_data[PLAYLIST_TRACKS])
        self.save_unique_tracks_in_playlists(all_data[UNIQUE_PLAYLIST_TRACKS])
        self.save_unique_artists_in_playlists(all_data[UNIQUE_PLAYLIST_ARTISTS])

    @abstractmethod
    def save_unique_tracks_in_playlists(self, unique_tracks_in_playlists: dict):
        pass

    @abstractmethod
    def save_unique_artists_in_playlists(self, unique_artists_in_playlists: dict):
        pass

    @abstractmethod
    def save_playlist_tracks(self, playlists: list, playlist_tracks: dict):
        pass

    @abstractmethod
    def save_playlist_details(self, playlists: list, playlist_tracks: dict):
        pass

    @abstractmethod
    def save_albums(self, albums: list):
        pass

    @abstractmethod
    def save_tracks(self, tracks: list):
        pass

    @abstractmethod
    def save_album_tracks(self, tracks: list):
        pass

    @abstractmethod
    def save_artists(self, artists: list):
        pass

    @abstractmethod
    def save_individual_playlists(self, playlists: list, playlist_tracks: dict):
        pass
