import codecs
import csv
import datetime
import logging
import os
import re
from configparser import ConfigParser

import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

from spotify.spotify_save import SpotifySave
from spotify.spotify_utils import (
    setup_app_logging,
    most_recent_directory,
    unzip_data_from_zip, get_config_location,
)

XLSX = ".xlsx"

CSV = ".csv"

SPOTIFY_LIBRARY_ALL_TRACKS = (
    "spotify_library_all_tracks_" + str(datetime.date.today()) + XLSX
)

SPOTIFY_LIBRARY_ALBUM_TRACKS = (
    "spotify_library_albums_tracks_" + str(datetime.date.today())
) + CSV

SPOTIFY_LIBRARY_TRACKS = "spotify_library_tracks_" + str(datetime.date.today()) + CSV

logger = logging.getLogger(__name__)


class SpotifyToFile(SpotifySave):
    user_id = ""
    save_location = ""
    playlist_location = ""
    individual_playlist_location = ""

    def __init__(self, user_id: str = "") -> None:
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

    def save_unique_tracks_in_playlists(self, unique_tracks_in_playlists: dict):
        csv_file_name = (
            "spotify_all_tracks_in_a_playlist_" + str(datetime.date.today()) + CSV
        )
        excel_file_name = csv_file_name.replace(CSV, XLSX)
        tracks = list(unique_tracks_in_playlists.values())
        for track in tracks:
            track["artists_joined"] = ", ".join(
                [artist["name"] for artist in track["artists"]]
            )
            track["release_year"] = calc_release_year(
                track["album"]["release_date"],
                track["album"]["release_date_precision"],
            )
        tracks = sorted(tracks, key=lambda k: (k["artists_joined"], k["name"]))

        with open(csv_file_name, "w", encoding="utf-8", newline="\n") as f:
            csv_writer = self.get_csv_writer(f)
            header_columns = [
                "Artist",
                "Track",
                "Album",
                "URI",
                "ID",
                "Playlist",
                "ISRC",
                "Release_Year",
                "Release_Date",
                "Release_Date_Precision",
            ]
            header_columns[0] = self.add_bom(header_columns[0])

            csv_writer.writerow(header_columns)
            for track in tracks:
                artist = ", ".join([artist["name"] for artist in track["artists"]])
                csv_writer.writerow(
                    [
                        artist,
                        track["name"],
                        track["album"]["name"],
                        track["uri"],
                        track["id"],
                        "",
                        self.get_external_id(track["external_ids"], "isrc"),
                        track["release_year"],
                        track["album"]["release_date"],
                        track["album"]["release_date_precision"],
                    ]
                )
            logger.debug(f"Wrote file: {csv_file_name}")
            self.make_excel_file(csv_file_name, excel_file_name)
            logger.debug(f"Wrote file: {excel_file_name}")

    @staticmethod
    def get_csv_writer(f):
        return csv.writer(
            f,
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
            lineterminator="\n",
        )

    @staticmethod
    def add_bom(string):
        return (codecs.BOM_UTF8 + string.encode("utf-8")).decode("utf-8")

    def save_unique_artists_in_playlists(self, unique_artists_in_playlists: dict):

        csv_all_artist_filename = (
            "spotify_all_artists_in_a_playlist_" + str(datetime.date.today()) + CSV
        )
        excel_all_artist_filename = csv_all_artist_filename.replace(CSV, XLSX)

        with open(csv_all_artist_filename, "w", encoding="utf-8", newline="\n") as f:
            csv_writer = self.get_csv_writer(f)
            header_columns = ["Name", "ID", "URI", "Href"]
            header_columns[0] = self.add_bom(header_columns[0])
            csv_writer.writerow(header_columns)

            artists = unique_artists_in_playlists.values()
            for artist in artists:
                csv_writer.writerow(
                    [artist["name"], artist["id"], artist["uri"], artist["href"]]
                )
            logger.debug("Wrote file: " + csv_all_artist_filename)

        self.make_excel_file(csv_all_artist_filename, excel_all_artist_filename)

    def save_playlist_tracks(self, playlists: list, playlist_tracks: dict):
        track_filename = "spotify_playlist_tracks_" + str(datetime.date.today()) + CSV
        excel_track_filename = track_filename.replace(CSV, XLSX)

        with open(track_filename, "w", encoding="utf-8", newline="\n") as f:
            csv_writer = self.get_csv_writer(f)
            header_columns = [
                "Artist",
                "Track",
                "Album",
                "Release_Year",
                "URI",
                "ID",
                "Playlist",
                "ISRC",
                "Release_Date",
                "Release_Date_Precision",
            ]
            header_columns[0] = self.add_bom(header_columns[0])
            csv_writer.writerow(header_columns)

            for playlist in playlists:
                playlist_name = playlist["name"]
                logger.debug(playlist["name"])
                tracks = playlist_tracks[playlist["id"]]
                for track in tracks:
                    track_1 = track
                    if track_1 is None:
                        continue
                    artist = ", ".join(
                        [artist["name"] for artist in track_1["artists"]]
                    )
                    csv_writer.writerow(
                        [
                            artist,
                            track_1["name"],
                            track_1["album"]["name"],
                            calc_release_year(
                                track_1["album"]["release_date"],
                                track_1["album"]["release_date_precision"],
                            ),
                            track_1["uri"],
                            track_1["id"],
                            playlist_name,
                            self.get_external_id(track_1["external_ids"], "isrc"),
                            track_1["album"]["release_date"],
                            track_1["album"]["release_date_precision"],
                        ]
                    )
            logger.debug("Wrote file: " + track_filename)
            self.make_excel_file(track_filename, excel_track_filename)

    def save_playlist_details(self, playlists: list, playlist_tracks: dict):
        logger.debug("save_playlist_details_to_file")
        playlist_filename = "spotify_playlists_" + str(datetime.date.today()) + CSV
        excel_playlist_filename = playlist_filename.replace(CSV, XLSX)

        with open(playlist_filename, "w", encoding="utf-8", newline="\n") as f:
            csv_writer = self.get_csv_writer(f)
            header_columns = [
                "Playlist",
                # "Number_of_Tracks",
                "Owner",
                "External_URL",
                "ID",
            ]
            header_columns[0] = self.add_bom(header_columns[0])
            csv_writer.writerow(header_columns)
            for playlist in playlists:
                playlist_name = playlist["name"]
                logger.debug(playlist["name"])
                # tracks: list = playlist_tracks.get(playlist["id"])
                csv_writer.writerow(
                    [
                        playlist_name,
                        # len(tracks),
                        playlist["owner"]["display_name"],
                        playlist["external_urls"]["spotify"],
                        playlist["id"],
                    ]
                )

        logger.debug("Wrote file: " + playlist_filename)
        self.make_excel_file(playlist_filename, excel_playlist_filename)

    def save_albums(self, albums: list):
        for album in albums:
            album["artists_joined"] = ", ".join(
                [artist["name"] for artist in album["artists"]]
            )
            album["release_year"] = calc_release_year(
                album["release_date"],
                album["release_date_precision"],
            )
        albums = sorted(
            albums,
            key=lambda k: (k["artists_joined"], k["release_year"]),
            reverse=False,
        )
        csv_album_file_name = (
            "spotify_library_albums_" + str(datetime.date.today()) + CSV
        )
        excel_album_file_name = csv_album_file_name.replace(CSV, XLSX)
        csv_album_track_file_name = SPOTIFY_LIBRARY_ALBUM_TRACKS
        excel_album_track_file_name = csv_album_track_file_name.replace(CSV, XLSX)

        with open(csv_album_file_name, "w", encoding="utf-8", newline="\n") as f:
            csv_writer_album = self.get_csv_writer(f)
            with open(
                csv_album_track_file_name, "w", encoding="utf-8", newline="\n"
            ) as g:
                csv_writer_album_track = self.get_csv_writer(g)
                album_header_rows = [
                    "Album",
                    "Artist",
                    "Release_Year",
                    "Label",
                    "Spotify_URI",
                    "Release_Date",
                    "Total_Tracks",
                    "Cover",
                    "Group",
                    "Type",
                    "ID",
                    "Genres",
                    "UPC",
                    "mbid",
                    "Artist_Album_(Year)",
                    "Artist_Album_(Year)_{Label}",
                ]
                album_header_rows[0] = self.add_bom(album_header_rows[0])
                csv_writer_album.writerow(album_header_rows)
                album_track_header_rows = [
                    "Album",
                    "Artist",
                    "Track",
                    "Release_Year",
                    "Track_Length_min",
                    "Release_Date",
                    "Release_Date_Precision",
                    "ID",
                    "Spotify_URI",
                ]

                album_track_header_rows[0] = self.add_bom(album_track_header_rows[0])
                csv_writer_album_track.writerow(album_track_header_rows)

                for album in albums:
                    album_tracks = album["tracks"]["items"]
                    external_ids = album["external_ids"]
                    upc = self.get_external_id(external_ids, "upc")
                    album_name = album["name"]
                    artists = ", ".join(
                        [artist["name"] for artist in album["artists"]]
                    )
                    # mbid = get_album_mbid(album_name, artists, upc)
                    mbid = ""
                    release_year = calc_release_year(
                        album["release_date"],
                        album["release_date_precision"],
                    )
                    extra = f"{artists} - {album_name} ({release_year})"
                    extra2 = f"{artists} - {album_name} ({release_year}) {{{album['label']}}}"
                    # handle if album_group does not exist
                    if "album_group" in album:
                        album_group = album["album_group"]
                    else:
                        album_group = ""
                    album_type = album["album_type"]
                    images = album["images"]
                    if len(images) > 0:
                        image_url = images[0]["url"]
                    else:
                        image_url = ""
                    csv_writer_album.writerow(
                        [
                            album_name,
                            album["artists_joined"],
                            album["release_year"],
                            album["label"],
                            album["uri"],
                            album["release_date"],
                            album["total_tracks"],
                            image_url,
                            album_group,
                            album_type,
                            album["id"],
                            "",
                            upc,
                            mbid,
                            extra,
                            extra2,
                        ]
                    )
                    for track in album_tracks:
                        duration_min = self.get_duration_in_min(track["duration_ms"])
                        artist = ", ".join(
                            [artist["name"] for artist in track["artists"]]
                        )
                        release_year = (
                            release_year if album_type != "compilation" else ""
                        )
                        csv_writer_album_track.writerow(
                            [
                                album_name,
                                artist,
                                track["name"],
                                release_year,
                                duration_min,
                                "",
                                "",
                                "",
                                track["id"],
                                track["uri"],
                            ]
                        )
        logger.debug("Wrote file: " + csv_album_file_name)
        logger.debug("Wrote file: " + csv_album_track_file_name)
        self.make_excel_file(csv_album_file_name, excel_album_file_name)
        self.make_excel_file(csv_album_track_file_name, excel_album_track_file_name)
        logger.debug("Wrote file: " + excel_album_file_name)
        logger.debug("Wrote file: " + excel_album_track_file_name)

    @staticmethod
    def get_external_id(external_ids, key):
        if key in external_ids.keys():
            value = external_ids[key]
        else:
            value = ""
        return value

    def save_tracks(self, tracks: list):
        csv_file_name = SPOTIFY_LIBRARY_TRACKS
        excel_file_name = csv_file_name.replace(CSV, XLSX)

        for track in tracks:
            track["artists_joined"] = ", ".join(
                [track["name"] for track in track["artists"]]
            )
            track["release_year"] = calc_release_year(
                track["album"]["release_date"],
                track["album"]["release_date_precision"],
            )
            track["duration_min"] = self.get_duration_in_min(
                track["duration_ms"]
            )

        tracks = sorted(
            tracks,
            key=lambda k: (k["artists_joined"], k["name"]),
            reverse=False,
        )

        with open(csv_file_name, "w", encoding="utf-8", newline="\n") as f:
            csv_writer = self.get_csv_writer(f)
            header_columns = [
                "Artist",
                "Track",
                "Album",
                "Release_Year",
                "Track_Length_min",
                "Release_Date",
                "Release_Date_Precision",
                "ID",
                "Spotify_URI",
                "ISRC",
                "Artist_Track",
            ]
            header_columns[0] = self.add_bom(header_columns[0])
            csv_writer.writerow(header_columns)

            for track in tracks:
                # track = t["track"]
                csv_writer.writerow(
                    [
                        (track["artists_joined"]),
                        track["name"],
                        track["album"]["name"],
                        track["release_year"],
                        track["duration_min"],
                        track["album"]["release_date"],
                        track["album"]["release_date_precision"],
                        track["id"],
                        track["uri"],
                        self.get_external_id(track["external_ids"], "isrc"),
                        f"{track['artists_joined']} - {track['name']}",
                    ]
                )

        logger.debug("Wrote file: " + csv_file_name)

        self.make_excel_file(csv_file_name, excel_file_name)
        logger.debug("Wrote file: " + excel_file_name)

    @staticmethod
    def make_excel_file(csv_file_name, excel_file_name):
        wb = openpyxl.Workbook()
        ws = wb.active
        with open(csv_file_name) as f:
            csv_reader = csv.reader(
                f,
                delimiter=",",
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL,
                lineterminator="\n",
            )
            for row in csv_reader:
                ws.append(row)
        wb.save(excel_file_name)

    @staticmethod
    def get_duration_in_min(duration_ms):
        duration_sec: int = round((duration_ms / 1000), 0)
        duration_min = str(datetime.timedelta(seconds=duration_sec))[3:]
        if duration_min[0] == "0":
            duration_min = duration_min[1:]
        return duration_min

    def save_artists(self, artists: list):
        file_name = "spotify_library_artists_" + str(datetime.date.today())
        csv_file_name = file_name + CSV
        excel_file_name = file_name + XLSX
        artists = sorted(
            artists,
            key=lambda k: (k["name"]),
            reverse=False,
        )

        with open(csv_file_name, "w", encoding="utf-8", newline="\n") as f:
            csv_writer = self.get_csv_writer(f)
            header_columns = [
                "Artist",
                "Spotify_URI",
                "ID",
                "Followers",
                "Popularity",
                "Genres",
                "Artist_Image_URL",
            ]
            header_columns[0] = self.add_bom(header_columns[0])
            csv_writer.writerow(header_columns)
            for artist in artists:
                artist_image_url = (
                    artist["images"][0]["url"] if len(artist["images"]) > 0 else ""
                )
                genres = ", ".join(genre for genre in artist["genres"])
                csv_writer.writerow(
                    [
                        artist["name"],
                        artist["uri"],
                        artist["id"],
                        artist["followers"],
                        artist["popularity"],
                        genres,
                        artist_image_url,
                    ]
                )
        logger.debug("Wrote file: " + csv_file_name)
        self.make_excel_file(csv_file_name, excel_file_name)
        logger.debug("Wrote file: " + excel_file_name)

    def save_all_library_tracks(self):
        wb = openpyxl.Workbook()
        ws: Worksheet = wb.active
        excel_file_name = SPOTIFY_LIBRARY_ALL_TRACKS
        self.append_to_worksheet(ws, SPOTIFY_LIBRARY_TRACKS)
        self.append_to_worksheet(ws, SPOTIFY_LIBRARY_ALBUM_TRACKS, skip_header=True)
        ws.auto_filter()

        wb.save(excel_file_name)

    @staticmethod
    def append_to_worksheet(ws, tracks, skip_header=False):
        with open(tracks) as f:
            csv_reader = csv.reader(
                f,
                delimiter=",",
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL,
                lineterminator="\n",
            )

            for row in csv_reader:
                if skip_header:
                    skip_header = False
                    continue
                ws.append(row)

    def save_individual_playlists(self, playlists: list, playlist_tracks: dict):
        os.chdir(self.individual_playlist_location)
        for playlist in playlists:
            playlist_name = playlist["name"]
            logger.debug(f"Playlist name is {playlist_name}")
            playlist_id = playlist["id"]

            indiv_playlist_filename = (
                self.sanitize_playlist_name(playlist_name)
                + "_"
                + playlist_id
                + "_"
                + str(datetime.date.today())
                + CSV
            )
            with open(
                indiv_playlist_filename, "w", encoding="utf-8", newline="\n"
            ) as f:
                csv_writer = self.get_csv_writer(f)
                header_columns = [
                    "Artist",
                    "Track",
                    "Album",
                    "Spotify_URI",
                    "ID",
                    "Playlist",
                    "Release_Year",
                    "Release_Date",
                    "Release_Date_Precision",
                    "Track_Length_min",
                ]
                header_columns[0] = self.add_bom(header_columns[0])
                csv_writer.writerow(header_columns)
                logger.debug(playlist["name"])
                tracks: list = playlist_tracks[playlist_id]
                for track in tracks:
                    track_1 = track
                    if track_1 is None:
                        continue
                    artists = track_1["artists"]
                    artists = ", ".join(artist["name"] for artist in artists)

                    release_year = calc_release_year(
                        track_1["album"]["release_date"],
                        track_1["album"]["release_date_precision"],
                    )
                    track_1["duration_min"] = self.get_duration_in_min(
                        track_1["duration_ms"]
                    )
                    csv_writer.writerow(
                        [
                            artists,
                            track_1["name"],
                            track_1["album"]["name"],
                            track_1["uri"],
                            track_1["id"],
                            playlist_name,
                            release_year,
                            track_1["album"]["release_date"],
                            track_1["album"]["release_date_precision"],
                            track_1["duration_min"],
                        ]
                    )
            logger.debug("Wrote file: " + str(indiv_playlist_filename))

    @staticmethod
    def sanitize_playlist_name(playlist_name: str) -> str:
        # Remove characters not allowed in file names
        sanitized_name = re.sub(r'[<>:"/\\|?*]', "_", playlist_name)
        # Trim leading and trailing whitespaces
        sanitized_name = sanitized_name.strip()

        # Remove trailing dots (Windows limitation)
        sanitized_name = sanitized_name.rstrip(".")
        # Truncate the name to the maximum allowed length for the target operating system
        max_length = 255  # Maximum file name length for most operating systems
        if len(sanitized_name) > max_length:
            sanitized_name = sanitized_name[:max_length]

        return sanitized_name

    def save_album_tracks(self, tracks: list):
        # not implemented
        pass

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


def calc_release_year(release_date, release_date_precision) -> int:
    if release_date_precision == ["year", "month", "day"]:
        return release_date[0:4]
    if release_date_precision is None:
        return -1

    return release_date


def main():
    setup_app_logging(logger, logging.DEBUG)
    spotify_to_file: SpotifyToFile = SpotifyToFile()
    os.chdir(spotify_to_file.playlist_location)
    spotify_to_file.save_all_data({})


if __name__ == "__main__":
    main()
