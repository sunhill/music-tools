import datetime
import logging
import os
from typing import List, Dict

from spotify.spotify_save import SpotifySave
from spotify.spotify_utils import (
    get_config_location,
    setup_app_logging,
    most_recent_directory,
    unzip_data_from_zip,
    get_data_location,
)

logger = logging.getLogger(__name__)



class SpotifyToMarkdown(SpotifySave):
    """Simple Markdown exporter for Spotify data.

    This implements the abstract methods from `SpotifySave` with small,
    human-readable markdown files. It's intentionally lightweight — the
    goal is to provide a working implementation so the class can be
    instantiated and used in scripts/tests.
    """

    def __init__(self, user_id: str = "") -> None:
        super().__init__()
        config_location = get_config_location()
        # Default to project directory if config missing — keep behaviour
        # minimal and robust for tests.
        save_dir = os.path.join(os.path.dirname(config_location), "markdown_exports")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        self.save_dir = save_dir

    def _write(self, filename: str, content: str):
        path = os.path.join(self.save_dir, filename)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        logger.debug(f"Wrote markdown file: {path}")

    def save_unique_tracks_in_playlists(self, unique_tracks_in_playlists: Dict):
        pass

    def save_unique_artists_in_playlists(self, unique_artists_in_playlists: Dict):
        pass

    def save_playlist_tracks(self, playlists: List[Dict], playlist_tracks: Dict):
        pass

    def save_playlist_details(self, playlists: List[Dict], playlist_tracks: Dict):
        pass

    def save_albums(self, albums: List[Dict]):
        md = ["# Albums\n"]
        for a in albums:
            artists = ", ".join(x["name"] for x in a.get("artists", []))
            md.append(f"- **{a.get('name','')}** — {artists} ({a.get('release_date','')})")
        self._write(f"albums_{datetime.date.today()}.md", "\n".join(md))

    def save_tracks(self, tracks: List[Dict]):
        pass

    def save_album_tracks(self, tracks: List[Dict]):
        pass

    def save_artists(self, artists: List[Dict]):
        # Create one markdown file per artist with basic metadata
        for a in artists:
            name = a.get("name", "unnamed")
            artist_id = a.get("id", "")
            uri = a.get("uri", "")
            followers = a.get("followers", "")
            popularity = a.get("popularity", "")
            genres = ", ".join(a.get("genres", []))
            image_url = ""
            imgs = a.get("images", [])
            if imgs and len(imgs) > 0 and isinstance(imgs[0], dict):
                image_url = imgs[0].get("url", "")

            # Build YAML front matter with genres as a list
            genres_list = a.get("genres", []) or []
            md_lines = []
            md_lines.append("---")
            # Quote strings to be safe in YAML
            md_lines.append(f"name: \"{name}\"")
            md_lines.append(f"id: \"{artist_id}\"")
            md_lines.append(f"uri: \"{uri}\"")
            md_lines.append(f"followers: {followers}")
            md_lines.append(f"popularity: {popularity}")
            md_lines.append("genres:")
            for g in genres_list:
                md_lines.append(f"  - \"{g}\"")
            md_lines.append("---")

            # Name should be displayed first after the front matter
            md_lines.append("")
            md_lines.append(f"# {name}")

            # Image should be displayed outside front matter for Obsidian (after the name)
            if image_url:
                md_lines.append("")
                md_lines.append(f"![300]({image_url})")


            # sanitize filename: keep alnum, space and dash; replace others with '_'
            safe_name = "".join(ch if ch.isalnum() or ch in (" ", "-") else "_" for ch in name).strip()
            safe_name = safe_name[:120]
            filename = f"{safe_name}.md"
            self._write(filename, "\n".join(md_lines))

    def save_individual_playlists(self, playlists: List[Dict], playlist_tracks: Dict):
        pass


def main():
    # Configure logging and write artist markdown files from the most recent saved data
    setup_app_logging(logger, logging.DEBUG)
    spotify_to_md = SpotifyToMarkdown()

    # Determine where the raw zipped data is stored and pick the most recent complete folder
    raw_data_location = get_data_location()
    most_recent = most_recent_directory(raw_data_location)
    logger.debug(f"Most recent directory: {most_recent}")
    zip_folder = f"{raw_data_location}/{most_recent}"

    # Unzip and write artist markdown files
    saved_artists = unzip_data_from_zip(f"{zip_folder}/saved_artists.gz")
    spotify_to_md.save_artists(saved_artists)


if __name__ == "__main__":
    main()

