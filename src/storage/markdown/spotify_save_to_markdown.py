import logging
import os
from configparser import ConfigParser

logger = logging.getLogger(__name__)

from spotify.spotify_save import SpotifySave
from spotify.spotify_utils import setup_app_logging, get_config_location, most_recent_directory, unzip_data_from_zip


class SpotifyToMarkdown(SpotifySave):
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


    def save_all_data(self, all_data: dict):
        most_recent = most_recent_directory(self.raw_data_location)
        logger.debug(f"Most recent directory: {most_recent}")
        zip_folder = f"{self.raw_data_location}/{most_recent}"
        # self.save_artists(
        #     unzip_data_from_zip(f"{zip_folder}/saved_artists.gz")
        # )
        self.save_albums(
            unzip_data_from_zip(f"{zip_folder}/saved_albums.gz")
        )

    def save_unique_tracks_in_playlists(self, unique_tracks_in_playlists: dict):
        pass

    def save_unique_artists_in_playlists(self, unique_artists_in_playlists: dict):
        pass

    def save_playlist_tracks(self, playlists: list, playlist_tracks: dict):
        pass

    def save_playlist_details(self, playlists: list, playlist_tracks: dict):
        pass

    def save_albums(self, albums: list):
        for album in albums:
            markdown: str = self.create_markdown(album)
            logger.debug(f"Markdown for album {album['name']}: {markdown}")

    def create_markdown(self, album):
        """
        Create a Markdown representation for a Spotify album payload.

        Args:
            album (dict): Album payload as returned from the Spotify API or the
                saved_albums export. The method tolerates both the flattened
                album dictionary (used elsewhere in the project) and the raw
                saved-album item that nests the album data below the "album"
                key.

        Returns:
            str: Markdown document describing the album. The caller can decide
                 whether to persist the markdown to disk or use it elsewhere.
        """
        if not album:
            return ""

        album_data = album.get("album", album)
        if not album_data:
            return ""

        album_name = album_data.get("name", "Unknown Album")
        album_type = album_data.get("album_type", "")
        album_group = album_data.get("album_group", "")
        release_date = album_data.get("release_date", "")
        release_precision = album_data.get("release_date_precision", "")
        total_tracks = album_data.get("total_tracks", "")
        label = album_data.get("label", "")
        popularity = album_data.get("popularity", "")
        external_urls = album_data.get("external_urls", {})
        spotify_url = external_urls.get("spotify", "")
        uri = album_data.get("uri", "")
        album_id = album_data.get("id", "")
        external_ids = album_data.get("external_ids", {})
        upc = external_ids.get("upc", "")
        genres = ", ".join(album_data.get("genres", []))
        added_at = album.get("added_at", "")
        images = album_data.get("images", [])
        cover_url = images[0]["url"] if images else ""
        artists = ", ".join(artist.get("name", "") for artist in album_data.get("artists", []))

        lines = [f"# {album_name}", ""]

        if cover_url:
            lines.append(f"![{album_name} – cover art]({cover_url})")
            lines.append("")

        metadata = [
            f"- Artist: {artists or 'Unknown Artist'}",
            f"- Album type: {album_type or 'Unknown'}",
            f"- Album group: {album_group or 'N/A'}",
            f"- Release date: {release_date or 'Unknown'} ({release_precision or 'precision unknown'})",
            f"- Total tracks: {total_tracks or 'Unknown'}",
            f"- Label: {label or 'Unknown'}",
            f"- Popularity: {popularity if popularity != '' else 'Unknown'}",
            f"- Spotify URL: {spotify_url or 'N/A'}",
            f"- URI: {uri or 'N/A'}",
            f"- Album ID: {album_id or 'N/A'}",
            f"- UPC: {upc or 'N/A'}",
            f"- Genres: {genres or 'N/A'}",
        ]

        if added_at:
            metadata.append(f"- Added to library: {added_at}")

        lines.extend(metadata)
        lines.append("")

        tracks = album_data.get("tracks", {}).get("items", [])
        if tracks:
            lines.append("## Tracklist")
            lines.append("")
            lines.append("| # | Track | Duration | Explicit | Spotify |")
            lines.append("| --- | --- | --- | --- | --- |")
            for track in tracks:
                track_number = track.get("track_number", "")
                track_name = track.get("name", "Unknown Track")
                duration = self._format_duration(track.get("duration_ms"))
                explicit = "Yes" if track.get("explicit") else "No"
                track_url = track.get("external_urls", {}).get("spotify", "")
                track_link = f"[Link]({track_url})" if track_url else ""
                lines.append(f"| {track_number} | {track_name} | {duration} | {explicit} | {track_link} |")
            lines.append("")

        return "\n".join(lines).strip()

    @staticmethod
    def _format_duration(duration_ms):
        if not duration_ms:
            return "N/A"
        seconds_total = int(round(duration_ms / 1000))
        minutes, seconds = divmod(seconds_total, 60)
        return f"{minutes}:{seconds:02d}"

    def save_tracks(self, tracks: list):
        pass

    def save_album_tracks(self, tracks: list):
        pass

    def save_artists(self, artists: list):
        pass

    def save_individual_playlists(self, playlists: list, playlist_tracks: dict):
        pass


def main():
    setup_app_logging(logger, logging.DEBUG)
    spotify_to_file: SpotifyToMarkdown = SpotifyToMarkdown()
    os.chdir(spotify_to_file.playlist_location)
    spotify_to_file.save_all_data({})

if __name__ == "__main__":
    main()